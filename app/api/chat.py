"""Streaming chat endpoint for agent interactions."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from agno.agent import Agent

from app.agent.agent import create_agent
from app.api.models import ChatMessage, ErrorResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


async def _stream_agent_response(agent: Agent, message: str, session_id: str | None = None) -> str:
    """Stream agent response token by token using Agno's built-in memory system."""
    try:
        import uuid
        
        # Use session_id as user_id for Agno's memory system
        # If no session_id provided, generate one (Agno will create memories for this user)
        user_id = session_id if session_id else str(uuid.uuid4())
        
        # Run agent and stream the response
        # Agno automatically maintains conversation history per user_id when enable_user_memories=True
        # The agent will automatically include previous conversation context
        response_coro = agent.arun(input=message, stream=True, user_id=user_id)
        
        # Check if it's a coroutine (needs await) or already an async generator
        import inspect
        if inspect.iscoroutine(response_coro):
            response_stream = await response_coro
        else:
            response_stream = response_coro

        # Stream the response chunks
        async for chunk in response_stream:
            if chunk:
                # Handle both string chunks and objects with content attribute
                chunk_content = ""
                if isinstance(chunk, str):
                    chunk_content = chunk
                elif hasattr(chunk, 'content'):
                    chunk_content = chunk.content
                else:
                    chunk_content = str(chunk)
                
                yield chunk_content
        
        # Yield session ID (user_id) as metadata for UI to track
        # Format: special marker so UI can extract it
        yield f'\n__SESSION_ID__:{user_id}__'
                
    except Exception as e:
        # Yield error as JSON
        error_msg = f'{{"error": "Agent error", "detail": "{str(e)}"}}'
        yield error_msg


@router.post("/stream")
async def stream_chat(request: ChatMessage) -> StreamingResponse:
    """Stream agent response token by token with session support."""
    try:
        agent = create_agent()
        
        # Create async generator for streaming
        async def generate() -> str:
            async for chunk in _stream_agent_response(
                agent=agent,
                message=request.message,
                session_id=request.session_id,
            ):
                # Format as Server-Sent Events (SSE) for better compatibility
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create streaming response: {str(e)}",
        )


@router.post("/", response_model=None)
async def chat(request: ChatMessage) -> StreamingResponse:
    """Chat endpoint that streams responses (alias for /stream)."""
    return await stream_chat(request)

