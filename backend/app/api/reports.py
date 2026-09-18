import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks, Response, Depends
from typing import List, Dict, Any
from app.database.db import db
from app.pipeline.graph import pipeline_graph
from app.pipeline.report_generator import _generate_single_report, REPORT_REGISTRY
from services.export_generator import export_generator
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.post("/generate/{project_id}")
async def trigger_report_generation(
    project_id: str, 
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # Verify ownership
    if project.get("user_id") and project["user_id"] != user_id and project["user_id"] != "default_founder":
        raise HTTPException(status_code=403, detail="Access denied.")

    # Run in background task so UI can stream live
    background_tasks.add_task(pipeline_graph.run, project_id, project)
    return {"status": "started", "project_id": project_id, "message": "Multi-agent deliberation started."}

@router.post("/regenerate-single/{project_id}/{report_type}")
async def regenerate_single_report(
    project_id: str,
    report_type: str,
    user_id: str = Depends(get_current_user)
):
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.get("user_id") and project["user_id"] != user_id and project["user_id"] != "default_founder":
        raise HTTPException(status_code=403, detail="Access denied.")

    registry_entry = next((r for r in REPORT_REGISTRY if r[0] == report_type), None)
    if not registry_entry:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")

    r_type, title, schema_cls = registry_entry
    state = {
        "project_id": project_id,
        "project_data": project,
        "scores": {
            "overall_score": project.get("overall_score", 82.0),
            "viability_score": project.get("viability_score", 85.0),
            "market_fit_score": project.get("market_fit_score", 80.0),
            "financial_score": project.get("financial_score", 80.0)
        }
    }
    sem = asyncio.Semaphore(1)
    res = await _generate_single_report(sem, r_type, title, schema_cls, state, force_fresh=True)
    return res

@router.get("/{project_id}")
async def get_project_reports(project_id: str, user_id: str = Depends(get_current_user)):
    project = await db.get_project(project_id)
    if project and project.get("user_id") and project["user_id"] != user_id and project["user_id"] != "default_founder":
        raise HTTPException(status_code=403, detail="Access denied.")
    
    reports = await db.get_reports(project_id)
    return {
        "project": project,
        "reports": reports
    }

@router.get("/export/{project_id}/{format}")
async def export_reports(project_id: str, format: str, user_id: str = Depends(get_current_user)):
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.get("user_id") and project["user_id"] != user_id and project["user_id"] != "default_founder":
        raise HTTPException(status_code=403, detail="Access denied.")

    reports = await db.get_reports(project_id)
    if not reports:
        raise HTTPException(status_code=400, detail="No reports available for export yet.")

    raw_name = project.get("name", "Venture")
    safe_name = "".join(c for c in raw_name if c.isalnum() or c in (' ', '_', '-')).strip() or "Venture"
    fmt = format.lower()

    if fmt == "docx":
        data = export_generator.generate_docx(raw_name, reports)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_Business_Plan.docx"'}
        )
    elif fmt == "pptx":
        data = export_generator.generate_pptx(raw_name, reports)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_Pitch_Deck.pptx"'}
        )
    elif fmt == "pdf":
        data = export_generator.generate_pdf(raw_name, reports)
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_Due_Diligence.pdf"'}
        )
    elif fmt in ("xlsx", "excel"):
        from services.simulator_engine import simulator_engine
        sim_data = simulator_engine.calculate_scenario()
        data = export_generator.generate_excel_simulation(raw_name, sim_data, project_meta=project, reports=reports)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_Financial_Model.xlsx"'}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Supported: docx, pptx, pdf, xlsx")
