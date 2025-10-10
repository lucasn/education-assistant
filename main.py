from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from langchain_core.messages import AIMessage, HumanMessage

import uvicorn

from models import AppContext, Assistant, AskRequest
from data_processing import FileIngestion


API_PORT = 8080
API_HOST = "localhost"

context = AppContext()

@asynccontextmanager
async def lifespan(app: FastAPI):
    context.build()

    with Assistant.checkpointer() as checkpointer:
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
def retrieve_index():
    return FileResponse("static/index.html")

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

# @app.post("/ask")
# def ask_assistant(askRequest: AskRequest):
#     if not context.is_existent_conversation(askRequest.threadId):
#         context.create_title_for_conversation(askRequest.threadId, askRequest.question)
    
#     response = context.assistant.invoke(askRequest.question, askRequest.threadId)
#     return response


@app.post("/ask_async")
async def ask_assistant_async(askRequest: AskRequest):
    if not context.is_existent_conversation(askRequest.threadId):
        context.create_title_for_conversation(askRequest.threadId, askRequest.question)

    generator = context.assistant.ainvoke(askRequest.question, askRequest.threadId)

    return StreamingResponse(generator, media_type="text/event-stream")

@app.get("/conversations")
def retrieve_conversations():
    db_cursor = context.title_database_collection.find()
    conversations = [{"threadId": doc["threadId"], "title": doc["title"], "timestamp": doc["timestamp"]} for doc in db_cursor]
    return conversations

@app.get("/conversation/{threadId}")
def retrieve_conversation(threadId: str):
    with Assistant.checkpointer() as checkpointer:
        checkpoint_tuple = checkpointer.get_tuple({"configurable": {"thread_id": threadId}})
        if checkpoint_tuple is None:
            return []
        checkpoint = checkpoint_tuple.checkpoint
        channel_values = checkpoint.get("channel_values") or {}
        messages = channel_values.get("messages") or []
        cleaned_messages = []
        stored_context = None
        for message in messages:
            json_message = {"content": message.content}

            if not stored_context is None:
                json_message["context"] = stored_context
                stored_context = None

            if isinstance(message, AIMessage):
                json_message["type"] = "ai"
            else:
                json_message["type"] = "human"

            if metadata := message.additional_kwargs.get("metadata"):
                stored_context = metadata["context"]

                if user_query := metadata.get("query"):
                    json_message["content"] = user_query

            cleaned_messages.append(json_message)

        return cleaned_messages



if __name__ == "__main__":
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
