from dataclasses import dataclass
from pathlib import Path

@dataclass
class Metadata:
    source_type: str
    file_name: str
    topic: str | None = None
    heading: str | None = None
    section_index: int | None = None

@dataclass
class Document:
    text: str
    metadata: Metadata

class DocumentLoader:

    SOURCE_MAPPING = {
        "docs"       : "doc",
        "issues"     : "issue",
        "readmes"    : "readme",
        "stacktraces": "stacktrace",
        "uploads"    : "upload",
    }

    def __init__(self, knowledge_path: str):
        self.knowledge_path = Path(knowledge_path)

    def load_documents(self):
        documents = []

        for file_path in self.knowledge_path.rglob("*"):
            if file_path.suffix not in [".txt", ".md"]:
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            source_folder = file_path.parent.name
            metadata = Metadata(
                source_type = self.SOURCE_MAPPING[source_folder],
                file_name = file_path.name,
                topic = file_path.stem if source_folder == "docs" else None
            )

            documents.append(Document(text=text, metadata=metadata))
            
        return documents
    

