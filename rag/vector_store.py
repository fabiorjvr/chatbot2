import chromadb
from sentence_transformers import SentenceTransformer
import uuid

class VectorStoreManager:
    def __init__(self, collection_name="renato_smartphones"):
        self.client = chromadb.PersistentClient(path="./data/chroma_db")
        self.text_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, documents, metadatas):
        embeddings = self.text_model.encode(documents, normalize_embeddings=True)
        ids = [str(uuid.uuid4()) for _ in documents]
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        return ids

    def search(self, query, n_results=1):
        query_embedding = self.text_model.encode([query], normalize_embeddings=True)
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        return results

    def get_collection_stats(self):
        return {"total_documents": self.collection.count()}