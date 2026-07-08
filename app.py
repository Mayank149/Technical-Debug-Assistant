import re
import time
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.chunker import Chunk, Chunker
from src.embedder import Embedder
from src.generator import Generator
from src.context_builder import ContextBuilder
from src.loader import Document, Metadata
from src.prompt_builder import PromptBuilder
from src.vector_store import VectorStore

# ── Constants ─────────────────────────────────────────────────────────────────
UPLOAD_DIR = Path("knowledge/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".txt", ".md"}
MAX_FILE_SIZE      = 5 * 1024 * 1024   # 5 MB

# ── Pipeline state ────────────────────────────────────────────────────────────
pipeline_ready: bool           = False
pipeline_error: Optional[str]  = None
embedder:        Optional[Embedder]       = None
vector_store:    Optional[VectorStore]    = None
context_builder: Optional[ContextBuilder] = None
prompt_builder:  Optional[PromptBuilder]  = None
generator_:      Optional[Generator]      = None
chat_history:    List[dict]               = []
chunker = Chunker()


def _init_pipeline():
    global pipeline_ready, pipeline_error
    global embedder, vector_store, context_builder, prompt_builder, generator_
    try:
        embedder        = Embedder()
        vector_store    = VectorStore()
        vector_store.load_index()
        context_builder = ContextBuilder()
        prompt_builder  = PromptBuilder()
        generator_      = Generator()
        pipeline_ready  = True
    except Exception as exc:
        pipeline_error  = str(exc)


# ── App lifespan ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=_init_pipeline, daemon=True).start()
    yield


app = FastAPI(
    title="Technical Debug Assistant",
    description="RAG-powered debugging assistant backed by FAISS + LLaMA-3.3-70b",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (CSS / JS)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class QuestionRequest(BaseModel):
    question: str


class SourceEntry(BaseModel):
    file: str
    score: float
    headings: List[str]


class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceEntry]
    elapsed: float
    timestamp: str


class StatusResponse(BaseModel):
    ready: bool
    error: Optional[str] = None


class HistoryClearResponse(BaseModel):
    ok: bool
    cleared: int


class UploadedFile(BaseModel):
    name: str
    size_kb: float
    chunks: int


class UploadResponse(BaseModel):
    ok: bool
    filename: str
    chunks_added: int
    message: str


# ── Helper: chunk a plain Document into Chunk objects ─────────────────────────
def _chunk_document(doc: Document) -> List[Chunk]:
    """Chunk a Document using the shared Chunker; fall back to a single chunk
    for plain text files that contain no markdown headings."""
    chunks = chunker.chunk_documents([doc])

    if not chunks:
        # Plain text without ## headings — treat the whole file as one chunk
        chunks = [
            Chunk(
                chunk_id=f"{doc.metadata.file_name}_1",
                text=doc.text,
                metadata=Metadata(
                    source_type=doc.metadata.source_type,
                    file_name=doc.metadata.file_name,
                    topic=doc.metadata.topic,
                    heading="Full document",
                    section_index=0,
                ),
            )
        ]

    return chunks


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=FileResponse, include_in_schema=False)
async def serve_ui():
    return FileResponse("templates/index.html")


@app.get("/api/status", response_model=StatusResponse, tags=["Health"])
async def get_status():
    """Check whether the RAG pipeline has finished loading."""
    return StatusResponse(ready=pipeline_ready, error=pipeline_error)


@app.post("/api/ask", response_model=AnswerResponse, tags=["Debug"])
async def ask_question(body: QuestionRequest):
    """Submit a debugging question and receive a context-grounded answer."""
    if not pipeline_ready:
        raise HTTPException(status_code=503, detail="Pipeline is still loading…")

    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question must not be empty.")

    t0              = time.time()
    query_embedding = embedder.embed_text(question)
    results         = vector_store.search(query_embedding, top_k=5)
    context         = context_builder.build(results)
    prompt          = prompt_builder.build(context, question)
    answer          = generator_.generate(prompt)
    elapsed         = round(time.time() - t0, 2)

    sources: List[SourceEntry] = []
    for doc in context:
        seen: set      = set()
        headings: List[str] = []
        for item in doc["chunks"]:
            h = item["chunk"].metadata.heading
            if h and h not in seen:
                headings.append(h)
                seen.add(h)
        sources.append(
            SourceEntry(
                file=doc["source"],
                score=round(doc["best_score"], 3),
                headings=headings,
            )
        )

    entry = AnswerResponse(
        question=question,
        answer=answer,
        sources=sources,
        elapsed=elapsed,
        timestamp=time.strftime("%H:%M:%S"),
    )
    chat_history.append(entry.model_dump())
    return entry


@app.get("/api/history", response_model=List[AnswerResponse], tags=["Debug"])
async def get_history():
    """Retrieve all Q&A entries from this session."""
    return chat_history


@app.post("/api/clear", response_model=HistoryClearResponse, tags=["Debug"])
async def clear_history():
    """Wipe the current session history."""
    count = len(chat_history)
    chat_history.clear()
    return HistoryClearResponse(ok=True, cleared=count)


# ── Upload endpoints ──────────────────────────────────────────────────────────

@app.post("/api/upload", response_model=UploadResponse, tags=["Upload"])
async def upload_file(file: UploadFile = File(...)):
    """Upload a .txt or .md file, embed it, and add it to the FAISS index."""
    if not pipeline_ready:
        raise HTTPException(status_code=503, detail="Pipeline is still loading…")

    # Validate extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{suffix}'. Only .txt and .md are allowed.",
        )

    # Read & size-check
    content_bytes = await file.read()
    if len(content_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds the 5 MB limit.")

    # Sanitise filename
    safe_name = re.sub(r"[^\w.\-]", "_", file.filename)
    dest_path = UPLOAD_DIR / safe_name

    # Save to disk
    dest_path.write_bytes(content_bytes)

    # Decode text
    try:
        text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="File must be UTF-8 encoded text.")

    # Build Document → Chunks → Embeddings
    doc = Document(
        text=text,
        metadata=Metadata(
            source_type="upload",
            file_name=safe_name,
            topic=Path(safe_name).stem,
        ),
    )
    chunks       = _chunk_document(doc)
    embeddings   = embedder.embed_chunks(chunks)
    vector_store.add_embeddings(embeddings, chunks)

    return UploadResponse(
        ok=True,
        filename=safe_name,
        chunks_added=len(chunks),
        message=f"'{safe_name}' embedded into {len(chunks)} chunk(s) and added to the index.",
    )


@app.get("/api/uploads", response_model=List[UploadedFile], tags=["Upload"])
async def list_uploads():
    """List all files that have been uploaded and indexed."""
    files: List[UploadedFile] = []
    for p in sorted(UPLOAD_DIR.iterdir()):
        if p.suffix.lower() in ALLOWED_EXTENSIONS:
            # Count how many chunks belong to this file
            chunk_count = sum(
                1 for c in vector_store.chunks
                if c.metadata.file_name == p.name
            ) if vector_store and vector_store.chunks else 0
            files.append(
                UploadedFile(
                    name=p.name,
                    size_kb=round(p.stat().st_size / 1024, 1),
                    chunks=chunk_count,
                )
            )
    return files


@app.delete("/api/uploads/{filename}", tags=["Upload"])
async def delete_upload(filename: str):
    """Remove an uploaded file.
    Note: chunks remain in the live FAISS index until the server restarts and
    the index is rebuilt. This is by design for simplicity."""
    safe_name = re.sub(r"[^\w.\-]", "_", filename)
    dest_path = UPLOAD_DIR / safe_name
    if not dest_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    dest_path.unlink()
    return JSONResponse({"ok": True, "deleted": safe_name})
