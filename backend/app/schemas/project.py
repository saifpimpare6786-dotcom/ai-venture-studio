from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(..., description="The name of the startup project")
    industry: str = Field(..., description="The industry category of the startup")
    idea_input: str = Field(..., description="The initial raw business idea description")
    description: Optional[str] = Field(None, description="Detailed description of the business model")
    stage: Optional[str] = Field("Ideation", description="Development stage (e.g. Ideation, MVP, Scale)")
    target_customers: Optional[str] = Field(None, description="Target customer demographics / segments")
    budget: Optional[float] = Field(None, description="Initial investment budget")
    revenue_model: Optional[str] = Field(None, description="Revenue model description")
    timeline: Optional[str] = Field(None, description="Expected operational timeline")
    team_size: Optional[int] = Field(1, description="Current size of the founding team")
    goals: Optional[List[str]] = Field(default_factory=list, description="Targeted business milestones")
    preferred_funding: Optional[str] = Field(None, description="Preferred source/type of funding")

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    category: str
    storage_path: str
    size_bytes: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
