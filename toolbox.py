from pymilvus import MilvusClient, DataType
from typing import Annotated
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage, ToolCall
from langchain_ollama import OllamaEmbeddings
from langchain_core.messages.tool import tool_call

MILVUS_URL = "http://localhost:19530"
DIFFICULTIES_VECTOR_DIMENSION = 1024
DIFFICULTIES_COLLECTION_NAME = "difficulties_collection"
OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "qwen3-embedding:0.6b"

class VectorDatabase:
    def __init__(self) -> None:
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
            dim=DIFFICULTIES_VECTOR_DIMENSION
        )
        schema.add_field(
            field_name="text",
            datatype=DataType.VARCHAR,
            max_length=65530 # Max possible
        )

        index_params = self.milvus_client.prepare_index_params()

        index_params.add_index(
            field_name="text",
            index_type="AUTOINDEX"
        )

        index_params.add_index(
            field_name="vector", 
            index_type="AUTOINDEX",
            metric_type="COSINE"
        )

        if not self.milvus_client.has_collection(DIFFICULTIES_COLLECTION_NAME):
            self.milvus_client.create_collection(
                collection_name=DIFFICULTIES_COLLECTION_NAME,
                schema=schema,
                index_params=index_params
            )


@tool
def register_difficulty(
        description: Annotated[str, "A brief description of the difficulty"]
    ):
    """Register a student's difficulty"""
    print("[X] Register difficulties called")
    database = VectorDatabase()
    embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)

    embedding = embedding_model.embed_query(description)

    data = {
        "text": description,
        "vector": embedding
    }

    response = database.milvus_client.insert(collection_name=DIFFICULTIES_COLLECTION_NAME, data=data)

    id = response["ids"][0]

    return ToolMessage(content=f"Difficulty saved in the database. Id: {id}", tool_call_id="123")

@tool
def retrieve_difficulties():
    """Retrieve the difficulties of the student"""
    print("[X] Retrieve difficulties called")
    database = VectorDatabase()
    difficulties = database.milvus_client.query(
        collection_name=DIFFICULTIES_COLLECTION_NAME,
        filter="",
        output_fields=["id", "text"],
        limit=100
    )

    return difficulties

if __name__ == '__main__':
    retrieve_difficulties.invoke({})