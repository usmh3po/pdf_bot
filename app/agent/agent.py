"""Agno agent configuration using OpenAI provider."""

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from app.config import get_settings


def create_agent() -> Agent:
    """Create and configure an Agno agent with OpenAI provider."""
    settings = get_settings()

    # Configure OpenAI model with API key from settings
    model = OpenAIChat(
        id="gpt-4.1-nano",
        api_key=settings.openai_api_key,
    )
    
    # Create agent instance with model
    agent = Agent(
        name="PDF Bot Agent",
        model=model,
        description="A helpful assistant that answers questions about uploaded PDF documents.",
    )
    
    return agent

