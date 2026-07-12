from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import projects, documents

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for AI Venture Studio",
    version="1.0.0"
)

# CORS configuration to allow local development and Vercel hosting origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific domains in a production configuration
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(projects.router, prefix="/api")
app.include_router(documents.router, prefix="/api")

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
