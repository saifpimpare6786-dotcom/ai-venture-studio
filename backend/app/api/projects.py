from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user
from app.database.supabase import get_supabase_client
from app.schemas.project import ProjectCreate, ProjectResponse
from typing import List

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, current_user = Depends(get_current_user)):
    """Creates a new startup project linked to the authenticated user."""
    supabase = get_supabase_client()
    project_data = project.model_dump()
    project_data["user_id"] = current_user.id
    
    try:
        response = supabase.table("projects").insert(project_data).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create project record in database")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ProjectResponse])
def list_projects(current_user = Depends(get_current_user)):
    """Retrieves all projects owned by the authenticated user."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("projects").select("*").eq("user_id", current_user.id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, current_user = Depends(get_current_user)):
    """Gets details for a single project owned by the authenticated user."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("projects").select("*").eq("id", project_id).eq("user_id", current_user.id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found or user lacks permission")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, project: ProjectCreate, current_user = Depends(get_current_user)):
    """Updates project information for a project owned by the authenticated user."""
    supabase = get_supabase_client()
    try:
        # Validate ownership first
        check_response = supabase.table("projects").select("id").eq("id", project_id).eq("user_id", current_user.id).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Project not found or user lacks permission")
            
        response = supabase.table("projects").update(project.model_dump()).eq("id", project_id).execute()
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, current_user = Depends(get_current_user)):
    """Deletes a user project and all nested relational database records."""
    supabase = get_supabase_client()
    try:
        # Validate ownership
        check_response = supabase.table("projects").select("id").eq("id", project_id).eq("user_id", current_user.id).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Project not found or user lacks permission")
            
        supabase.table("projects").delete().eq("id", project_id).execute()
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
