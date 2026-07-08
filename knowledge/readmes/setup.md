# Setup Notes for RAG Ingestion

## 1. Ingestion
- Load all files under `knowledge/` recursively.
- Split markdown by headers first, then by token limit.
- Keep stack traces as smaller line-window chunks.

## 2. Embeddings
- Use a single embedding model for all sources to avoid vector drift.
- Store embedding metadata: file path, heading, line range, and timestamp.

## 3. Indexing
- Upsert by deterministic document ID (for re-index safety).
- Add tags: framework, error_type, environment.

## 4. Retrieval
- Use hybrid retrieval (vector + keyword) for stack traces.
- Re-rank top-k passages before final context assembly.

## 5. Evaluation
- Maintain a test set of known debug questions.
- Track hit rate@k, exact-fix retrieval, and hallucination rate.
