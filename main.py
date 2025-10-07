from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from langgraph.checkpoint.postgres import PostgresSaver
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

OLLAMA_BASE_URL = "http://localhost:11434"
API_PORT = 8080
API_HOST = "localhost"
POSTGRES_URL = "postgresql://root:root@localhost:5432/checkpoint"

class AppContext:
    def __init__(self):
        self.model = None
        self.memory = None

    def agent(self, checkpointer):
        return create_react_agent(
            model=context.model,
            tools=[],
            prompt="You are a helpful assistant. Give short answers.",
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
    with context.checkpointer() as checkpointer:
        checkpointer.setup()
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
def read_root():
    return FileResponse("static/index.html")

@app.post("/ask")
def ask(askRequest: AskRequest):
    with context.checkpointer() as checkpointer:
        agent = context.agent(checkpointer)
        response = agent.invoke(
            {"messages": [{"role": "user", "content": askRequest.question}]},
            config={"configurable": {"thread_id": askRequest.threadId}}
        )
        print(response)
        return response["messages"][-1].content


if __name__ == "__main__":
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)

