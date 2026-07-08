import faiss
import numpy as np
import pickle
from pathlib import Path

class VectorStore:

    def __init__(self, db_path = "vector_db"):
        self.index = None
        self.chunks = []
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)

    def build_index(self, embeddings, chunks):
        embeddings = embeddings.astype('float32') #FAISS requires float32 data type for the index

        faiss.normalize_L2(embeddings)
        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dimension) # IP = Inner Product which is just cosine similarity for normalized vectors
        self.index.add(embeddings)

        self.chunks = chunks

    def save_index(self):
        faiss.write_index(
            self.index, 
            str(self.db_path/"index.faiss")
        )

        with open(self.db_path/"chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)

    def load_index(self):
        if not (self.db_path / "index.faiss").exists():
            raise FileNotFoundError("Vector database not found. Run build_index() and save_index() first.")
        self.index = faiss.read_index(str(self.db_path/"index.faiss"))

        with open(self.db_path/"chunks.pkl", "rb") as f:
            self.chunks = pickle.load(f)

    def add_embeddings(self, new_embeddings, new_chunks):
        """Incrementally add new vectors to the live index and persist."""
        new_embeddings = new_embeddings.astype('float32')
        faiss.normalize_L2(new_embeddings)
        self.index.add(new_embeddings)
        self.chunks.extend(new_chunks)
        self.save_index()

    def search(self, query_embedding, top_k=5):
        query_embedding = query_embedding.astype('float32')
        query_embedding = query_embedding.reshape(1, -1)  # Reshape to 2D array for FAISS
        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(query_embedding, top_k)

        results = []

        for score, idx in zip(scores[0], indices[0]):
            results.append(
                {
                    "score" : float(score),
                    "chunk" : self.chunks[idx]
                }
            )
            
        return results