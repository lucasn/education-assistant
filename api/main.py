from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import uvicorn
from models import AppContext, AskRequest
from data_processing import FileIngestion
from dotenv import load_dotenv
from os import getenv
from agents.professor import ProfessorAgent

load_dotenv()

API_PORT = int(getenv("API_PORT"))
API_HOST = getenv("API_HOST")

context = AppContext()

@asynccontextmanager
async def lifespan(app: FastAPI):
    context.build()

    with ProfessorAgent.checkpointer() as checkpointer:
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

@app.post("/ingest")
async def ingest(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    for file in files:
        content_type = (file.content_type or "").lower()
        if content_type not in {"application/pdf", "application/x-pdf", "application/octet-stream"} and not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Unsupported file type for {file.filename}. Only PDF is allowed.")

        file_bytes = await file.read()
        file_ingestion = FileIngestion()
        file_ingestion.ingest(file_bytes, file.filename)

    return 200


@app.post("/ask_async")
async def ask_professor_async(askRequest: AskRequest):
    if not context.is_existent_conversation(askRequest.threadId):
        context.create_title_for_conversation(askRequest.threadId, askRequest.question)

    generator = context.professor.ainvoke_graph(askRequest.question, askRequest.threadId)

    return StreamingResponse(generator, media_type="text/event-stream")

@app.get("/conversations")
def retrieve_conversations():
    db_cursor = context.title_database_collection.find()
    conversations = [{"threadId": doc["threadId"], "title": doc["title"], "timestamp": doc["timestamp"]} for doc in db_cursor]
    return conversations

@app.get("/conversation/{threadId}")
def retrieve_conversation(threadId: str):
    config = {"configurable": {"thread_id": threadId}}
    return context.professor.get_conversation(config)



if __name__ == "__main__":
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
