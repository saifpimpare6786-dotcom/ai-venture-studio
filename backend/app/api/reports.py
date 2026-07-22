from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from app.core.security import get_current_user
from app.database.supabase import get_supabase_client
from services.export_generator import generate_docx, generate_pptx, generate_pdf
from typing import List, Dict, Any

router = APIRouter(prefix="/reports", tags=["reports"])

def run_pipeline_background(project_id: str, project_record: Dict[str, Any]):
    """Orchestrates the LangGraph execution in the background to prevent HTTP timeouts."""
    try:
        from app.pipeline.graph import execute_pipeline
        from app.pipeline.specialized_agents import retrieve_context
        
        # Manually create profile bypass check to ensure logs references won't fail key constraints
        supabase = get_supabase_client()
        
        # Log Pipeline start
        supabase.table("agent_logs").insert({
            "project_id": project_id,
            "agent_name": "Pipeline Orchestrator",
            "status": "started",
            "input_data": {"message": "Boardroom pipeline initiated."},
            "output_data": {}
        }).execute()
        
        # Construct initial pipeline state
        # Map fields to match Planning and specialized nodes
        initial_state = {
            "project_id": project_id,
            "business_idea_input": (
                f"Business Name: {project_record['name']}\n"
                f"Industry: {project_record['industry']}\n"
                f"Core Idea: {project_record['idea_input']}\n"
                f"Budget: {project_record.get('budget', '')}\n"
                f"Location/Country: {project_record.get('target_customers', '')}"
            ),
            "rag_context": retrieve_context(project_id, project_record['idea_input'], top_k=5),
            "plan": "",
            "directives": "",
            "research_results": "",
            "specialized_outputs": {},
            # Failure-tracking fields (required by pipeline gate nodes)
            "failed_agents": [],
            "pipeline_aborted": False,
            "abort_reason": "",
            "council_feedback": [],
            "reviewer_notes": "",
            "critic_notes": "",
            "rules_validation_result": {},
            "scores": {},
            "final_report": "",
            "force_refresh": False
        }
        
        execute_pipeline(initial_state)
        print(f"Background pipeline execution succeeded for project: {project_id}")
    except Exception as e:
        print(f"Background pipeline failed for project {project_id}: {str(e)}")
        try:
            supabase.table("agent_logs").insert({
                "project_id": project_id,
                "agent_name": "Pipeline Orchestrator",
                "status": "failed",
                "input_data": {},
                "output_data": {"error": str(e)}
            }).execute()
        except Exception:
            pass

@router.get("/project/{project_id}")
def get_project_reports(project_id: str, current_user = Depends(get_current_user)):
    """Retrieves all generated reports and score rubrics for a specific project."""
    supabase = get_supabase_client()
    
    # Verify project ownership
    project = supabase.table("projects").select("user_id").eq("id", project_id).execute()
    if not project.data or project.data[0]["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found or user lacks permission")
        
    try:
        response = supabase.table("reports").select("*").eq("project_id", project_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/project/{project_id}/generate", status_code=status.HTTP_202_ACCEPTED)
def trigger_generation(
    project_id: str, 
    background_tasks: BackgroundTasks, 
    sync: bool = False,
    current_user = Depends(get_current_user)
):
    """Triggers the full multi-agent boardroom analysis pipeline (Background or Synchronous)."""
    supabase = get_supabase_client()
    
    # Verify project ownership
    project = supabase.table("projects").select("*").eq("id", project_id).execute()
    if not project.data or project.data[0]["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found or user lacks permission")
        
    project_record = project.data[0]
    
    if sync:
        # Run synchronously (primarily for unit/integration testing)
        run_pipeline_background(project_id, project_record)
        return {"status": "success", "message": "Pipeline ran synchronously."}
    else:
        # Run asynchronously in background tasks
        background_tasks.add_task(run_pipeline_background, project_id, project_record)
        return {"status": "processing", "message": "Venture analysis and report generation triggered."}

@router.get("/project/{project_id}/logs")
def get_project_logs(project_id: str, current_user = Depends(get_current_user)):
    """Retrieves execution logs sorted chronologically for boardroom livestream streaming."""
    supabase = get_supabase_client()
    
    # Verify ownership
    project = supabase.table("projects").select("user_id").eq("id", project_id).execute()
    if not project.data or project.data[0]["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found or user lacks permission")
        
    try:
        response = supabase.table("agent_logs").select("*").eq("project_id", project_id).order("created_at", desc=False).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}/download/{format}")
def download_report(report_id: str, format: str, current_user = Depends(get_current_user)):
    """Streams a generated report in Word (.docx), PowerPoint (.pptx), or PDF (.pdf) format."""
    supabase = get_supabase_client()
    
    # Fetch report
    report_res = supabase.table("reports").select("*").eq("id", report_id).execute()
    if not report_res.data:
        raise HTTPException(status_code=404, detail="Report record not found")
        
    report = report_res.data[0]
    project_id = report["project_id"]
    
    # Verify ownership of parent project
    project_res = supabase.table("projects").select("user_id, name").eq("id", project_id).execute()
    if not project_res.data or project_res.data[0]["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="Report not found or access unauthorized")
        
    project_name = project_res.data[0]["name"]
    report_type  = report["report_type"]
    content      = report["content"]
    
    # Load the human-readable section labels from the report registry
    # (section_labels maps field_key -> heading string for DOCX/PPTX/PDF exports)
    try:
        from app.pipeline.report_generator import _build_registry
        _dummy_context = {k: "" for k in [
            "idea", "strategy", "finance", "marketing", "risk",
            "council_str", "reviewer", "critic", "rules_json",
            "scores_json", "overall_score"
        ]}
        _dummy_context["overall_score"] = 0.0
        registry = _build_registry(_dummy_context)
        section_labels = registry.get(report_type, {}).get("export_mapping", {})
    except Exception:
        section_labels = {}
    
    clean_filename = f"{project_name.replace(' ', '_')}_{report_type.replace(' ', '_')}"
    
    if format.lower() == "docx":
        file_stream = generate_docx(report_type, content, project_name, section_labels)
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={clean_filename}.docx"}
        )
    elif format.lower() == "pptx":
        file_stream = generate_pptx(report_type, content, project_name, section_labels)
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f"attachment; filename={clean_filename}.pptx"}
        )
    elif format.lower() == "pdf":
        file_stream = generate_pdf(report_type, content, project_name, section_labels)
        return StreamingResponse(
            file_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={clean_filename}.pdf"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported download format. Options: docx, pptx, pdf")
