from typing import Annotated
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langchain_ollama import OllamaEmbeddings
from agents.question_generator import QuestionGeneratorAgent
from os import getenv
from data_processing import VectorStore
from uuid import uuid4
import json

OLLAMA_BASE_URL = getenv("OLLAMA_BASE_URL")
EMBEDDING_MODEL = getenv("EMBEDDING_MODEL")
DIFFICULTIES_COLLECTION_NAME = getenv("DIFFICULTIES_COLLECTION_NAME")


@tool
def register_difficulty(
        description: Annotated[str, "A brief description of the difficulty"]
    ):
    """Register a student's difficulty"""
    print("[X] Register difficulties called")
    vector_store = VectorStore()
    embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)

    embedding = embedding_model.embed_query(description)

    difficulty_id = vector_store.insert_difficulty(description, embedding)

    return ToolMessage(content=f"Difficulty saved in the database. Id: {difficulty_id}", tool_call_id="123")

@tool
def retrieve_difficulties():
    """Retrieve the difficulties of the student"""
    print("[X] Retrieve difficulties called")
    vector_store = VectorStore()
    difficulties = vector_store.query_difficulties(limit=100)

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

@tool
def search_documents(query: Annotated[str, "The topic, concept, or subject that should be searched in the documents"]):
    """Search for relevant documents in the database"""
    print(f"[Tool Call] search_documents(topic={query})")
    vector_store = VectorStore()
    documents = vector_store.search(query, top_k=6)

    tool_response = []
    for document in documents:
        piece_id = str(uuid4()).split("-")[0]
        document_json = {
            "piece_id": piece_id,
            "distance": document["distance"],
            "content": document["text"]
        }
        tool_response.append(document_json)
    return json.dumps(tool_response)