from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from app.config import settings
from app.api.actions import router as actions_router

app = FastAPI(
    title=settings.app_name,
    description="AI Agent Safety and Control Middleware",
    version=settings.version
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(actions_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "subtitle": settings.app_subtitle,
        "version": settings.version,
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)

