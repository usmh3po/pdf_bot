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
# Edit .env and add your OPENAI_API_KEY
```

## Running the Application

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

## Cursor Configuration

_This section will be expanded as the project develops to document Cursor setup, MCP servers, linters, and IDE features used._


## Architecture

_Architecture overview and design decisions will be documented here as the project develops._

## Trade-offs & Limitations

_Trade-offs, limitations, and future improvements will be documented here._

## License

_To be determined_

