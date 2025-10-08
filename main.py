from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import InMemorySaver
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from prompts import CONVERSATION_TITLE_PROMPT
from datetime import datetime
from langchain_core.messages import AIMessageChunk
import json
from fastapi.responses import StreamingResponse
import asyncio

OLLAMA_BASE_URL = "http://localhost:11434"
API_PORT = 8080
API_HOST = "localhost"
POSTGRES_URL = "postgresql://root:root@localhost:5432/checkpoint"
MONGO_URL = "mongodb://root:root@localhost:27017"

class AppContext:
    def __init__(self):
        self.model = None
        self.title_generation_model = None
        self.database_client = None
        self.database_collection = None

    def agent(self, checkpointer):
        return create_react_agent(
            model=context.model,
            tools=[],
            prompt="You are a helpful assistant. Give a short answer.",
            checkpointer=checkpointer
        )

    def checkpointer(self):
        return PostgresSaver.from_conn_string(POSTGRES_URL)

class AskRequest(BaseModel):
    threadId: str
    question: str

context = AppContext()

@asynccontextmanager
async def lifespan(app: FastAPI):
    context.model = ChatOllama(model='llama3.2:3b', temperature=0, base_url=OLLAMA_BASE_URL)
    context.title_generation_model = ChatOllama(model='llama3.2:3b', base_url=OLLAMA_BASE_URL)
    with context.checkpointer() as checkpointer:
        checkpointer.setup()
    
    context.database_client = MongoClient(MONGO_URL)
    db = context.database_client["education"]
    context.database_collection = db["education_data"]
    yield
  

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def retrieve_index():
    return FileResponse("static/index.html")

@app.post("/ask")
def ask_assistant(askRequest: AskRequest):
    db_cursor = context.database_collection.find({"threadId": askRequest.threadId})
    mongo_documents = [doc for doc in db_cursor]
    print(mongo_documents)

    if len(mongo_documents) == 0:
        title_creation_response = context.title_generation_model.invoke([
            {"role": "system", "content": CONVERSATION_TITLE_PROMPT},
            {"role": "user", "content": f"{askRequest.question}"}
        ])

        title = title_creation_response.content
        print(title)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        context.database_collection.insert_one({"threadId": askRequest.threadId, "title": title, "timestamp": timestamp})

    with context.checkpointer() as checkpointer:
        agent = context.agent(checkpointer)
        response = agent.invoke(
            {"messages": [{"role": "user", "content": askRequest.question}]},
            config={"configurable": {"thread_id": askRequest.threadId}}
        )
        print(response)
        return response["messages"][-1].content

@app.post("/ask_async")
async def ask_assistant_async(askRequest: AskRequest):
    db_cursor = context.database_collection.find({"threadId": askRequest.threadId})
    mongo_documents = [doc for doc in db_cursor]
    print(mongo_documents)

    if len(mongo_documents) == 0:
        title_creation_response = context.title_generation_model.invoke([
            {"role": "system", "content": CONVERSATION_TITLE_PROMPT},
            {"role": "user", "content": f"{askRequest.question}"}
        ])

        title = title_creation_response.content
        print(title)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        context.database_collection.insert_one({"threadId": askRequest.threadId, "title": title, "timestamp": timestamp})

    async def generate():
        with context.checkpointer() as checkpointer:
            agent = context.agent(checkpointer)
            response_stream = agent.stream(
                {"messages": [{"role": "user", "content": askRequest.question}]},
                config={"configurable": {"thread_id": askRequest.threadId}},
                stream_mode="messages"
            )
            for chunk in response_stream:
                message = chunk[0]
                if isinstance(message, AIMessageChunk):
                    print(message.content)
                    yield f"data: {json.dumps({"content": message.content})}\n\n"
                    await asyncio.sleep(0)
                else:
                    print(f"Unknown object in stream: {message}")
    
    return StreamingResponse(generate(), media_type="text/event-stream")
            

# @app.post("/test")
# async def ask_assistant(askRequest: AskRequest):
#     async def generate():
#         agent = create_react_agent(
#             model=context.model,
#             tools=[],
#             prompt="You are a helpful assistant.",
#             checkpointer=InMemorySaver()
#         )

#         response_stream = agent.stream(
#             {"messages": [{"role": "user", "content": askRequest.question}]},
#             config={"configurable": {"thread_id": askRequest.threadId}},
#             stream_mode="messages"
#         )
        
#         for chunk in response_stream:
#             message = chunk[0]
#             if isinstance(message, AIMessageChunk):
#                 yield f"data: {json.dumps({"content": message.content})}\n\n"
#             else:
#                 print(f"Unknown object in stream: {message}")
    
#     return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/conversations")
def retrieve_conversations():
    db_cursor = context.database_collection.find()
    conversations = [{"threadId": doc["threadId"], "title": doc["title"], "timestamp": doc["timestamp"]} for doc in db_cursor]
    return conversations

@app.get("/conversation/{threadId}")
def retrieve_conversation(threadId: str):
    with context.checkpointer() as checkpointer:
        checkpoint_tuple = checkpointer.get_tuple({"configurable": {"thread_id": threadId}})
        if checkpoint_tuple is None:
            return []
        checkpoint = checkpoint_tuple.checkpoint
        channel_values = checkpoint.get("channel_values") or {}
        messages = channel_values.get("messages") or []
        return messages



if __name__ == "__main__":
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
