# Education Assistant

> A sophisticated AI-powered educational system using Retrieval Augmented Generation (RAG), LangGraph agents, and automated evaluation pipelines.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Detailed Setup Guide](#detailed-setup-guide)
- [Component Documentation](#component-documentation)
  - [API Backend](#api-backend)
  - [Frontend Application](#frontend-application)
  - [Evaluation System](#evaluation-system)
- [Understanding the Architecture](#understanding-the-architecture)
  - [RAG (Retrieval Augmented Generation)](#rag-retrieval-augmented-generation)
  - [LangGraph Agent System](#langgraph-agent-system)
  - [Vector Database with pgvector](#vector-database-with-pgvector)
  - [Conversation Persistence](#conversation-persistence)
  - [Evaluation Pipeline](#evaluation-pipeline)
- [Development Guides](#development-guides)
  - [Running Individual Components](#running-individual-components)
  - [Ingesting Documents](#ingesting-documents)
  - [Running Evaluations](#running-evaluations)
  - [Database Management](#database-management)
- [API Reference](#api-reference)
- [Database Schemas](#database-schemas)
- [Configuration Reference](#configuration-reference)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Education Assistant** is an advanced AI-powered educational platform that combines multiple cutting-edge technologies to provide intelligent, context-aware responses to student questions. The system uses Retrieval Augmented Generation (RAG) to ground its responses in actual course materials, preventing hallucinations and ensuring accuracy.

### What Makes This Special?

1. **RAG-Based Responses**: All answers are grounded in retrieved course materials, not just LLM knowledge
2. **Persistent Conversations**: Full conversation history with thread-based management
3. **Automated Evaluation**: Built-in testing system using LLM-as-judge for quality assurance
4. **Agent-Based Architecture**: Uses LangGraph for sophisticated multi-step reasoning
5. **Streaming Responses**: Real-time response streaming for better user experience
6. **Document Ingestion**: Upload PDFs which are automatically chunked, embedded, and indexed
7. **Study Question Generation**: AI-powered generation of study questions based on topics

---

## Key Features

### For Students
- **Intelligent Q&A**: Ask questions and get answers grounded in course materials
- **Context-Aware Responses**: The system retrieves relevant documents before answering
- **Conversation History**: All conversations are saved and can be resumed later
- **Study Questions**: Generate practice questions on any topic from your course materials

### For Educators
- **Document Upload**: Upload course materials (PDFs) for the AI to reference
- **Quality Assurance**: Automated evaluation system to assess response quality
- **Conversation Monitoring**: View and analyze student conversations
- **Evaluation Dashboard**: Visual analytics for system performance

### For Developers
- **Modular Architecture**: Clean separation between API, frontend, and evaluation
- **Docker-Based Deployment**: One command to run the entire stack
- **Extensible Agent System**: Easy to add new tools and capabilities
- **Comprehensive Testing**: Automated evaluation with detailed metrics

---

## System Architecture

The Education Assistant consists of three main components working together:

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│                 │         │                  │         │                 │
│    Frontend     │────────▶│   API Backend    │────────▶│   Databases     │
│  (React+Vite)   │  HTTP   │  (FastAPI +      │         │  - PostgreSQL   │
│                 │◀────────│   LangGraph)     │         │  - MongoDB      │
│                 │   SSE   │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │
                                     │
                            ┌────────▼─────────┐
                            │                  │
                            │  Evaluation      │
                            │  System          │
                            │  (RabbitMQ +     │
                            │   LLM Judge)     │
                            │                  │
                            └──────────────────┘
```

### Component Overview

1. **Frontend**: React application providing the chat interface
2. **API**: FastAPI backend with LangGraph agents for intelligent responses
3. **PostgreSQL (Checkpoint DB)**: Stores conversation state via LangGraph checkpointing
4. **PostgreSQL (Vector DB)**: Stores document embeddings for RAG using pgvector
5. **MongoDB**: Stores conversation metadata and evaluation results
6. **RabbitMQ**: Message queue for decoupled evaluation pipeline
7. **Ollama**: Local LLM inference for all model operations

---

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **LangGraph**: Framework for building stateful, multi-agent applications
- **LangChain**: LLM application framework with tool integration
- **Ollama**: Local LLM inference engine (supports various models)
- **PostgreSQL + pgvector**: Vector database for RAG
- **MongoDB**: NoSQL database for metadata and results
- **RabbitMQ**: Message broker for async evaluation

### Frontend
- **React 19**: Modern JavaScript library for building user interfaces
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **React Markdown**: Markdown rendering for chat messages

### Evaluation
- **Groq**: High-performance LLM API for evaluation (LLM-as-judge)
- **Jupyter**: Interactive notebooks for statistical analysis
- **Matplotlib**: Data visualization for evaluation metrics

### Infrastructure
- **Docker & Docker Compose**: Containerization and orchestration
- **Uvicorn**: ASGI server for FastAPI

---

## Quick Start

### Prerequisites

1. **Docker & Docker Compose** installed on your system
2. **Ollama** running with required models (see Configuration)

### Install Ollama Models

```bash
# Install required Ollama models
ollama pull qwen3:8b
ollama pull qwen3-embedding:0.6b

# Optional: Use different models (update .env files accordingly)
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### Start the Application

```bash
# Clone the repository
git clone <repository-url>
cd education-assistant

# Configure environment variables
cp api/.env.example api/.env
cp frontend/.env.example frontend/.env
cp evaluation/.env.example evaluation/.env

# Edit .env files to match your Ollama setup
# For Ollama running locally, default settings should work

# Start all services
docker-compose up

# Or run in background
docker-compose up -d
```

### Access the Application

- **Frontend**: http://localhost:5173
- **API**: http://localhost:8080
- **MongoDB Express**: http://localhost:8081 (Database UI)
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

### Upload Documents and Start Chatting

1. Open http://localhost:5173 in your browser
2. Click the upload icon to upload PDF documents
3. Wait for ingestion to complete
4. Start asking questions about your documents!

---

## Detailed Setup Guide

### Step 1: Install Dependencies

#### Install Ollama

**macOS**:
```bash
brew install ollama
ollama serve
```

**Linux**:
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

**Windows**: Download from https://ollama.com/download

#### Pull Required Models

```bash
# Embedding model (required for vector search)
ollama pull qwen3-embedding:0.6b

# Main conversational model
ollama pull qwen3:8b

# Or use alternative models:
# ollama pull llama3.1:8b
# ollama pull mistral:7b
# ollama pull nomic-embed-text
```

#### Install Docker

Follow the official Docker installation guide for your platform:
- https://docs.docker.com/get-docker/

### Step 2: Configure Environment Variables

#### API Configuration (`api/.env`)

```bash
# Database URLs
POSTGRES_URL="postgresql://root:root@checkpoint-db:5432/checkpoint"
VECTOR_DB_URL="postgresql://root:root@vector-db:5432/vector_db"
MONGO_URL="mongodb://root:root@mongodb:27017"

# Ollama Configuration
OLLAMA_BASE_URL="http://host.docker.internal:11434"  # For Docker
# OLLAMA_BASE_URL="http://localhost:11434"  # For local development

# Model Configuration
EMBEDDING_MODEL="qwen3-embedding:0.6b"
TITLE_GENERATION_MODEL="qwen3:8b"
QUESTION_GENERATOR_MODEL="qwen3:8b"
PROFESSOR_MODEL="qwen3:8b"

# Vector Database Configuration
DOCUMENTS_COLLECTION_NAME="documents_collection"
DOCUMENTS_VECTOR_DIMENSION=1024
DIFFICULTIES_COLLECTION_NAME="difficulties_collection"
TEXT_SPLITTER_CHUNK_SIZE=1000

# API Server Configuration
API_PORT=8080
API_HOST="0.0.0.0"

# Evaluation Mode (optional)
EVALUATION=0  # Set to 1 to enable evaluation mode filtering
```

#### Frontend Configuration (`frontend/.env`)

```bash
API_URL="http://localhost:8080"
```

#### Evaluation Configuration (`evaluation/.env`)

```bash
# API Configuration
API_URL="http://localhost:8080"

# RabbitMQ Configuration
RABBITMQ_HOST="localhost"
RABBITMQ_PORT=5672
RABBITMQ_USER="guest"
RABBITMQ_PASSWORD="guest"

# MongoDB Configuration
MONGO_URL="mongodb://root:root@localhost:27017"

# Groq API (for LLM Judge)
GROQ_API_KEY="your-groq-api-key-here"
# Get your API key from https://console.groq.com/
```

### Step 3: Start Services

```bash
# From the project root
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api
docker-compose logs -f frontend
```

### Step 4: Verify Installation

1. **Check Frontend**: Open http://localhost:5173
2. **Check API**: Open http://localhost:8080/docs (FastAPI Swagger UI)
3. **Check MongoDB**: Open http://localhost:8081 (Mongo Express)
4. **Check RabbitMQ**: Open http://localhost:15672 (guest/guest)

---

## Component Documentation

### API Backend

The API is built with FastAPI and uses LangGraph for agent orchestration. It provides endpoints for document ingestion, question answering, and conversation management.

#### File Structure

```
api/
├── agents/
│   ├── professor.py          # Main conversational agent
│   └── question_generator.py # Study question generator agent
├── data_processing.py         # Vector DB and document ingestion
├── main.py                    # FastAPI application
├── models.py                  # Pydantic models and AppContext
├── prompts.py                 # System prompts for LLMs
├── toolbox.py                 # Tool definitions for agents
├── test.py                    # Vector search test script
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
└── .env                       # Environment variables
```

#### Key Classes

**AppContext** (`models.py`):
- Central application context manager
- Initializes database connections
- Manages LLM models and agents
- Handles conversation title generation

**ProfessorAgent** (`agents/professor.py`):
- Main conversational agent using LangGraph
- Implements StateGraph with tool calling
- Uses PostgresSaver for conversation persistence
- Streams responses via Server-Sent Events (SSE)
- State: `{messages: list, context: str}`
- Graph flow: `inject_prompt` → `chatbot` → conditional(`tools`) → `chatbot`

**QuestionGeneratorAgent** (`agents/question_generator.py`):
- Generates study questions based on topics
- Uses vector search to find relevant context
- Structured output using Pydantic models
- Temperature: 0.8 for creative generation

**FileIngestion** (`data_processing.py`):
- PDF text extraction using `unstructured` library
- Fallback to PyMuPDF for problematic PDFs
- Text chunking with RecursiveCharacterTextSplitter
- Embedding generation via Ollama
- Storage in PostgreSQL with pgvector

**VectorStore** (`data_processing.py`):
- Cosine similarity search in pgvector
- Keyword-based filtering for evaluation mode
- Difficulty tracking for student struggles
- IVFFlat indexing for performance

#### API Endpoints

**POST /ingest**
- Upload PDF files for document ingestion
- Validates PDF file type
- Chunks text and generates embeddings
- Stores in vector database
- Returns: 200 on success

Example:
```bash
curl -X POST http://localhost:8080/ingest \
  -F "files=@course_material.pdf"
```

**POST /ask_async**
- Ask a question and stream the response
- Auto-creates conversation title on first message
- Returns Server-Sent Events (SSE) stream
- Request body: `{"threadId": "uuid", "question": "string"}`

Example:
```bash
curl -X POST http://localhost:8080/ask_async \
  -H "Content-Type: application/json" \
  -d '{"threadId": "123e4567-e89b-12d3-a456-426614174000", "question": "What is RAG?"}'
```

**GET /conversations**
- List all conversations with titles
- Returns: Array of `{threadId, title, timestamp}`

Example:
```bash
curl http://localhost:8080/conversations
```

**GET /conversation/{threadId}**
- Retrieve full conversation state
- Includes all messages and metadata
- Returns: LangGraph checkpoint state

Example:
```bash
curl http://localhost:8080/conversation/123e4567-e89b-12d3-a456-426614174000
```

#### Tools Available to Agents

Defined in `toolbox.py`:

1. **search_documents(query: str)**
   - Vector similarity search in document collection
   - Returns top-k most relevant documents
   - Includes piece_id and similarity distance
   - Automatically called by professor agent when needed

2. **generate_study_questions(topic: str)**
   - Invokes QuestionGeneratorAgent
   - Returns list of Q&A pairs
   - Uses vector search for relevant context
   - Temperature: 0.8 for variety

3. **register_difficulty(description: str)**
   - Stores student difficulties with embeddings
   - Helps track learning challenges
   - Stored in separate pgvector collection

4. **retrieve_difficulties()**
   - Retrieves all stored student difficulties
   - Useful for identifying common challenges

---

### Frontend Application

A modern React application built with Vite, providing an intuitive chat interface for interacting with the AI professor.

#### File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── FileUpload.jsx     # PDF upload component
│   │   ├── MessageBubble.jsx  # Chat message display
│   │   └── icons.jsx          # SVG icon components
│   ├── App.jsx                # Main application
│   ├── main.jsx               # React entry point
│   └── utils.jsx              # Utility functions
├── public/                    # Static assets
├── package.json               # npm dependencies
├── vite.config.js             # Vite configuration
├── tailwind.config.js         # Tailwind CSS config
└── Dockerfile                 # Container configuration
```

#### Key Features

**Conversation Management**:
- Sidebar with conversation history
- Auto-generated conversation titles
- Thread-based conversation persistence
- Filters out test conversations

**Message Streaming**:
- Real-time message streaming via SSE
- Displays messages as they're generated
- Shows typing indicators during generation

**File Upload**:
- Drag-and-drop PDF upload
- Multiple file selection
- Upload progress tracking
- Visual success/error feedback

**Rich Message Display**:
- Markdown rendering with GitHub Flavored Markdown
- Collapsible context sections
- Collapsible tool call information
- Syntax highlighting for code blocks

#### Component Details

**App.jsx**:
- Main application component (326 lines)
- Manages conversation state
- Handles SSE streaming
- Conversation sidebar with history
- Message input and display area

**FileUpload.jsx**:
- PDF upload interface
- Drag-and-drop support
- File validation (PDF only)
- Upload status indication

**MessageBubble.jsx**:
- Individual message display
- Markdown rendering
- Context display (collapsible)
- Tool call display (collapsible)
- Different styling for human/AI messages

#### Styling

- **Dark theme**: Gray-900 background for reduced eye strain
- **Tailwind CSS**: Utility-first styling
- **Responsive design**: Works on mobile and desktop
- **Smooth animations**: Transitions for better UX

---

### Evaluation System

An automated testing and evaluation pipeline using RabbitMQ for decoupling and Groq's LLM for quality assessment.

#### File Structure

```
evaluation/
├── frontend/
│   ├── api.py                 # FastAPI dashboard server
│   ├── index.html             # Evaluation dashboard UI
│   └── requirements.txt       # Python dependencies
├── evaluator.py               # RabbitMQ consumer & evaluator
├── test_runner.py             # Test execution & publisher
├── judge.py                   # LLM evaluation chains
├── prompts.py                 # Evaluation prompts
├── rabbitmq_client.py         # RabbitMQ wrapper
├── evaluation_statistics.ipynb # Statistical analysis notebook
├── README_STATISTICS.md       # Statistics documentation
├── requirements.txt           # Python dependencies
└── Dockerfile                 # Container configuration
```

#### How It Works

```
┌──────────────┐      ┌─────────────┐      ┌──────────────┐
│              │      │             │      │              │
│ Test Runner  │─────▶│  RabbitMQ   │─────▶│  Evaluator   │
│              │      │   Queue     │      │              │
└──────────────┘      └─────────────┘      └──────────────┘
       │                                           │
       │ 1. Sends questions                       │ 3. Evaluates
       │ 2. Streams responses                     │    with LLM Judge
       │                                           │
       ▼                                           ▼
┌──────────────┐                          ┌──────────────┐
│              │                          │              │
│  API Backend │                          │   MongoDB    │
│              │                          │  (Results)   │
└──────────────┘                          └──────────────┘
```

#### Components

**test_runner.py**:
- Loads test questions from `data/*.json`
- Sends each question to the API
- Streams responses via SSE
- Extracts tool calls from conversation state
- Publishes results to RabbitMQ queue `tests_results`
- Generates unique test_run_id for each batch

**evaluator.py**:
- Consumes messages from RabbitMQ queue
- Evaluates using Judge (Groq LLM)
- Two evaluation criteria:
  - **Correctness**: Is the answer correct?
  - **Groundedness**: Is the answer based on retrieved context?
- Stores results in MongoDB
- Runs as a service (graceful shutdown on SIGINT/SIGTERM)

**judge.py**:
- LLM-as-judge implementation
- Uses Groq's `openai/gpt-oss-120b` model
- Two evaluation chains:
  - `correctness_chain`: Evaluates answer correctness
  - `groundedness_chain`: Evaluates grounding in context
- Structured output: `{analysis: str, verdict: "good" | "satisfactory" | "unsatisfactory"}`
- Temperature: 0.0 for consistent evaluation

**prompts.py**:
- Detailed evaluation rubrics
- Verdict guidelines with examples
- Special handling for "I don't know" responses (evaluated as GOOD)

**Evaluation Dashboard**:
- Web UI for viewing evaluation results
- Lists all test runs
- Shows detailed results per test
- Color-coded verdicts (green/yellow/red)
- Collapsible test details

**evaluation_statistics.ipynb**:
- Jupyter notebook for statistical analysis
- Functions:
  - `list_test_run_ids()`: List available test runs
  - `generate_evaluation_statistics(test_run_id)`: Generate charts
  - `display_statistics_summary(stats)`: Text summary
  - `compare_test_runs(test_run_ids)`: Compare multiple runs
- Pie charts for correctness and groundedness
- Color scheme: Good (blue), Satisfactory (yellow), Unsatisfactory (red)

#### Running Evaluations

**Step 1: Prepare Test Data**

Create JSON files in `data/` directory:
```json
{
  "questions": [
    {
      "id": 1,
      "question": "What is RAG?",
      "answer": "Retrieval Augmented Generation is a technique..."
    }
  ]
}
```

**Step 2: Run Test Runner**

```bash
cd evaluation
pip install -r requirements.txt
python test_runner.py
```

**Step 3: Start Evaluator Service**

```bash
# In a separate terminal
cd evaluation
python evaluator.py
```

**Step 4: View Results**

**MongoDB**:
```bash
# MongoDB Express: http://localhost:8081
# Navigate to education > evaluation collection
```

**Dashboard**:
```bash
cd evaluation/frontend
pip install -r requirements.txt
python api.py
# Open http://localhost:8000
```

**Jupyter Notebook**:
```bash
cd evaluation
jupyter notebook evaluation_statistics.ipynb
```

---

## Understanding the Architecture

### RAG (Retrieval Augmented Generation)

**What is RAG?**

RAG is a technique that enhances LLM responses by retrieving relevant information from a knowledge base before generating an answer. This prevents hallucinations and grounds responses in factual data.

**How It Works in Education Assistant**:

1. **Document Ingestion**:
   - PDFs are uploaded via `/ingest` endpoint
   - Text is extracted using `unstructured` library
   - Text is split into chunks (configurable size, default 1000 chars)
   - Each chunk is embedded using Ollama embedding model
   - Embeddings are stored in PostgreSQL with pgvector

2. **Query Processing**:
   - User asks a question
   - Professor agent uses `search_documents` tool
   - Query is embedded using the same model
   - Cosine similarity search finds top-k relevant chunks
   - Retrieved chunks are injected into the prompt as context

3. **Response Generation**:
   - LLM generates response using retrieved context
   - Response is grounded in actual course materials
   - Significantly reduces hallucinations

**Example Flow**:

```
User Question: "What is process synchronization?"
      ↓
Query Embedding: [0.23, 0.45, 0.67, ...]
      ↓
Vector Search: Find similar embeddings in database
      ↓
Retrieved Context: "Process synchronization is a mechanism..."
      ↓
Prompt: "Given this context: [context]\n\nAnswer: [question]"
      ↓
LLM Response: "Process synchronization is..."
```

### LangGraph Agent System

**What is LangGraph?**

LangGraph is a framework for building stateful, multi-agent applications with LLMs. It uses a graph-based approach to model agent workflows.

**How It Works in Education Assistant**:

**State Definition**:
```python
class State(TypedDict):
    messages: Annotated[list, add_messages]  # Conversation history
    context: str                              # Retrieved context
```

**Graph Structure**:
```
┌──────────────┐
│ inject_prompt│  # Adds system prompt
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   chatbot    │  # LLM processes message
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ should_call_ │  # Decides if tools needed
│    tools?    │
└──┬───────┬───┘
   │       │
  NO      YES
   │       │
   │       ▼
   │  ┌──────────────┐
   │  │    tools     │  # Executes tools
   │  └──────┬───────┘
   │         │
   │         ▼
   │  ┌──────────────┐
   │  │   chatbot    │  # Processes tool results
   │  └──────┬───────┘
   │         │
   └────┬────┘
        │
        ▼
   ┌──────────────┐
   │  __end__     │  # Response complete
   └──────────────┘
```

**Key Features**:
- **Stateful**: Maintains conversation history across messages
- **Tool Calling**: Automatically decides when to use tools
- **Checkpointing**: Saves state after each step (uses PostgreSQL)
- **Streaming**: Supports streaming responses

**Example**:
```python
# User asks: "What is process scheduling?"
# Agent flow:
# 1. inject_prompt: Adds system prompt
# 2. chatbot: Realizes it needs context
# 3. tools: Calls search_documents("process scheduling")
# 4. chatbot: Generates response with retrieved context
```

### Vector Database with pgvector

**What is pgvector?**

pgvector is a PostgreSQL extension for vector similarity search. It allows storing and querying high-dimensional vectors efficiently.

**Why Use pgvector Instead of Specialized Vector DBs?**

1. **Simplicity**: Leverage existing PostgreSQL knowledge
2. **ACID Compliance**: Full transaction support
3. **Integration**: Easy to join with relational data
4. **Mature Ecosystem**: Proven database with extensive tooling

**Database Schema**:

```sql
CREATE EXTENSION vector;

CREATE TABLE documents_collection (
    id BIGSERIAL PRIMARY KEY,
    vector vector(1024),           -- Embedding vector
    text TEXT,                      -- Original text chunk
    file_id VARCHAR(50),            -- Groups chunks from same file
    filename TEXT,                  -- Source filename
    keywords TEXT[],                -- For filtering (e.g., 'evaluation')
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for fast similarity search
CREATE INDEX ON documents_collection
USING ivfflat (vector vector_cosine_ops)
WITH (lists = 100);
```

**Similarity Search**:

```python
# Find top 5 most similar documents
query_embedding = embed(query)
results = db.execute(
    "SELECT text, 1 - (vector <=> %s) AS similarity "
    "FROM documents_collection "
    "ORDER BY vector <=> %s "
    "LIMIT 5",
    (query_embedding, query_embedding)
)
```

**Indexing Strategy**:
- **IVFFlat**: Inverted file with flat vectors
- **Cosine Similarity**: Measures vector similarity (1 - cosine distance)
- **Lists**: Number of clusters (100 by default)

### Conversation Persistence

**Two-Level Storage Architecture**:

1. **LangGraph Checkpointer (PostgreSQL)**:
   - Stores complete conversation state
   - Managed by LangGraph's PostgresSaver
   - Tables: `checkpoints`, `checkpoint_blobs`, `checkpoint_writes`
   - Enables conversation resume
   - Tracks all state changes

2. **Conversation Metadata (MongoDB)**:
   - Stores only title and timestamp
   - Faster for listing conversations
   - Document: `{threadId, title, timestamp}`

**Why Two Databases?**

- **PostgreSQL**: Structured data with ACID guarantees (checkpoints)
- **MongoDB**: Flexible schema for metadata and evaluations
- **Separation of Concerns**: State vs. metadata

**How It Works**:

```python
# Saving conversation state
config = {"configurable": {"thread_id": "uuid"}}
agent.invoke({"messages": [message]}, config=config)
# Automatically saved to PostgreSQL by checkpointer

# Listing conversations
conversations = mongo.education.education_data.find()
# Returns [{threadId, title, timestamp}, ...]

# Retrieving conversation
state = agent.get_state(config)
# Loads from PostgreSQL checkpoint
```

### Evaluation Pipeline

**Architecture**:

The evaluation system uses a message queue pattern for decoupling:

```
Test Runner ──▶ RabbitMQ ──▶ Evaluator ──▶ MongoDB
```

**Why RabbitMQ?**

1. **Decoupling**: Test runner and evaluator can run independently
2. **Reliability**: Messages are persisted (durable queues)
3. **Scalability**: Can run multiple evaluator instances
4. **Async Processing**: Non-blocking evaluation

**Message Format**:

```json
{
  "test_run_id": "uuid",
  "question": "What is RAG?",
  "answer": "Retrieval Augmented Generation is...",
  "search_documents_content": "Context from vector search...",
  "thread_id": "uuid"
}
```

**Evaluation Criteria**:

1. **Correctness**:
   - Does the answer correctly address the question?
   - Verdicts: GOOD, SATISFACTORY, UNSATISFACTORY

2. **Groundedness**:
   - Is the answer based on retrieved context?
   - Does it avoid hallucination?
   - Verdicts: GOOD, SATISFACTORY, UNSATISFACTORY

**LLM-as-Judge Pattern**:

Uses a powerful LLM (Groq's gpt-oss-120b) to evaluate responses:
- Temperature: 0.0 for consistency
- Structured output with Pydantic
- Detailed analysis and verdict
- Rubric-based evaluation

---

## Development Guides

### Running Individual Components

#### API Only

```bash
cd api
pip install -r requirements.txt

# Set environment variables
export POSTGRES_URL="postgresql://root:root@localhost:5432/checkpoint"
export VECTOR_DB_URL="postgresql://root:root@localhost:5433/vector_db"
export MONGO_URL="mongodb://root:root@localhost:27017"
export OLLAMA_BASE_URL="http://localhost:11434"
# ... other env vars from .env.example

# Run API
python main.py

# API will be available at http://localhost:8080
```

#### Frontend Only

```bash
cd frontend
npm install

# Configure API URL in .env
echo 'API_URL="http://localhost:8080"' > .env

# Run dev server
npm run dev

# Frontend will be available at http://localhost:5173
```

#### Evaluation Only

```bash
cd evaluation
pip install -r requirements.txt

# Configure .env file with Groq API key

# Run test runner
python test_runner.py

# In another terminal, run evaluator
python evaluator.py
```

### Ingesting Documents

#### Via Frontend

1. Open http://localhost:5173
2. Click the upload icon (top-left)
3. Drag and drop PDF files or click to select
4. Wait for upload to complete

#### Via API

```bash
curl -X POST http://localhost:8080/ingest \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf"
```

#### Via Script (Batch Ingestion)

```bash
# For evaluation test data
python scripts/ingest_test_data.py

# This script:
# 1. Reads all PDFs from scripts/test_data/
# 2. Uploads each to /ingest endpoint
# 3. Adds 'evaluation' keyword for filtering
```

#### Creating Custom Ingestion Script

```python
import requests
from pathlib import Path

def ingest_documents(folder_path):
    api_url = "http://localhost:8080/ingest"

    for pdf_file in Path(folder_path).glob("*.pdf"):
        with open(pdf_file, 'rb') as f:
            files = {'files': (pdf_file.name, f, 'application/pdf')}
            response = requests.post(api_url, files=files)
            print(f"Uploaded {pdf_file.name}: {response.status_code}")

ingest_documents("path/to/pdfs")
```

### Running Evaluations

#### Step 1: Prepare Test Questions

Create `data/my_test.json`:

```json
{
  "questions": [
    {
      "id": 1,
      "question": "What is the main topic of this course?",
      "answer": "Expected answer..."
    },
    {
      "id": 2,
      "question": "Explain the key concept X",
      "answer": "Expected answer..."
    }
  ]
}
```

#### Step 2: Update Test Runner

Edit `evaluation/test_runner.py` to load your questions:

```python
# Load from your JSON file
with open('../data/my_test.json', 'r') as f:
    test_data = json.load(f)
    questions = test_data['questions']
```

#### Step 3: Run Evaluation

```bash
# Terminal 1: Start evaluator service
cd evaluation
python evaluator.py

# Terminal 2: Run tests
cd evaluation
python test_runner.py
```

#### Step 4: Analyze Results

**MongoDB**:
```bash
# Open MongoDB Express: http://localhost:8081
# Navigate to: education > evaluation
# View raw evaluation results
```

**Jupyter Notebook**:
```bash
cd evaluation
jupyter notebook evaluation_statistics.ipynb

# Run cells to:
# 1. List all test runs
# 2. Generate statistics
# 3. View pie charts
# 4. Compare test runs
```

**Dashboard**:
```bash
cd evaluation/frontend
python api.py

# Open http://localhost:8000
# Browse test runs and results
```

### Database Management

#### PostgreSQL (Checkpoints)

```bash
# Connect to checkpoint database
docker exec -it checkpoint-db psql -U root -d checkpoint

# View checkpoints
\dt
SELECT * FROM checkpoints LIMIT 10;

# Count checkpoints by thread
SELECT thread_id, COUNT(*)
FROM checkpoints
GROUP BY thread_id;
```

#### PostgreSQL (Vector DB)

```bash
# Connect to vector database
docker exec -it vector-db psql -U root -d vector_db

# View documents
SELECT COUNT(*) FROM documents_collection;
SELECT filename, COUNT(*) FROM documents_collection GROUP BY filename;

# Search by keyword
SELECT * FROM documents_collection WHERE 'evaluation' = ANY(keywords);

# View vector dimensions
SELECT vector_dims(vector) FROM documents_collection LIMIT 1;
```

#### MongoDB

```bash
# Connect via MongoDB Express: http://localhost:8081

# Or via mongo shell
docker exec -it mongodb mongosh -u root -p root

use education
db.education_data.find()  # View conversations
db.evaluation.find()      # View evaluations

# Count evaluations by verdict
db.evaluation.aggregate([
  {$group: {_id: "$correctness.verdict", count: {$sum: 1}}}
])
```

#### RabbitMQ

```bash
# Open management UI: http://localhost:15672
# Login: guest/guest

# View queues
# View message rates
# Purge queue if needed
```

---

## API Reference

### Endpoints

#### POST /ingest

Upload PDF files for document ingestion.

**Request**:
- Content-Type: `multipart/form-data`
- Body: `files` (array of PDF files)

**Response**:
- Status: `200` on success
- Status: `400` if no files or invalid file type

**Example**:
```bash
curl -X POST http://localhost:8080/ingest \
  -F "files=@course.pdf"
```

---

#### POST /ask_async

Ask a question and stream the response via Server-Sent Events (SSE).

**Request**:
- Content-Type: `application/json`
- Body:
  ```json
  {
    "threadId": "uuid-string",
    "question": "Your question here"
  }
  ```

**Response**:
- Content-Type: `text/event-stream`
- SSE stream with JSON data:
  ```
  data: {"type": "message", "content": "response chunk"}
  data: {"type": "tool_call", "content": {...}}
  data: {"type": "context", "content": "retrieved context"}
  ```

**Example**:
```bash
curl -X POST http://localhost:8080/ask_async \
  -H "Content-Type: application/json" \
  -d '{
    "threadId": "550e8400-e29b-41d4-a716-446655440000",
    "question": "What is process synchronization?"
  }'
```

**JavaScript Example**:
```javascript
const eventSource = new EventSource('http://localhost:8080/ask_async');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data.content);
};
```

---

#### GET /conversations

List all conversations.

**Response**:
```json
[
  {
    "threadId": "uuid",
    "title": "Conversation title",
    "timestamp": "2025-12-24 10:30:00"
  }
]
```

**Example**:
```bash
curl http://localhost:8080/conversations
```

---

#### GET /conversation/{threadId}

Retrieve full conversation state.

**Response**:
```json
{
  "values": {
    "messages": [...],
    "context": "..."
  },
  "metadata": {...}
}
```

**Example**:
```bash
curl http://localhost:8080/conversation/550e8400-e29b-41d4-a716-446655440000
```

---

## Database Schemas

### PostgreSQL (Checkpoints)

Managed automatically by LangGraph's PostgresSaver.

**Tables**:
- `checkpoints`: Main checkpoint data
- `checkpoint_blobs`: Large binary data
- `checkpoint_writes`: Individual writes

**Schema** (simplified):
```sql
CREATE TABLE checkpoints (
    thread_id TEXT,
    checkpoint_ns TEXT DEFAULT '',
    checkpoint_id TEXT,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB,
    metadata JSONB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);
```

---

### PostgreSQL (Vector DB)

**Documents Collection**:
```sql
CREATE TABLE documents_collection (
    id BIGSERIAL PRIMARY KEY,
    vector vector(1024),           -- Embedding (dimension = DOCUMENTS_VECTOR_DIMENSION)
    text TEXT NOT NULL,             -- Chunk text
    file_id VARCHAR(50),            -- UUID grouping chunks from same file
    filename TEXT,                  -- Original filename
    keywords TEXT[],                -- Array of keywords (e.g., ['evaluation'])
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON documents_collection
USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);

CREATE INDEX ON documents_collection (file_id);
CREATE INDEX ON documents_collection USING GIN (keywords);
```

**Difficulties Collection**:
```sql
CREATE TABLE difficulties_collection (
    id BIGSERIAL PRIMARY KEY,
    vector vector(1024),
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON difficulties_collection
USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);
```

---

### MongoDB

**Database**: `education`

**Collection**: `education_data` (Conversation Titles)
```json
{
  "_id": ObjectId("..."),
  "threadId": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Process Synchronization Questions",
  "timestamp": "2025-12-24 10:30:00"
}
```

**Collection**: `evaluation` (Evaluation Results)
```json
{
  "_id": ObjectId("..."),
  "test_run_id": "550e8400-e29b-41d4-a716-446655440001",
  "question": "What is RAG?",
  "answer": "Retrieval Augmented Generation is...",
  "search_documents_content": "Context retrieved from vector search...",
  "correctness": {
    "analysis": "The answer correctly explains RAG...",
    "verdict": "good"
  },
  "groundedness": {
    "analysis": "The answer is well-grounded in the retrieved context...",
    "verdict": "good"
  },
  "timestamp": "2025-12-24T10:30:00.000Z"
}
```

**Indexes**:
```javascript
db.evaluation.createIndex({ "test_run_id": 1 })
db.evaluation.createIndex({ "timestamp": -1 })
db.education_data.createIndex({ "threadId": 1 }, { unique: true })
```

---

## Configuration Reference

### Environment Variables

#### API Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_URL` | PostgreSQL connection for checkpointing | - | Yes |
| `VECTOR_DB_URL` | PostgreSQL+pgvector connection for RAG | - | Yes |
| `MONGO_URL` | MongoDB connection | - | Yes |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` | Yes |
| `EMBEDDING_MODEL` | Embedding model name | `qwen3-embedding:0.6b` | Yes |
| `TITLE_GENERATION_MODEL` | Model for title generation | `qwen3:8b` | Yes |
| `QUESTION_GENERATOR_MODEL` | Model for question generation | `qwen3:8b` | Yes |
| `PROFESSOR_MODEL` | Main conversational model | `qwen3:8b` | Yes |
| `DOCUMENTS_COLLECTION_NAME` | Vector table name | `documents_collection` | No |
| `DOCUMENTS_VECTOR_DIMENSION` | Embedding dimension | `1024` | No |
| `DIFFICULTIES_COLLECTION_NAME` | Difficulties table name | `difficulties_collection` | No |
| `TEXT_SPLITTER_CHUNK_SIZE` | Text chunk size | `1000` | No |
| `API_PORT` | API server port | `8080` | No |
| `API_HOST` | API server host | `localhost` | No |
| `EVALUATION` | Enable evaluation mode (0 or 1) | `0` | No |

#### Frontend Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `API_URL` | Backend API URL | `http://localhost:8080` | No |

#### Evaluation Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `API_URL` | Backend API URL | `http://localhost:8080` | No |
| `RABBITMQ_HOST` | RabbitMQ host | `localhost` | Yes |
| `RABBITMQ_PORT` | RabbitMQ port | `5672` | Yes |
| `RABBITMQ_USER` | RabbitMQ username | `guest` | Yes |
| `RABBITMQ_PASSWORD` | RabbitMQ password | `guest` | Yes |
| `MONGO_URL` | MongoDB connection | - | Yes |
| `GROQ_API_KEY` | Groq API key for LLM judge | - | Yes |

### Model Selection

**Embedding Models** (choose one):
```bash
# Small and fast (recommended)
EMBEDDING_MODEL="qwen3-embedding:0.6b"  # 1024 dims

# Alternative options
EMBEDDING_MODEL="nomic-embed-text"      # 768 dims (requires dimension change)
EMBEDDING_MODEL="mxbai-embed-large"     # 1024 dims
```

**Conversational Models** (choose one):
```bash
# Balanced performance (recommended)
PROFESSOR_MODEL="qwen3:8b"

# Larger models (better quality, slower)
PROFESSOR_MODEL="llama3.1:8b"
PROFESSOR_MODEL="mistral:7b"
PROFESSOR_MODEL="qwen3:14b"

# Smaller models (faster, lower quality)
PROFESSOR_MODEL="qwen3:4b"
PROFESSOR_MODEL="phi3:3.8b"
```

**Important**: If you change `EMBEDDING_MODEL` to one with different dimensions:
1. Update `DOCUMENTS_VECTOR_DIMENSION` to match
2. Re-ingest all documents (embeddings are incompatible)
3. Drop and recreate vector database tables

---

## Troubleshooting

### Common Issues

#### 1. "Connection refused" errors

**Symptoms**: API can't connect to databases or Ollama

**Solutions**:
```bash
# Check all services are running
docker-compose ps

# Check Ollama is running
curl http://localhost:11434/api/tags

# For Docker on Mac/Windows, use host.docker.internal
# In api/.env:
OLLAMA_BASE_URL="http://host.docker.internal:11434"
```

#### 2. "Model not found" errors

**Symptoms**: `Error: model 'qwen3:8b' not found`

**Solutions**:
```bash
# Pull the model
ollama pull qwen3:8b

# List available models
ollama list

# Update .env to use available model
```

#### 3. Vector dimension mismatch

**Symptoms**: `ERROR: vector dimension mismatch`

**Solutions**:
```bash
# Drop and recreate vector database
docker-compose down
docker volume rm education-assistant_vector_data
docker-compose up -d vector-db

# Re-ingest documents
curl -X POST http://localhost:8080/ingest -F "files=@document.pdf"
```

#### 4. Slow response times

**Symptoms**: Long wait for responses

**Solutions**:
- Use smaller models (qwen3:4b instead of qwen3:8b)
- Reduce chunk size (TEXT_SPLITTER_CHUNK_SIZE=500)
- Reduce top-k in vector search (edit toolbox.py)
- Ensure Ollama has sufficient RAM

#### 5. Frontend can't connect to API

**Symptoms**: Network errors in browser console

**Solutions**:
```bash
# Check API is running
curl http://localhost:8080/conversations

# Check CORS is enabled (should be by default)
# In frontend/.env:
API_URL="http://localhost:8080"

# Clear browser cache and reload
```

#### 6. RabbitMQ connection errors

**Symptoms**: `Connection refused to rabbitmq:5672`

**Solutions**:
```bash
# Check RabbitMQ is running
docker-compose ps rabbitmq

# Check RabbitMQ management UI
# Open http://localhost:15672 (guest/guest)

# For local evaluation, use localhost
# In evaluation/.env:
RABBITMQ_HOST="localhost"

# For Docker evaluation, use service name
# In docker-compose.yml:
RABBITMQ_HOST="rabbitmq"
```

#### 7. Out of memory errors

**Symptoms**: Container crashes, "Killed" messages

**Solutions**:
```bash
# Increase Docker memory limit (Docker Desktop)
# Preferences > Resources > Memory > 8GB+

# Use smaller models
PROFESSOR_MODEL="qwen3:4b"
EMBEDDING_MODEL="nomic-embed-text"

# Reduce chunk size
TEXT_SPLITTER_CHUNK_SIZE=500
```

### Debugging Tips

**View Logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 api
```

**Check Database Connections**:
```bash
# PostgreSQL (Checkpoints)
docker exec -it checkpoint-db psql -U root -d checkpoint -c "\dt"

# PostgreSQL (Vector)
docker exec -it vector-db psql -U root -d vector_db -c "\dt"

# MongoDB
docker exec -it mongodb mongosh -u root -p root --eval "db.adminCommand('listDatabases')"
```

**Test API Endpoints**:
```bash
# Check API health
curl http://localhost:8080/docs

# Test conversation list
curl http://localhost:8080/conversations

# Test ingest
curl -X POST http://localhost:8080/ingest -F "files=@test.pdf"
```

**Monitor Resource Usage**:
```bash
# Docker resource usage
docker stats

# System resource usage
htop  # or top on macOS
```

---

## Contributing

Contributions are welcome! Please follow these guidelines:

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and test thoroughly
4. Commit with clear messages: `git commit -m "feat: add new feature"`
5. Push to your fork: `git push origin feature/my-feature`
6. Open a Pull Request

### Code Style

**Python**:
- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and short

**JavaScript/React**:
- Use ESLint configuration provided
- Follow React best practices
- Use functional components and hooks
- Keep components small and reusable

**Commit Messages**:
Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

### Testing

Before submitting a PR:
1. Test all API endpoints
2. Test frontend functionality
3. Run evaluation pipeline
4. Check for console errors
5. Verify Docker build works

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add description of changes
4. Link related issues
5. Request review from maintainers

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Lucas Noronha

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Acknowledgments

- **LangChain & LangGraph**: For the agent framework
- **Ollama**: For local LLM inference
- **pgvector**: For vector similarity search in PostgreSQL
- **FastAPI**: For the modern API framework
- **React & Vite**: For the frontend framework
- **Groq**: For high-performance LLM evaluation

---

## Additional Resources

### Documentation
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Ollama Documentation](https://ollama.com/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

### Related Projects
- [LangChain](https://github.com/langchain-ai/langchain)
- [Ollama](https://github.com/ollama/ollama)
- [pgvector](https://github.com/pgvector/pgvector)

### Community
- Report issues: [GitHub Issues](https://github.com/yourusername/education-assistant/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/education-assistant/discussions)

---

**Built with ❤️ using AI-powered tools and open-source technologies.**
