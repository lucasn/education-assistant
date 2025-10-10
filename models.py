from prompts import CONVERSATION_TITLE_PROMPT, MAIN_MODEL_PROMPT
from langchain_ollama import ChatOllama
from langgraph.checkpoint.postgres import PostgresSaver
from pymongo import MongoClient
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from langchain_core.messages import AIMessageChunk

import asyncio
import json
from datetime import datetime

OLLAMA_BASE_URL = "http://localhost:11434"
API_PORT = 8080
API_HOST = "localhost"
POSTGRES_URL = "postgresql://root:root@localhost:5432/checkpoint"
MONGO_URL = "mongodb://root:root@localhost:27017"

class AppContext:
    def __init__(self):
        pass

    def build(self):
        self.main_model = ChatOllama(model='llama3.2:3b', temperature=0, base_url=OLLAMA_BASE_URL)
        self.title_generation_model = ChatOllama(model='llama3.2:3b', base_url=OLLAMA_BASE_URL)

        self.title_database_client = MongoClient(MONGO_URL)
        self.title_database = self.title_database_client["education"]
        self.title_database_collection = self.title_database["education_data"]
        self.assistant = Assistant()

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


class Assistant:
    def __init__(self) -> None:
        self.model = ChatOllama(model='llama3.2:3b', temperature=0, base_url=OLLAMA_BASE_URL) 
        
    @staticmethod
    def checkpointer():
        return PostgresSaver.from_conn_string(POSTGRES_URL)
            
    def create_agent(self, checkpointer):
        return create_react_agent(
            model=self.model,
            tools=[],
            prompt=MAIN_MODEL_PROMPT,
            checkpointer=checkpointer
        )
        
    def create_messages(self, query):
        return {"messages": [{"role": "user", "content": query}]}

    
    def invoke(self, query, thread_id):
        with Assistant.checkpointer() as checkpointer:
            agent = self.create_agent(checkpointer)
            messages = self.create_messages(query)

            response = agent.invoke(
                messages,
                config={"configurable": {"thread_id": thread_id}}
            )
            return response["messages"][-1].content

    async def ainvoke(self, query, thread_id):
        with Assistant.checkpointer() as checkpointer:
            agent = self.create_agent(checkpointer)
            messages = self.create_messages(query)

            response_stream = agent.stream(
                messages,
                config={"configurable": {"thread_id": thread_id}},
                stream_mode="messages"
            )
            for chunk in response_stream:
                message = chunk[0]
                if isinstance(message, AIMessageChunk):
                    yield f"data: {json.dumps({"content": message.content})}\n\n"
                    await asyncio.sleep(0)
                else:
                    print(f"Unknown object in stream: {message}")

class AskRequest(BaseModel):
    threadId: str
    question: str

