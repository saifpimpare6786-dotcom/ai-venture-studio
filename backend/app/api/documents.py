import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from app.core.security import get_current_user
from app.database.supabase import get_supabase_client
from app.schemas.project import DocumentResponse
from services.document_parser import extract_text, chunk_text
from services.rag_retriever import ingest_chunks
from typing import List

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: str = Form(..., description="The associated project UUID"),
    category: str = Form(..., description="The upload type (e.g. Pitch Deck, Competitor Analysis)"),
    file: UploadFile = File(..., description="The document file stream"),
    current_user = Depends(get_current_user)
):
    """
    Uploads a document to secure storage, extracts its text using file-type specific parsers,
    generates chunks, and embeds them into ChromaDB.
    """
    supabase = get_supabase_client()
    
    # Verify project ownership
    project_check = supabase.table("projects").select("id").eq("id", project_id).eq("user_id", current_user.id).execute()
    if not project_check.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Project not found or user is not authorized"
        )
        
    doc_id = str(uuid.uuid4())
    filename = file.filename
    temp_dir = "./temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{doc_id}_{filename}")
    
    # 1. Write the upload file stream locally for parsing
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to write file stream locally: {str(e)}"
        )
        
    size_bytes = os.path.getsize(temp_path)
    storage_path = f"documents/{project_id}/{doc_id}_{filename}"
    
    # 2. Upload raw file to Supabase Storage (failover safe)
    try:
        with open(temp_path, "rb") as f:
            supabase.storage.from_("documents").upload(storage_path, f)
    except Exception as storage_err:
        # Log error, but proceed since local chunking + DB storage is core to the application
        print(f"Supabase Storage upload warning (continuing processing): {str(storage_err)}")
        
    # 3. Create document record in database
    doc_record = {
        "id": doc_id,
        "project_id": project_id,
        "filename": filename,
        "category": category,
        "storage_path": storage_path,
        "size_bytes": size_bytes,
        "status": "Processing"
    }
    
    try:
        db_response = supabase.table("documents").insert(doc_record).execute()
        if not db_response.data:
            raise Exception("No data returned from DB insert")
    except Exception as db_err:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to insert document record: {str(db_err)}"
        )
        
    # 4. Parse text, run semantic splitter, and load vectors
    try:
        # Read text depending on file format extension
        text = extract_text(temp_path, filename)
        
        # Split into semantic boundaries
        chunks = chunk_text(text)
        
        # Load local embedding model and commit vectors to project collection in ChromaDB
        ingest_chunks(
            project_id=project_id, 
            document_id=doc_id, 
            filename=filename, 
            category=category, 
            chunks=chunks
        )
        
        # Success status update
        supabase.table("documents").update({"status": "Completed"}).eq("id", doc_id).execute()
        
    except Exception as process_err:
        err_msg = str(process_err)
        print(f"Document parsing error for {filename}: {err_msg}")
        # Register fail state in db
        supabase.table("documents").update({
            "status": "Failed", 
            "error_message": err_msg
        }).eq("id", doc_id).execute()
        
        # Record fail log in agent history logs
        try:
            supabase.table("agent_logs").insert({
                "project_id": project_id,
                "agent_name": "Document Processor",
                "status": "failed",
                "input_data": {"filename": filename, "category": category},
                "output_data": {"error": err_msg}
            }).execute()
        except Exception:
            pass
    finally:
        # Cleanup temporary files
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    # Fetch final updated database record to return
    final_record = supabase.table("documents").select("*").eq("id", doc_id).execute()
    return final_record.data[0]

@router.get("/project/{project_id}", response_model=List[DocumentResponse])
def list_documents(project_id: str, current_user = Depends(get_current_user)):
    """Retrieves all documents associated with a project."""
    supabase = get_supabase_client()
    try:
        # Confirm user owns the project
        project_check = supabase.table("projects").select("id").eq("id", project_id).eq("user_id", current_user.id).execute()
        if not project_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Project not found or user is not authorized"
            )
            
        response = supabase.table("documents").select("*").eq("project_id", project_id).execute()
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, current_user = Depends(get_current_user)):
    """Removes a document from the database, storage, and Chroma vector index."""
    supabase = get_supabase_client()
    try:
        # Validate project relationship and user ownership
        doc_resp = supabase.table("documents").select("*, projects(user_id)").eq("id", document_id).execute()
        if not doc_resp.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
        doc = doc_resp.data[0]
        # In newer Supabase-py library executions, join results are returned nested or flattened
        # Handle cases where project values are in projects list/dict
        project = doc.get("projects")
        if isinstance(project, list):
            project = project[0] if project else None
            
        if not project or project.get("user_id") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="User lacks permission to delete this file"
            )
            
        # 1. Remove from storage bucket
        try:
            supabase.storage.from_("documents").remove([doc["storage_path"]])
        except Exception as e:
            print(f"Failed to delete file from storage bucket: {str(e)}")
            
        # 2. Remove from ChromaDB collection
        try:
            from services.rag_retriever import get_chroma_client
            client = get_chroma_client()
            col_name = f"project_{doc['project_id'].replace('-', '_')}"
            col = client.get_collection(name=col_name)
            col.delete(where={"document_id": document_id})
        except Exception as chroma_err:
            print(f"Failed to clean vectors from ChromaDB: {str(chroma_err)}")
            
        # 3. Delete DB record
        supabase.table("documents").delete().eq("id", document_id).execute()
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
