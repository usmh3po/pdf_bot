"""NiceGUI chat interface for streaming chatbot."""

import asyncio
from nicegui import ui
import httpx


def create_chat_ui() -> None:
    async def check_upload_status(file_id: str, status_label: ui.label, filename: str) -> None:
        """Poll upload status until processing is complete."""
        max_attempts = 60  # Check for up to 5 minutes (5 second intervals)
        attempt = 0
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            while attempt < max_attempts:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                try:
                    response = await client.get(
                        f"http://localhost:8000/api/upload/status/{file_id}",
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        status_value = result.get("status", "").lower()
                        
                        if "completed" in status_value or "success" in status_value:
                            status_label.text = "Ready"
                            status_label.classes("text-sm text-green-500")
                            return
                        elif "failed" in status_value or "error" in status_value:
                            status_label.text = "Failed"
                            status_label.classes("text-sm text-red-500")
                            return
                        else:
                            status_label.text = "Processing..."
                            status_label.classes("text-sm text-yellow-500")
                    
                    attempt += 1
                except Exception:
                    attempt += 1
            
            # Timeout
            status_label.text = "Timeout"
            status_label.classes("text-sm text-orange-500")
    
    async def handle_pdf_upload(e) -> None:
        """Handle PDF file upload with async status updates."""
        upload_status.text = "Uploading..."
        upload_status.classes("text-sm text-blue-500")
        
        try:
            # NiceGUI upload event structure: e.file is the uploaded file object
            # e.file.name is filename, e.file.read() is async and gets file content
            uploaded_file = e.file
            filename = uploaded_file.name
            file_content = await uploaded_file.read()
            
            # Upload to API
            async with httpx.AsyncClient(timeout=120.0) as client:
                files = {"file": (filename, file_content, "application/pdf")}
                response = await client.post(
                    "http://localhost:8000/api/upload/pdf",
                    files=files,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    file_id = result.get("file_id")
                    filename = result.get("filename")
                    
                    upload_status.text = f"Processing {filename}..."
                    upload_status.classes("text-sm text-yellow-500")
                    
                    # Add to uploaded files list
                    with uploaded_files_container:
                        file_row = ui.row().classes("w-full items-center gap-2 p-2 bg-gray-100 rounded")
                        file_label = ui.label(f"📄 {filename}").classes("flex-1")
                        file_status = ui.label("Processing...").classes("text-sm text-yellow-500")
                    
                    # Poll for status updates
                    await check_upload_status(file_id, file_status, filename)
                else:
                    error_msg = response.json().get("detail", "Upload failed")
                    upload_status.text = f"Error: {error_msg}"
                    upload_status.classes("text-sm text-red-500")
                    
        except Exception as e:
            upload_status.text = f"Upload error: {str(e)}"
            upload_status.classes("text-sm text-red-500")
    
    async def send_message() -> None:
        """Send message and stream response."""
        nonlocal session_id
        
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
                    json={"message": message, "session_id": session_id},
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
                                
                                # Check for session ID in response
                                if "__SESSION_ID__:" in content:
                                    # Extract session ID
                                    parts = content.split("__SESSION_ID__:")
                                    if len(parts) > 1:
                                        session_part = parts[1].split("__")[0]
                                        session_id = session_part
                                        # Remove session ID from displayed content
                                        content = parts[0]
                                
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
    
    # Session ID for maintaining chat history across messages
    session_id: str | None = None
    
    with ui.column().classes("w-full max-w-4xl mx-auto p-4 gap-4"):
        ui.label("PDF Bot Chat").classes("text-2xl font-bold")
        
        # PDF Upload section
        with ui.card().classes("w-full p-4"):
            ui.label("Upload PDF Document").classes("text-lg font-semibold mb-2")
            with ui.row().classes("w-full gap-2 items-center"):
                file_upload = ui.upload(
                    on_upload=handle_pdf_upload,
                    auto_upload=True,
                    max_file_size=10 * 1024 * 1024,  # 10MB limit
                ).classes("flex-1")
                file_upload.props('accept=".pdf"')
                upload_status = ui.label("").classes("text-sm text-gray-500")
        
        # Uploaded files list
        uploaded_files_container = ui.column().classes("w-full")
        
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
    
    

    


