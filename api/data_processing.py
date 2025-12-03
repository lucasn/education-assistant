import pymupdf
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from uuid import uuid4
from io import BytesIO
from langchain_core.documents import Document
from unstructured.partition.auto import partition
from os import getenv
import psycopg
from pgvector.psycopg import register_vector


OLLAMA_BASE_URL = getenv("OLLAMA_BASE_URL")
EMBEDDING_MODEL = getenv("EMBEDDING_MODEL")
VECTOR_DB_URL = getenv("VECTOR_DB_URL")
DOCUMENTS_COLLECTION_NAME = getenv("DOCUMENTS_COLLECTION_NAME")
DOCUMENTS_VECTOR_DIMENSION = int(getenv("DOCUMENTS_VECTOR_DIMENSION"))
TEXT_SPLITTER_CHUNK_SIZE = int(getenv("TEXT_SPLITTER_CHUNK_SIZE"))
DIFFICULTIES_VECTOR_DIMENSION = int(getenv("DIFFICULTIES_VECTOR_DIMENSION"))
DIFFICULTIES_COLLECTION_NAME = getenv("DIFFICULTIES_COLLECTION_NAME")


def initialize_vector_database(conn):
    """Initialize pgvector extension and create all necessary tables and indexes"""
    with conn.cursor() as cur:
        # Create documents table
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {DOCUMENTS_COLLECTION_NAME} (
                id BIGSERIAL PRIMARY KEY,
                vector vector({DOCUMENTS_VECTOR_DIMENSION}),
                text TEXT,
                file_id VARCHAR(50),
                filename TEXT,
                keywords TEXT[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create documents indexes
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS {DOCUMENTS_COLLECTION_NAME}_vector_idx
            ON {DOCUMENTS_COLLECTION_NAME}
            USING ivfflat (vector vector_cosine_ops)
            WITH (lists = 100)
        """)

        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS {DOCUMENTS_COLLECTION_NAME}_file_id_idx
            ON {DOCUMENTS_COLLECTION_NAME} (file_id)
        """)

        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS {DOCUMENTS_COLLECTION_NAME}_text_idx
            ON {DOCUMENTS_COLLECTION_NAME}
            USING gin(to_tsvector('english', text))
        """)

        # Create difficulties table
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {DIFFICULTIES_COLLECTION_NAME} (
                id BIGSERIAL PRIMARY KEY,
                vector vector({DIFFICULTIES_VECTOR_DIMENSION}),
                text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create difficulties indexes
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS {DIFFICULTIES_COLLECTION_NAME}_vector_idx
            ON {DIFFICULTIES_COLLECTION_NAME}
            USING ivfflat (vector vector_cosine_ops)
            WITH (lists = 100)
        """)

        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS {DIFFICULTIES_COLLECTION_NAME}_text_idx
            ON {DIFFICULTIES_COLLECTION_NAME}
            USING gin(to_tsvector('english', text))
        """)


class FileIngestion:
    def __init__(self) -> None:
        self.embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=TEXT_SPLITTER_CHUNK_SIZE,
            chunk_overlap=200,
            add_start_index=True
        )

        # Connect to PostgreSQL with pgvector
        self.conn = psycopg.connect(VECTOR_DB_URL, autocommit=True)
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(self.conn)

        # Initialize database tables and indexes
        initialize_vector_database(self.conn)

    def ingest(self, file_bytes, filename):
        file_id = str(uuid4())

        text = self.extract_text(file_bytes)
        pieces, embeddings = self.embed_text(text)

        # Store all chunks with the same file_id and filename
        with self.conn.cursor() as cur:
            for piece, embedding in zip(pieces, embeddings):
                cur.execute(
                    f"""
                    INSERT INTO {DOCUMENTS_COLLECTION_NAME}
                    (vector, text, file_id, filename, keywords)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (embedding, piece, file_id, filename, [])
                )

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

    def get_chunks_by_file_id(self, file_id):
        """Retrieve all chunks for a given file_id"""
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, text, filename
                FROM {DOCUMENTS_COLLECTION_NAME}
                WHERE file_id = %s
                ORDER BY id
                """,
                (file_id,)
            )
            results = cur.fetchall()
            return [{
                "id": row[0],
                "text": row[1],
                "filename": row[2]
            } for row in results]

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


class VectorStore:
    def __init__(self) -> None:
        self.embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)
        self.conn = psycopg.connect(VECTOR_DB_URL, autocommit=True)
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(self.conn)

        # Initialize database tables and indexes
        initialize_vector_database(self.conn)

    # Document search methods
    def search(self, query, top_k=3):
        """Search for documents by query string (embeds the query automatically)

        Args:
            query: The search query string
            top_k: Number of results to return
            evaluation: If True, search only entries with 'evaluation' keyword.
                       If False, search only entries without any keywords (default: False)
        """
        evaluation = bool(int(getenv("EVALUATION", "0")))
        print(f"Evaluation flag: {evaluation}")
        embedding = self.embedding_model.embed_query(query)

        # Build WHERE clause based on evaluation flag
        if evaluation:
            where_clause = "WHERE 'evaluation' = ANY(keywords)"
        else:
            where_clause = "WHERE (keywords IS NULL OR keywords = '{}')"

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, text, file_id, keywords,
                       1 - (vector <=> %s::vector) as distance
                FROM {DOCUMENTS_COLLECTION_NAME}
                {where_clause}
                ORDER BY vector <=> %s::vector
                LIMIT %s
                """,
                (embedding, embedding, top_k)
            )

            results = cur.fetchall()

            return [{
                "id": row[0],
                "text": row[1],
                "file_id": row[2],
                "keywords": row[3] if row[3] else [],
                "distance": float(row[4])
            } for row in results]

    # Difficulty management methods
    def insert_difficulty(self, text, vector):
        """Insert a difficulty with its vector into the difficulties collection"""
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {DIFFICULTIES_COLLECTION_NAME}
                (vector, text)
                VALUES (%s, %s)
                RETURNING id
                """,
                (vector, text)
            )
            return cur.fetchone()[0]

    def query_difficulties(self, limit=100):
        """Query all difficulties from the database"""
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, text
                FROM {DIFFICULTIES_COLLECTION_NAME}
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,)
            )
            results = cur.fetchall()
            return [{"id": row[0], "text": row[1]} for row in results]

    def search_difficulties(self, vector, top_k=3):
        """Search for similar difficulties by vector"""
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, text,
                       1 - (vector <=> %s::vector) as distance
                FROM {DIFFICULTIES_COLLECTION_NAME}
                ORDER BY vector <=> %s::vector
                LIMIT %s
                """,
                (vector, vector, top_k)
            )

            results = cur.fetchall()

            return [{
                "id": row[0],
                "text": row[1],
                "distance": float(row[2])
            } for row in results]

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

