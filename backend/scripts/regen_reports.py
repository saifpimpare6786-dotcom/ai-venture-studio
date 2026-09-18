"""
Regenerate Reports Script — AI Venture Studio
Runs deterministic multi-agent report synthesis for a specific project.
"""

import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path for both runtime and IDE static analysis
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

import asyncio
import json
from typing import Optional
from app.database.db import db
from app.pipeline.state import AgentState
from app.pipeline.report_generator import report_generator_node

async def regenerate_project_reports(target_project_id: Optional[str] = None):
    # If no ID specified, fetch the latest active project
    if not target_project_id:
        projects = await db.list_projects()
        if not projects:
            print("No projects found in database.")
            return
        target_project_id = projects[0]["id"]

    project = await db.get_project(target_project_id)
    if not project:
        print(f"Project '{target_project_id}' not found.")
        return

    print(f"Regenerating 13 institutional deliverables for: '{project.get('name')}' (ID: {target_project_id}, Currency: {project.get('currency')})...")
    
    state: AgentState = {
        "project_id": target_project_id,
        "project_data": project,
        "finance_assessment": {},
        "strategy_assessment": {},
        "marketing_assessment": {},
        "risk_assessment": {},
        "critic_assessment": {},
        "scores": {
            "viability": 84,
            "overall_score": 84,
            "market_fit_score": 86,
            "financial_score": 82,
            "moat_score": 80
        },
        "reports": {},
        "discussion_logs": []
    }

    result = await report_generator_node(state)
    print(f"Successfully synthesized {len(result['reports'])} reports:")
    for r_type, report in result["reports"].items():
        content_size = len(json.dumps(report.get("content", {})))
        from_cache = report.get("from_cache", False)
        print(f"  • {r_type}: {content_size} bytes (Cached: {from_cache})")

if __name__ == "__main__":
    proj_id = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(regenerate_project_reports(proj_id))
