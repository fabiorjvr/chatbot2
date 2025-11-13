import chromadb
import os

# Criar diretório
os.makedirs("./data/chroma_db", exist_ok=True)

# Configurar ChromaDB com persistência
client = chromadb.PersistentClient(path="./data/chroma_db")

# Criar collection
collection = client.get_or_create_collection(
    name="renato_smartphones",
    metadata={"hnsw:space": "cosine"}
)

print(f"✅ ChromaDB inicializado")
print(f"📦 Collection: {collection.name}")
print(f"📊 Total docs: {collection.count()}")