from prompts import CONVERSATION_TITLE_PROMPT
from langchain_ollama import ChatOllama
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
from os import getenv
from agents.professor import ProfessorAgent

OLLAMA_BASE_URL = getenv("OLLAMA_BASE_URL")
POSTGRES_URL = getenv("POSTGRES_URL")
MONGO_URL = getenv("MONGO_URL")
TITLE_GENERATION_MODEL = getenv("TITLE_GENERATION_MODEL")

class AppContext:
    def __init__(self):
        pass

    def build(self):
        self.title_generation_model = ChatOllama(model=TITLE_GENERATION_MODEL, base_url=OLLAMA_BASE_URL, reasoning=False)

        self.title_database_client = MongoClient(MONGO_URL)
        self.title_database = self.title_database_client["education"]
        self.title_database_collection = self.title_database["education_data"]
        self.professor = ProfessorAgent()

    def is_existent_conversation(self, thread_id):
        db_cursor = self.title_database_collection.find({"threadId": thread_id})
        mongo_documents = [doc for doc in db_cursor]

        return len(mongo_documents) != 0        

    def create_title_for_conversation(self, thread_id, question):
        title_creation_response = self.title_generation_model.invoke([
            {"role": "system", "content": CONVERSATION_TITLE_PROMPT},
            {"role": "user", "content": question}
        ])

        title = title_creation_response.content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.title_database_collection.insert_one({"threadId": thread_id, "title": title, "timestamp": timestamp})
        print(f"Creating title for conversation: {title}")

class AskRequest(BaseModel):
    threadId: str
    question: str

