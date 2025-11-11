"""Application runner that integrates FastAPI and NiceGUI."""

import uvicorn
from nicegui import ui

# Import after NiceGUI is initialized
from app.main import app

# Start NiceGUI with FastAPI
# ui.run_with() integrates NiceGUI with the FastAPI app
if __name__ == "__main__":
    # Configure NiceGUI to work with FastAPI
    # This mounts NiceGUI routes onto the FastAPI app
    ui.run_with(app)
    
    # Start the server using uvicorn
    # NiceGUI routes should now be available
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

