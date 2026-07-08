from sentence_transformers import SentenceTransformer

class Embedder:
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def embed_text(self, text):
        return self.model.encode(text, convert_to_numpy = True)
    
    def embed_chunks(self, chunks):

        texts = [chunk.text for chunk in chunks]

        embeddings = self.model.encode(
            texts,
            convert_to_numpy = True
        )

        return embeddings
    
    