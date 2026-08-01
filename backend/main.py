from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import projects, documents, reports

from services.llm import print_nim_model_dispatch_table

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for AI Venture Studio",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    """Prints the NIM model dispatch routing table on application startup."""
    print_nim_model_dispatch_table()

# CORS configuration to allow local development (http://localhost:5173) and production deployment origins
allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(projects.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify server status.
    This also serves as a warm-up ping for Render free-tier spin-up.
    """
    return {"status": "healthy", "project": settings.PROJECT_NAME}

if __name__ == "__main__":
    import uvicorn
    # Start the server if executing this script directly
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
