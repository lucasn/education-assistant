from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from langgraph.checkpoint.postgres import PostgresSaver
import os
from contextlib import asynccontextmanager

OLLAMA_BASE_URL = "http://localhost:11434"
API_PORT = 8080
API_HOST = "localhost"
POSTGRES_URL = "postgresql://root:root@localhost:5432/checkpoint"

class AppContext:
    def __init__(self):
        self.agent = None
        self.model = None
        self.memory = None

    def retrieve_agent(self, checkpointer):
        return create_react_agent(
            model=context.model,
            tools=[],
            prompt="You are a helpful assistant. Give short answers.",
            checkpointer=checkpointer
        )

context = AppContext()

@asynccontextmanager
async def lifespan(app: FastAPI):
    context.model = ChatOllama(model='llama3.2:3b', temperature=0, base_url=OLLAMA_BASE_URL)
    with PostgresSaver.from_conn_string(POSTGRES_URL) as checkpointer:
        checkpointer.setup()
    yield
  

app = FastAPI(lifespan=lifespan)


class AskRequest(BaseModel):
    threadId: str
    question: str


@app.post("/ask")
def ask(askRequest: AskRequest):
    with PostgresSaver.from_conn_string(POSTGRES_URL) as checkpointer:
        agent = context.retrieve_agent(checkpointer)
        response = agent.invoke(
            {"messages": [{"role": "user", "content": askRequest.question}]},
            config={"configurable": {"thread_id": askRequest.threadId}}
        )
        print(response)
        return response["messages"][-1].content


if __name__ == "__main__":
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)

