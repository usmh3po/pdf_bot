"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.config import get_settings

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


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint providing health check."""
    return {"message": "PDF Bot API is running", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint returning service status."""
    return {"status": "healthy", "service": settings.app_name}


# Include API routers
app.include_router(chat_router)

