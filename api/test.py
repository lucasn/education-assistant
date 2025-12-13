import os

os.environ["EMBEDDING_MODEL"]="qwen3-embedding:0.6b"
os.environ["OLLAMA_BASE_URL"]="http://localhost:11434"
os.environ["VECTOR_DB_URL"]="postgresql://root:root@localhost:5433/vector_db"
os.environ["DOCUMENTS_COLLECTION_NAME"]="documents_collection"
os.environ["DOCUMENTS_VECTOR_DIMENSION"]="1024"
os.environ["TEXT_SPLITTER_CHUNK_SIZE"]="1000"
os.environ["DIFFICULTIES_VECTOR_DIMENSION"]="1024"
os.environ["DIFFICULTIES_COLLECTION_NAME"]="difficulties_collection"
os.environ["EVALUATION"]="0"  # Disable evaluation mode filtering

from data_processing import VectorStore

if __name__ == "__main__":
    store = VectorStore()
    results = store.search("application layer")
    print(len(results))
    print(results)
    