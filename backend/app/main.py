from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from app.config import settings
from app.database import init_db
from app.api.actions import router as actions_router
from app.api.evaluations import router as evaluations_router
from app.api.agent import router as agent_router
from app.api.routes import router as core_routes_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables on startup
    init_db()
    yield

app = FastAPI(
    title=settings.app_name,
    description="AI Agent Safety and Control Middleware",
    version=settings.version,
    lifespan=lifespan,
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core persistent routes & SSE
app.include_router(core_routes_router)

# Action execution & evaluation routes
app.include_router(actions_router)
app.include_router(evaluations_router)
app.include_router(agent_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)

