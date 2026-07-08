from dataclasses import dataclass
from src.loader import Metadata
import re

@dataclass
class Chunk:
    chunk_id : str
    text: str
    metadata: Metadata

class Chunker:
    def __init__(self, max_lines = 20, overlap = 5):
        self.max_lines = max_lines
        self.overlap = overlap

    def chunk_documents(self, documents):
        chunks = []

        for document in documents:
            if document.metadata.source_type == "stacktrace":
                chunks.extend(self._chunk_stacktrace(document))
            else:
                chunks.extend(self._chunk_markdown(document))

        return chunks
    
    def _chunk_markdown(self, document):
        chunks = []

        sections = re.split(
            r"(?=^## )",
            document.text,
            flags=re.MULTILINE
        )

        for index, section in enumerate(sections):
            section = section.strip()

            if not section.startswith("##"):
                continue

            heading = section.split("\n")[0].replace("##", "").strip()

            metadata = Metadata(
                source_type = document.metadata.source_type,
                file_name = document.metadata.file_name,
                topic = document.metadata.topic,
                heading = heading,
                section_index = index
            )

            chunks.append(
                Chunk(
                    chunk_id=f"{document.metadata.file_name}_{len(chunks)+1}",
                    text = section,
                    metadata = metadata
                )
            )

        return chunks
    
    def _chunk_stacktrace(self, document):
        chunks = []
        lines = document.text.splitlines()

        step = self.max_lines - self.overlap

        for start in range(0, len(lines), step):
            chunk_lines = lines[start : start + self.max_lines]
            chunk_text = "\n".join(chunk_lines)

            metadata = Metadata(
                source_type = document.metadata.source_type,
                file_name = document.metadata.file_name,
                topic = document.metadata.topic,
                heading = f"Lines {start + 1}-{min(start + self.max_lines, len(lines))}"
            )

            chunks.append(
                Chunk(
                    chunk_id=f"{document.metadata.file_name}_{len(chunks)+1}",
                    text = chunk_text,
                    metadata = metadata
                )
            )

        return chunks