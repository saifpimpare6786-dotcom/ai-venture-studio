import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.database.db import db
from app.api.projects import router as projects_router
from app.api.documents import router as documents_router
from app.api.reports import router as reports_router
from app.api.simulator import router as simulator_router
from app.api.stream import router as stream_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite DB tables if not using Supabase
    await db.init_sqlite()
    print(f"[AI Venture Studio] Backend initialized. LLM Provider: {settings.DEFAULT_LLM_PROVIDER} ({settings.OLLAMA_MODEL})")
    yield
    # Shutdown
    print("[AI Venture Studio] Backend shutdown cleanly.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(reports_router)
app.include_router(simulator_router)
app.include_router(stream_router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "llm_provider": settings.DEFAULT_LLM_PROVIDER,
        "ollama_model": settings.OLLAMA_MODEL,
        "prefer_local": settings.PREFER_LOCAL_OLLAMA
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG)
