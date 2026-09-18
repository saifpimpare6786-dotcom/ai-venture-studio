from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Dict, Any
from services.document_parser import document_parser
from services.rag_retriever import rag_retriever
from app.database.db import db
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    # Verify project ownership
    project = await db.get_project(project_id)
    if project and project.get("user_id") and project["user_id"] != user_id and project["user_id"] != "default_founder":
        raise HTTPException(status_code=403, detail="Access denied.")

    try:
        filename = file.filename or "uploaded_file"
        content = await file.read()
        parsed = document_parser.parse_document(content, filename)
        
        # Index in ChromaDB
        rag_retriever.index_document(project_id, parsed)

        return {
            "status": "success",
            "filename": filename,
            "file_type": parsed["file_type"],
            "sha256": parsed["sha256"],
            "size_bytes": parsed["size_bytes"],
            "preview": parsed["text"][:300] + "..." if len(parsed["text"]) > 300 else parsed["text"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
