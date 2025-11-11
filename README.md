# PDF Bot - Document QA Chatbot

A minimal Document QA Chatbot built with FastAPI, Agno, and NiceGUI that streams agent responses and handles PDF document uploads.

## Overview

This application provides a real-time streaming chatbot interface that can answer questions about uploaded PDF documents using OpenAI's LLM through the Agno agent framework.

## Features

- **Streaming Chatbot**: Real-time token-by-token streaming of agent responses
- **PDF Upload & Parsing**: Upload PDF documents and make them available to the agent
- **Async Status Signals**: Non-blocking status updates in the UI
- **Session Management**: Preserves chat history using Agno's session features

## Setup

### Prerequisites

- Python 3.13+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd pdf_bot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e ".[dev]"
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and PostgreSQL settings
```

5. Set up PostgreSQL database:
```bash
# Connect to PostgreSQL (on port 5433)
psql -h localhost -p 5433 -U postgres

# Create the database
CREATE DATABASE pdf_bot;

# Connect to the new database
\c pdf_bot

# Enable pgvector extension (required for vector search)
CREATE EXTENSION IF NOT EXISTS vector;

# Verify extension is installed
\dx

# Exit PostgreSQL
\q
```

**Note:** Make sure your `.env` file includes the PostgreSQL connection settings:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=pdf_bot
```

## Running the Application

### Option 1: Using the integrated runner (Recommended)
```bash
python run.py
```

### Option 2: Using uvicorn (API only, no UI)
```bash
uvicorn app.main:app --reload
```

Then open your browser to the URL shown in the terminal (typically `http://localhost:8000`).

## Testing

Run all tests:
```bash
pytest
```

Run specific test suites:
```bash
pytest tests/unit
pytest tests/integration
```

## Project Structure

```
pdf_bot/
├── app/
│   ├── main.py          # FastAPI application entry point
│   ├── api/             # API endpoints
│   ├── agent/           # Agno agent configuration
│   ├── parsing/         # PDF parsing logic
│   └── ui/              # NiceGUI UI components
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── data/            # Test data (sample PDFs)
├── .env.example         # Environment variable template
├── pyproject.toml       # Project configuration
└── README.md           # This file
```

## Architecture

### System Overview

The PDF Bot follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    NiceGUI UI Layer                      │
│              (Frontend - chat_ui.py)                     │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/SSE
┌────────────────────▼────────────────────────────────────┐
│                 FastAPI API Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Chat Router  │  │Upload Router │  │  Main App    │  │
│  │  (chat.py)   │  │ (upload.py)  │  │  (main.py)   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼─────────────────┼──────────────────┼─────────┘
          │                 │                  │
┌─────────▼─────────────────▼──────────────────▼─────────┐
│              Agno Agent Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Agent      │  │  Knowledge   │  │   Memory     │  │
│  │  (agent.py)  │  │(knowledge.py)│  │  (SqliteDb)  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼─────────────────┼──────────────────┼─────────┘
          │                 │                  │
┌─────────▼─────────────────▼──────────────────▼─────────┐
│              Data Storage Layer                          │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │  PostgreSQL  │  │   SQLite     │                    │
│  │  (pgvector)  │  │  (agno.db)  │                    │
│  │  - Vectors   │  │  - Sessions  │                    │
│  │  - Chunks    │  │  - Memories  │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

### Key Components

1. **FastAPI Application** (`app/main.py`)
   - Main application entry point
   - CORS middleware configuration
   - Router registration
   - NiceGUI integration

2. **API Endpoints** (`app/api/`)
   - **Chat Router**: Streaming chat endpoint with session management
   - **Upload Router**: PDF upload, status checking, and listing
   - **Models**: Pydantic models for request/response validation

3. **Agno Agent** (`app/agent/`)
   - **Agent Configuration**: OpenAI model setup with memory and knowledge
   - **Knowledge Base**: PgVector for vector storage, PDFReader for parsing
   - **Memory System**: SQLite-based session and conversation history

4. **UI Layer** (`app/ui/`)
   - NiceGUI-based chat interface
   - Real-time streaming response display
   - PDF upload with async status updates

5. **Configuration** (`app/config.py`)
   - Pydantic Settings for environment variable management
   - Singleton pattern for settings access

### Data Flow

1. **PDF Upload Flow**:
   ```
   User → UI Upload → FastAPI /api/upload/pdf → Save to disk → 
   Agno Knowledge.add_content() → PDFReader → Semantic Chunking → 
   OpenAI Embedder → PgVector Storage → Status Update
   ```

2. **Chat Flow**:
   ```
   User Message → UI → FastAPI /api/chat/stream → Agno Agent.arun() → 
   Knowledge Search (if relevant) → OpenAI LLM → Stream Response → UI
   ```

3. **Session Management**:
   ```
   Session ID → Agno Memory System → SQLite Database → 
   Context Retrieval → Agent Response with History
   ```

### Design Decisions

- **Streaming Responses**: Uses Server-Sent Events (SSE) for real-time token streaming
- **Async Processing**: PDF processing runs in thread executors to avoid event loop conflicts
- **Vector Search**: PgVector with OpenAI embeddings for semantic document search
- **Session Persistence**: Agno's built-in memory system for conversation history
- **Type Safety**: Pydantic models throughout for validation and type checking

## Trade-offs & Limitations

### Trade-offs

1. **Synchronous PDF Processing in Async Context**
   - **Decision**: Run `knowledge.add_content()` in thread executor
   - **Reason**: Agno's knowledge methods may use `asyncio.run()` internally
   - **Trade-off**: Slightly more complex code, but avoids event loop conflicts

2. **SQLite for Session Storage**
   - **Decision**: Use SQLite for Agno's memory system
   - **Reason**: Simple, file-based, no additional setup required
   - **Trade-off**: Not suitable for distributed deployments (would need PostgreSQL)

3. **PostgreSQL for Vector Storage**
   - **Decision**: Use PgVector for document embeddings
   - **Reason**: Efficient vector similarity search, production-ready
   - **Trade-off**: Requires PostgreSQL setup (more complex than SQLite)

4. **Streaming vs Batch Processing**
   - **Decision**: Stream agent responses token-by-token
   - **Reason**: Better user experience, feels more responsive
   - **Trade-off**: More complex error handling, requires SSE support

5. **File Storage**
   - **Decision**: Store uploaded PDFs temporarily in `uploads/` directory
   - **Reason**: Simple, no additional infrastructure needed
   - **Trade-off**: Files persist on disk (should implement cleanup)

### Limitations

1. **Single User Session**
   - Current implementation uses session IDs but doesn't enforce authentication
   - Multiple users could potentially access each other's sessions if they know the ID

2. **File Size Limits**
   - No explicit file size validation (relies on NiceGUI's 10MB default)
   - Large PDFs may take significant time to process

3. **No PDF Deletion**
   - Once uploaded, PDFs cannot be deleted through the UI
   - Files remain in the knowledge base and on disk

4. **Error Recovery**
   - Limited error recovery for failed PDF processing
   - No retry mechanism for failed embeddings

5. **No Rate Limiting**
   - API endpoints don't have rate limiting
   - Could be overwhelmed by excessive requests

6. **Synchronous Knowledge Operations**
   - Knowledge base operations run in thread executors
   - May not scale well under high concurrent load

### Future Improvements

1. **Authentication & Authorization**
   - Add user authentication
   - Implement proper session management
   - Multi-user support with isolation

2. **File Management**
   - Add PDF deletion endpoint
   - Implement file cleanup for old uploads
   - Add file size limits and validation

3. **Performance Optimizations**
   - Implement caching for frequently accessed documents
   - Add connection pooling for PostgreSQL
   - Optimize vector search queries

4. **Error Handling**
   - Better error messages for users
   - Retry mechanisms for failed operations
   - Comprehensive logging

5. **Monitoring & Observability**
   - Add structured logging
   - Health check improvements
   - Metrics collection

6. **Additional Features**
   - Support for multiple file formats (DOCX, TXT, etc.)
   - Batch upload functionality
   - Export chat history
   - Search across uploaded documents

## Cursor Configuration

This project uses the following development tools and configurations:

### Cursor Settings

Recommended Cursor IDE settings for this project:

1. **Python Interpreter**: Set to use the virtual environment (`venv/`)
2. **Format on Save**: Enabled (uses Ruff formatter)
3. **Lint on Save**: Enabled (uses Ruff linter)
4. **Type Checking**: Enabled (uses MyPy)
5. **Auto Import**: Enabled for better code completion

### MCP Servers

Model Context Protocol (MCP) servers recommended for this project:

#### 1. **Filesystem MCP Server**
- **Purpose**: File operations, directory navigation, reading/writing files
- **Use Cases**: 
  - Reading project files
  - Creating new modules
  - Managing uploads directory
- **Configuration**: Usually comes pre-installed with Cursor

#### 2. **PostgreSQL MCP Server** (Optional)
- **Purpose**: Direct database access and queries
- **Use Cases**:
  - Inspecting vector embeddings in `pdf_knowledge` table
  - Debugging knowledge base content
  - Running SQL queries for troubleshooting
- **Configuration**: 
  ```json
  {
    "mcpServers": {
      "postgres": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres"],
        "env": {
          "POSTGRES_CONNECTION_STRING": "postgresql://postgres:password@localhost:5433/pdf_bot"
        }
      }
    }
  }
  ```

#### 3. **Git MCP Server** (Optional)
- **Purpose**: Version control operations
- **Use Cases**:
  - Viewing git history
  - Creating commits
  - Managing branches
- **Configuration**: Usually available as an extension

#### 4. **Python MCP Server** (Optional)
- **Purpose**: Python-specific tooling
- **Use Cases**:
  - Running Python scripts
  - Executing tests
  - Managing dependencies
- **Configuration**: Can be set up for virtual environment access

### Cursor Rules File

A `.cursorrules` file is recommended to guide AI assistance. Example:

```markdown
# PDF Bot Project Rules

## Code Style
- Use Python 3.13+ features (type unions, pattern matching)
- Follow PEP 8 with 100 character line length
- Use type hints for all functions
- Use Pydantic models for data validation

## Architecture
- FastAPI for API layer
- Agno for agent orchestration
- NiceGUI for UI
- PostgreSQL with pgvector for vector storage
- SQLite for session management

## Testing
- Write unit tests for all API endpoints
- Use pytest with async support
- Mock external dependencies (OpenAI, databases)

## Error Handling
- Validate all inputs (file type, size, content)
- Provide clear error messages
- Clean up resources on errors
```

### Linters & Formatters

- **Ruff**: Fast Python linter and formatter
  - Configuration in `pyproject.toml`
  - Line length: 100 characters
  - Target version: Python 3.13
  - Enabled rules: E, F, I, N, W, UP

- **MyPy**: Static type checker
  - Configuration in `pyproject.toml`
  - Python version: 3.13
  - Warns on return any and unused configs
  - Ignores missing imports (for third-party libraries)

### Testing

- **pytest**: Test framework
  - Async mode: auto
  - Test discovery: `tests/` directory
  - Verbose output with short tracebacks

### IDE Features

- **Type Hints**: Full type annotations throughout the codebase
- **Pydantic Models**: Type-safe request/response validation
- **Modern Python**: Uses Python 3.13 features (type unions, pattern matching, etc.)

### Development Workflow

1. **Code Quality**: Run `ruff check .` and `ruff format .` before committing
2. **Type Checking**: Run `mypy app/` to check types
3. **Testing**: Run `pytest` to execute all tests
4. **Environment**: Use `.env` file for configuration (see `.env.example`)

### Cursor-Specific Tips

1. **Context Awareness**: Cursor AI understands the project structure and can help with:
   - FastAPI endpoint creation
   - Agno agent configuration
   - Pydantic model definitions
   - Test writing

2. **Code Generation**: When asking for code:
   - Specify the file path (e.g., "add to `app/api/upload.py`")
   - Mention existing patterns to follow
   - Request type hints and error handling

3. **Debugging**: Use Cursor's built-in terminal and debugger:
   - Set breakpoints in FastAPI routes
   - Inspect async operations
   - Monitor database queries

## License

_To be determined_

