import json
import asyncio
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from app.database.db import db
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/pipeline", tags=["streaming"])

@router.get("/stream/{project_id}")
async def stream_pipeline_progress(
    project_id: str, 
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """
    Server-Sent Events (SSE) real-time streaming endpoint for agent discussions.
    Includes keep-alive heartbeats and extended timeout to prevent disconnection.
    
    Auth Note: In dev mode, user_id falls back to 'default_founder'.
    For production with Supabase Auth, the frontend should pass ?token=<jwt> 
    since EventSource cannot set Authorization headers.
    """
    # Verify project ownership
    project = await db.get_project(project_id)
    if project and project.get("user_id") and project["user_id"] != user_id and project["user_id"] != "default_founder":
        return StreamingResponse(
            iter([f"data: {json.dumps({'event': 'error', 'message': 'Access denied.'})}\n\n"]),
            media_type="text/event-stream"
        )

    async def event_generator():
        last_count = 0
        max_checks = 600 # 10 minutes max (prevents early disconnection during deep inference)
        heartbeat_interval = 2 # send keepalive every 2 seconds
        heartbeat_counter = 0

        # Push initial connection event
        yield f"data: {json.dumps({'event': 'connected', 'project_id': project_id})}\n\n"
        
        while max_checks > 0:
            if await request.is_disconnected():
                break

            discussions = await db.get_agent_discussions(project_id)
            project_data = await db.get_project(project_id)
            status = project_data.get("status", "draft") if project_data else "draft"

            if len(discussions) > last_count:
                new_items = discussions[last_count:]
                for item in new_items:
                    payload = {
                        "event": "agent_message",
                        "agent": item.get("agent_name"),
                        "role": item.get("agent_role"),
                        "message": item.get("message_content"),
                        "step": item.get("step_index"),
                        "status": status
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                last_count = len(discussions)
                heartbeat_counter = 0
            else:
                heartbeat_counter += 1
                if heartbeat_counter >= heartbeat_interval:
                    # Emit SSE keep-alive heartbeat to prevent proxy/browser timeout
                    yield f"data: {json.dumps({'event': 'heartbeat', 'status': status, 'message_count': len(discussions)})}\n\n"
                    heartbeat_counter = 0

            if status in ("completed", "failed"):
                yield f"data: {json.dumps({'event': 'pipeline_end', 'status': status})}\n\n"
                break

            await asyncio.sleep(1.0)
            max_checks -= 1

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
