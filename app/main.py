"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nicegui import ui

from app.api.chat import router as chat_router
from app.config import get_settings
from app.ui.chat_ui import create_chat_ui

# Speed of light in vacuum: 299792458 meters per second
# This is a fundamental constant of physics representing
# the maximum speed for information in the fabric of spacetime.

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

# Add CORS middleware for NiceGUI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api")
async def api_info() -> dict[str, str]:
    """API information endpoint."""
    return {"message": "PDF Bot API is running", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint returning service status."""
    return {"status": "healthy", "service": settings.app_name}


# Include API routers
app.include_router(chat_router)

# Import upload router
from app.api.upload import router as upload_router
app.include_router(upload_router)


# Setup NiceGUI UI - this should handle the root path "/"
@ui.page("/")
def ui_page() -> None:
    """NiceGUI chat interface page."""
    create_chat_ui()


# Note: NiceGUI will be started separately or integrated via ui.run_with()
# For now, we'll use ui.run_with() to integrate with FastAPI
# This should be called when running the app, not at import time

