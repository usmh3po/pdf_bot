"""Agno agent configuration using OpenAI provider."""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat

from app.agent.knowledge import get_knowledge
from app.config import get_settings


# Global database instance for session/memory persistence
_db: SqliteDb | None = None


def get_db() -> SqliteDb:
    """Get or create the database instance."""
    global _db
    if _db is None:
        _db = SqliteDb(db_file="agno.db")
    return _db


def create_agent() -> Agent:
    """Create and configure an Agno agent with OpenAI provider, memory, and knowledge support."""
    settings = get_settings()
    db = get_db()
    knowledge = get_knowledge()

    # Configure OpenAI model with API key from settings
    model = OpenAIChat(
        id="gpt-4.1-nano",
        api_key=settings.openai_api_key,
    )
    
    # Create agent instance with model, database, memory, and knowledge enabled
    # Agno will automatically maintain conversation history per user_id
    # and search knowledge base when relevant
    agent = Agent(
        name="PDF Bot Agent",
        model=model,
        db=db,
        knowledge=knowledge,
        enable_user_memories=True,  # Enable Agno's built-in memory system
        search_knowledge=True,  # Enable agentic knowledge search (recommended)
        description="A helpful assistant that answers questions about uploaded PDF documents.",
    )
    
    return agent

