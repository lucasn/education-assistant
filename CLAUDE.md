# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Education Assistant is a RAG-based AI education system with LangGraph-powered agents. It consists of:
- **API**: FastAPI backend with LangGraph agents (professor, question generator) using Ollama models
- **Frontend**: React + Vite application with Tailwind CSS
- **Evaluation**: Automated testing system with RabbitMQ and LLM-based evaluation (correctness, groundedness)
- **Databases**: PostgreSQL (checkpointing, pgvector for RAG), MongoDB (conversation titles, evaluations)

## Development Commands

### Running the Full Stack

```bash
# Start all services (API, frontend, databases, RabbitMQ)
docker-compose up

# Start in background
docker-compose up -d

# Stop all services
docker-compose down
```

**Service Ports:**
- Frontend: http://localhost:5173
- API: http://localhost:8080
- MongoDB Express: http://localhost:8081
- RabbitMQ Management: http://localhost:15672
- PostgreSQL (checkpoint): localhost:5432
- PostgreSQL (vector): localhost:5433
- MongoDB: localhost:27017
- RabbitMQ: localhost:5672

### API Development

```bash
cd api

# Install dependencies
pip install -r requirements.txt

# Run API server (with hot reload)
python main.py

# Run tests
python test.py
```

**Required Environment Variables** (see `api/.env.example`):
- `OLLAMA_BASE_URL`: Ollama server URL
- `POSTGRES_URL`: PostgreSQL connection for checkpointing
- `VECTOR_DB_URL`: PostgreSQL with pgvector for RAG
- `MONGO_URL`: MongoDB connection
- Model configuration: `PROFESSOR_MODEL`, `EMBEDDING_MODEL`, `TITLE_GENERATION_MODEL`, `QUESTION_GENERATOR_MODEL`

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

### Evaluation System

```bash
cd evaluation

# Install dependencies
pip install -r requirements.txt

# Run test runner (loads questions from data/*.json and sends to RabbitMQ)
python test_runner.py

# Run evaluator service (consumes from RabbitMQ, evaluates with LLM judge)
python evaluator.py
```

**Evaluation Flow:**
1. `test_runner.py` reads questions from `data/*.json` files
2. Sends each question to the API and streams responses
3. Publishes test results to RabbitMQ queue `tests_results`
4. `evaluator.py` consumes messages and evaluates using Judge (Groq LLM)
5. Saves evaluation results (correctness, groundedness) to MongoDB

## Architecture

### LangGraph Agent System

The core is built on LangGraph with PostgreSQL checkpointing for conversation persistence:

**ProfessorAgent** (`api/agents/professor.py`):
- Main conversational agent using LangGraph StateGraph
- State: `{messages: list, context: str}`
- Graph nodes: `inject_prompt` → `chatbot` → conditional(`tools`) → `chatbot`
- Uses PostgresSaver for thread-based checkpointing
- Tools available: `search_documents`, `generate_study_questions`
- Streaming responses via Server-Sent Events (SSE)

**QuestionGeneratorAgent** (`api/agents/question_generator.py`):
- Generates study questions based on topics
- Called as a tool by ProfessorAgent

### Vector Database (pgvector)

The system uses PostgreSQL with pgvector extension instead of Milvus:

**VectorStore** (`api/data_processing.py`):
- Two collections: `documents_collection` (course materials), `difficulties_collection` (student difficulties)
- Documents table schema: `id, vector, text, file_id, filename, keywords, created_at`
- Uses IVFFlat indexing with cosine similarity
- Embedding model: Configured via `EMBEDDING_MODEL` (default: qwen3-embedding:0.6b)
- Evaluation mode: Filter by `keywords` array (e.g., 'evaluation' keyword) controlled by `EVALUATION` env var

**FileIngestion** (`api/data_processing.py`):
- Processes PDFs using `unstructured` library (fallback to PyMuPDF)
- Chunks text with RecursiveCharacterTextSplitter (chunk_size from env)
- Embeds chunks and stores in pgvector
- All chunks from same file share a `file_id`

### Tools System

Tools are defined in `api/toolbox.py`:

- `search_documents(query)`: Vector similarity search in pgvector, returns top-k documents with piece_id and distance
- `generate_study_questions(topic)`: Invokes QuestionGeneratorAgent to create Q&A pairs
- `register_difficulty(description)`: Stores student difficulties with embeddings
- `retrieve_difficulties()`: Retrieves all stored difficulties

Tools are bound to the model via `model.bind_tools(tools)` and executed through custom `ToolNode` implementation.

### API Endpoints

**FastAPI** (`api/main.py`):
- `POST /ingest`: Upload PDFs for ingestion (validates PDF only)
- `POST /ask_async`: Ask question, returns SSE stream (auto-creates conversation title on first message)
- `GET /conversations`: List all conversations from MongoDB
- `GET /conversation/{threadId}`: Retrieve conversation state from LangGraph checkpoint

### Evaluation Criteria

**Judge** (`evaluation/judge.py`):
- Uses Groq's `openai/gpt-oss-120b` model
- Two evaluation chains:
  - **Correctness**: Evaluates if answer is correct for the question
  - **Groundedness**: Evaluates if answer is grounded in retrieved context
- Output: `{analysis: str, verdict: "good" | "satisfactory" | "unsatisfactory"}`
- Prompts defined in `evaluation/prompts.py`

### Data Structure

**Test Questions** (`data/*.json`):
```json
{
  "questions": [
    {"question": "...", "answer": "..."}
  ]
}
```

**Conversation Titles** (MongoDB `education.education_data`):
```json
{"threadId": "...", "title": "...", "timestamp": "..."}
```

**Evaluation Results** (MongoDB `education.evaluation`):
```json
{
  "test_run_id": "...",
  "question": "...",
  "reference_answer": "...",
  "answer": "...",
  "search_documents_content": "...",
  "correctness": {"analysis": "...", "verdict": "..."},
  "groundedness": {"analysis": "...", "verdict": "..."},
  "timestamp": "..."
}
```

## Key Implementation Details

### Streaming Responses

The API uses LangGraph's `stream_mode="messages"` with `AIMessageChunk` to stream responses:

```python
async def ainvoke_graph(self, query, thread_id):
    response_stream = agent.stream(
        {"messages": messages},
        config=config,
        stream_mode="messages"
    )
    for chunk in response_stream:
        message = chunk[0]
        if isinstance(message, AIMessageChunk):
            yield f"data: {json.dumps(...)}\n\n"
```

### Conversation Persistence

- LangGraph checkpointer stores full conversation state in PostgreSQL
- MongoDB stores only conversation metadata (threadId, title, timestamp)
- Title auto-generated on first message using `TITLE_GENERATION_MODEL`

### Database Initialization

On startup, the system:
1. Builds AppContext with models and database connections
2. Initializes PostgresSaver checkpoint tables
3. Creates pgvector extension and tables with indexes (if not exists)

### Evaluation Pipeline

The evaluation system is decoupled via RabbitMQ:
- Test runner can be run independently to generate test data
- Evaluator runs as a service consuming from queue
- Allows parallel evaluation of multiple test runs
- Results persist in MongoDB for analysis

## Important Notes

- The system requires Ollama running locally or remotely with configured models
- Vector database changed from Milvus to pgvector (as of commit 4c8ebc5)
- Evaluation mode uses `keywords` array filtering in vector search
- All LLM calls use Ollama except Judge which uses Groq
- Frontend expects SSE responses with specific JSON format
- Document ingestion accepts only PDF files
