from typing import Annotated
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langchain_ollama import OllamaEmbeddings
from agents.question_generator import QuestionGeneratorAgent
from os import getenv
from data_processing import VectorDatabase

MILVUS_URL = getenv("MILVUS_URL")
OLLAMA_BASE_URL = getenv("OLLAMA_BASE_URL")
EMBEDDING_MODEL = getenv("EMBEDDING_MODEL")
DIFFICULTIES_COLLECTION_NAME = getenv("DIFFICULTIES_COLLECTION_NAME")


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

@tool
def generate_study_questions(
    topic: Annotated[str, "The topic, concept, or subject area the questions should focus on."]
    ):
    """Generates study or quiz questions related to a specific topic or document context. This tool helps the professor agent create questions that assess a student’s understanding of the material."""
    print(f"[Tool Call] generate_study_questions(topic={topic})")
    agent = QuestionGeneratorAgent()
    response = agent.invoke(topic)

    tool_response = f"# Study questions about: {topic}\n"
    for i, question in enumerate(response["questions"]):
        tool_response += f"Question {i+1}: {question.question}\n\n"
        tool_response += f"Answer {i+1}: {question.answer}\n\n"

    return tool_response