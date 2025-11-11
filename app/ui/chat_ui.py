"""NiceGUI chat interface for streaming chatbot."""

import asyncio
from nicegui import ui
import httpx


def create_chat_ui() -> None:
    async def send_message() -> None:
        """Send message and stream response."""
        message = message_input.value.strip()
        if not message:
            return
        
        # Disable input while processing
        message_input.disable()
        send_button.disable()
        status_label.text = "Sending..."
        
        # Add user message to chat
        with messages_container:
            ui.label(f"You: {message}").classes("text-blue-600 font-semibold")
        
        # Clear input
        message_input.value = ""
        
        # Create response area for streaming
        with messages_container:
            response_container = ui.column().classes("w-full")
            response_text = ui.label("Bot: ").classes("text-green-600 font-semibold")
            response_content = ui.label("").classes("text-gray-800")
        
        try:
            # Stream response from API
            status_label.text = "Streaming response..."
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    "http://localhost:8000/api/chat/stream",
                    json={"message": message, "session_id": None},
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        response_content.text = f"Error: {response.status_code} - {error_text.decode()}"
                        status_label.text = "Error occurred"
                        return
                    
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        
                        # Parse SSE format: "data: <content>\n\n"
                        while "\n\n" in buffer:
                            line, buffer = buffer.split("\n\n", 1)
                            if line.startswith("data: "):
                                content = line[6:]  # Remove "data: " prefix
                                # Append to response
                                current_text = response_content.text
                                response_content.text = current_text + content
                                # Small delay to show streaming effect
                                await asyncio.sleep(0.01)
            
            status_label.text = "Response complete"
            
        except httpx.RequestError as e:
            response_content.text = f"Connection error: {str(e)}"
            status_label.text = "Connection failed"
        except Exception as e:
            response_content.text = f"Error: {str(e)}"
            status_label.text = "Error occurred"
        finally:
            # Re-enable input
            message_input.enable()
            send_button.enable()
            # Note: NiceGUI Input doesn't have a focus() method
            # The input will remain focused after re-enabling


    """Create the chat UI with streaming support."""
    ui.page_title("PDF Bot - Chat")
    
    with ui.column().classes("w-full max-w-4xl mx-auto p-4 gap-4"):
        ui.label("PDF Bot Chat").classes("text-2xl font-bold")
        
        # Chat messages display area
        with ui.column().classes("w-full border rounded-lg p-4 min-h-[400px] max-h-[600px] overflow-y-auto bg-gray-50"):
            messages_container = ui.column().classes("w-full gap-2")
        
        # Input area
        with ui.row().classes("w-full gap-2"):
            message_input = ui.input(
                placeholder="Type your message here...",
            ).classes("flex-1")
            
            send_button = ui.button("Send", on_click=send_message).classes("px-6")
            
            # Handle Enter key press
            async def handle_enter() -> None:
                await send_message()
            message_input.on("keydown.enter", handle_enter)
        
        # Status indicator
        status_label = ui.label("").classes("text-sm text-gray-500")
    

    


