"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message request model."""
    
    message: str = Field(..., description="User message to send to the agent")
    session_id: str | None = Field(None, description="Optional session ID for chat history")


class ChatResponse(BaseModel):
    """Chat response model."""
    
    content: str = Field(..., description="Agent response content")
    session_id: str | None = Field(None, description="Session ID for this conversation")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Additional error details")

