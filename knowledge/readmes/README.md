# Technical Debug Assistant Knowledge Base

This folder contains retrieval-friendly knowledge for a RAG-based debugging assistant.

## Structure
- `docs/`: technology-specific notes and troubleshooting guides.
- `readmes/`: project overview and setup instructions.
- `issues/`: anonymized issue records with reproduction and fix notes.
- `stacktraces/`: raw traces used for retrieval and matching.

## Retrieval intent
Documents are written with clear headings and compact sections so chunking pipelines can map user queries to relevant context quickly.

## Suggested metadata fields
- source_type (doc, issue, stacktrace, readme)
- topic (flask, postgres, docker)
- severity (low, medium, high)
- component (api, database, infra)
