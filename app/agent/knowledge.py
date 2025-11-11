"""Agno Knowledge base configuration for PDF document storage and retrieval."""

from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.chunking.fixed import FixedSizeChunking
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.vectordb.pgvector import PgVector
from agno.db.sqlite import SqliteDb

from app.config import get_settings


# Global knowledge instance
_knowledge: Knowledge | None = None
# Global contents database instance for tracking content status
_contents_db: SqliteDb | None = None


def get_contents_db() -> SqliteDb:
    """Get or create the contents database instance for tracking content status."""
    global _contents_db
    if _contents_db is None:
        _contents_db = SqliteDb(db_file="agno.db")
    return _contents_db


def get_knowledge() -> Knowledge:
    """Get or create the Knowledge base instance."""
    global _knowledge
    if _knowledge is None:
        settings = get_settings()
        
        # Build PostgreSQL connection URL
        db_url = (
            f"postgresql+psycopg://{settings.postgres_user}:{settings.postgres_password}"
            f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
        )
        
        # Configure OpenAI embedder with API key
        embedder = OpenAIEmbedder(
            id="text-embedding-3-small",
            api_key=settings.openai_api_key,
        )
        
        # Configure vector database with embedder
        vector_db = PgVector(
            table_name="pdf_knowledge",
            db_url=db_url,
            embedder=embedder,
        )
        
        # Get contents database for tracking content status
        contents_db = get_contents_db()
        
        # Create knowledge base with semantic chunking for better context
        _knowledge = Knowledge(
            name="PDF Documents",
            vector_db=vector_db,
            contents_db=contents_db,  # Database for tracking content metadata and status
            max_results=10,  # Return top 10 most relevant chunks
        )
    
    return _knowledge


def get_pdf_reader() -> PDFReader:
    """Get PDF reader with semantic chunking strategy."""
    return PDFReader(
        chunking_strategy=FixedSizeChunking(
            chunk_size=1000
        ),
    )

