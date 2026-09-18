from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

try:
    from app.schemas.project import ProjectCreate, ProjectResponse
    from app.database.db import db
    from app.core.auth import get_current_user
except ImportError:
    from ..schemas.project import ProjectCreate, ProjectResponse
    from ..database.db import db
    from ..core.auth import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.post("", response_model=Dict[str, Any])
async def create_project(data: ProjectCreate, user_id: str = Depends(get_current_user)):
    project_data = data.model_dump()
    project_data["user_id"] = user_id
    created = await db.create_project(project_data)
    return created

@router.get("", response_model=List[Dict[str, Any]])
async def list_projects(user_id: str = Depends(get_current_user)):
    return await db.list_projects(user_id=user_id)

@router.get("/{project_id}", response_model=Dict[str, Any])
async def get_project(project_id: str, user_id: str = Depends(get_current_user)):
    p = await db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    # Verify ownership
    if p.get("user_id") and p["user_id"] != user_id and p["user_id"] != "default_founder":
        raise HTTPException(status_code=403, detail="Access denied.")
    return p

@router.delete("/{project_id}")
async def delete_project(project_id: str, user_id: str = Depends(get_current_user)):
    p = await db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    # Verify ownership
    if p.get("user_id") and p["user_id"] != user_id and p["user_id"] != "default_founder":
        raise HTTPException(status_code=403, detail="Access denied.")
    await db.delete_project(project_id)
    return {"status": "success", "message": f"Project {project_id} deleted successfully."}
