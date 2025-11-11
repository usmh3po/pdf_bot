"""PDF upload endpoint for adding documents to the knowledge base."""

import asyncio
import concurrent.futures
import os
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.agent.knowledge import get_knowledge, get_pdf_reader

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Directory to store uploaded PDFs temporarily
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)) -> JSONResponse:
    """Upload a PDF file and add it to the knowledge base."""
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )
    
    try:
        # Save uploaded file temporarily
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        
        # Write file to disk
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Get knowledge base and PDF reader
        knowledge = get_knowledge()
        pdf_reader = get_pdf_reader()
        
        # Add PDF to knowledge base
        # This will process, chunk, embed, and store the PDF content
        # Run in executor to avoid event loop conflicts if add_content uses asyncio.run()
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                lambda: knowledge.add_content(
                    path=str(file_path),
                    reader=pdf_reader,
                    metadata={
                        "filename": file.filename,
                        "file_id": file_id,
                        "type": "pdf",
                    },
                ),
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "PDF uploaded and processed successfully",
                "file_id": file_id,
                "filename": file.filename,
                "status": "processing",  # Agno processes asynchronously
            },
        )
        
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload PDF: {str(e)}",
        )


@router.get("/status/{file_id}")
async def get_upload_status(file_id: str) -> JSONResponse:
    """Get the processing status of an uploaded PDF."""
    try:
        knowledge = get_knowledge()
        
        # Get all content and find the one with matching file_id
        # Run in executor to avoid event loop conflicts
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            content_list, _ = await loop.run_in_executor(
                executor,
                lambda: knowledge.get_content(),
            )
        
        for content in content_list:
            if content.metadata and content.metadata.get("file_id") == file_id:
                # Get status in executor as well
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    status_info, message = await loop.run_in_executor(
                        executor,
                        lambda: knowledge.get_content_status(content.id),
                    )
                
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "file_id": file_id,
                        "status": status_info.value if hasattr(status_info, "value") else str(status_info),
                        "message": message,
                    },
                )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}",
        )


@router.get("/list")
async def list_uploads() -> JSONResponse:
    """List all uploaded PDFs in the knowledge base."""
    try:
        knowledge = get_knowledge()
        
        # Run in executor to avoid event loop conflicts
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            content_list, total_count = await loop.run_in_executor(
                executor,
                lambda: knowledge.get_content(),
            )
        
        uploads = []
        for content in content_list:
            if content.metadata and content.metadata.get("type") == "pdf":
                # Get status in executor as well
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    status_info, message = await loop.run_in_executor(
                        executor,
                        lambda: knowledge.get_content_status(content.id),
                    )
                
                uploads.append({
                    "file_id": content.metadata.get("file_id"),
                    "filename": content.metadata.get("filename"),
                    "status": status_info.value if hasattr(status_info, "value") else str(status_info),
                    "message": message,
                })
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "uploads": uploads,
                "total": len(uploads),
            },
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list uploads: {str(e)}",
        )

