import pymupdf
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from minio import Minio
from uuid import uuid4
from io import BytesIO
from langchain_core.documents import Document
from pymilvus import MilvusClient, DataType
from unstructured.partition.auto import partition


OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "qwen3-embedding:0.6b"
MINIO_URL = "127.0.0.1:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
FILES_BUCKET_NAME = "files-bucket"
MILVUS_URL = "http://localhost:19530"
DOCUMENTS_COLLECTION_NAME = "documents_collection"
DOCUMENTS_VECTOR_DIMENSION = 1024
TEXT_SPLITTER_CHUNK_SIZE = 1000


class FileIngestion:
    def __init__(self) -> None:
        self.embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=TEXT_SPLITTER_CHUNK_SIZE, 
            chunk_overlap=200, 
            add_start_index=True
        )

        self.minio_client = Minio(MINIO_URL,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )

        files_bucket = self.minio_client.bucket_exists(FILES_BUCKET_NAME)
        if not files_bucket:
            self.minio_client.make_bucket(FILES_BUCKET_NAME)
            print("Created bucket", FILES_BUCKET_NAME)
        else:
            print("Bucket", FILES_BUCKET_NAME, "already exists")

        self.milvus_client = MilvusClient(MILVUS_URL)

        schema = MilvusClient.create_schema()
        schema.add_field(
            field_name="id",
            datatype=DataType.INT64,
            is_primary=True,
            auto_id=True
        )
        schema.add_field(
            field_name="vector",
            datatype=DataType.FLOAT_VECTOR,
            dim=DOCUMENTS_VECTOR_DIMENSION
        )
        schema.add_field(
            field_name="text",
            datatype=DataType.VARCHAR,
            max_length=2*TEXT_SPLITTER_CHUNK_SIZE
        )
        schema.add_field(
            field_name="file_id",
            datatype=DataType.VARCHAR,
            max_length=50
        )
        schema.add_field(
            field_name="keywords",
            datatype=DataType.ARRAY,
            element_type=DataType.VARCHAR,
            max_capacity=200,
            max_length=512,
            nullable=True
        )

        index_params = self.milvus_client.prepare_index_params()

        index_params.add_index(
            field_name="text",
            index_type="AUTOINDEX"
        )

        index_params.add_index(
            field_name="file_id",
            index_type="AUTOINDEX"
        )

        index_params.add_index(
            field_name="vector", 
            index_type="AUTOINDEX",
            metric_type="COSINE"
        )

        if not self.milvus_client.has_collection(DOCUMENTS_COLLECTION_NAME):
            self.milvus_client.create_collection(
                collection_name=DOCUMENTS_COLLECTION_NAME,
                schema=schema,
                index_params=index_params
            )

    def ingest(self, file_bytes, filename):
        file_id = str(uuid4())
        metadata = {'filename': filename}
        self.upload_to_bucket(file_bytes, file_id, metadata)

        text = self.extract_text(file_bytes)
        pieces, embeddings = self.embed_text(text)

        for piece, embedding in zip(pieces, embeddings):
            data = {
                "text": piece,
                "vector": embedding,
                "keywords": [],
                "file_id": file_id
            }
            self.milvus_client.insert(collection_name=DOCUMENTS_COLLECTION_NAME, data=data)

    def upload_to_bucket(self, file_bytes, file_id, metadata):
        self.minio_client.put_object(FILES_BUCKET_NAME, file_id, BytesIO(file_bytes), len(file_bytes), metadata=metadata)

    def extract_text(self, file_bytes):
        try:
            print("Ingesting with unstructured")
            elements = partition(file=BytesIO(file_bytes), content_type="application/pdf", languages=["por", "eng"])
            text = ""
            for element in elements:
                text += f"\n{str(element)}"
        except Exception as error:
            print(f"Error while ingesting with unstructured: {error}")
            print("Ingesting with PyMuPDF")
            document = pymupdf.Document(stream=file_bytes)
            text = ""
            for page in document:
                text += page.get_text()
        finally:
            return text

    def embed_text(self, text):
        splits = self.text_splitter.split_documents([Document(page_content=text)])
        text_splits = [split.page_content for split in splits]
        embeddings = self.embedding_model.embed_documents(text_splits)

        return text_splits, embeddings


class VectorialSearch:
    def __init__(self) -> None:
        self.embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)
        self.milvus_client = MilvusClient(MILVUS_URL)
    
    def search(self, query, top_k=3):
        embedding = self.embedding_model.embed_query(query)
        documents = self.milvus_client.search(
            collection_name=DOCUMENTS_COLLECTION_NAME,
            anns_field="vector",
            data=[embedding],
            limit=top_k,
            search_params={"metric_type": "COSINE"},
            output_fields=["text", "file_id", "keywords"]
        )

        return [ {
            "id": entry["id"],
            "distance": entry["distance"],
            "text": entry["entity"]["text"],
            "keywords": entry["entity"]["keywords"],
            "file_id": entry["entity"]["file_id"]

        } for entry in documents[0] ]

if __name__ == '__main__':

    ingestion = FileIngestion()
    with open("./data/chapter1.pdf", mode='rb') as f:
        print(ingestion.extract_text(f.read()))