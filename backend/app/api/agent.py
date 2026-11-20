from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field

from app.agent.agent_engine import AgentEngine, AgentSession, TaskState

router = APIRouter(prefix="/api/agent", tags=["Agent Execution Engine"])

engine = AgentEngine()

class CreateSessionRequest(BaseModel):
    user_goal: str = Field(..., description="Prompt or goal for the agent")
    auto_run: bool = Field(default=True, description="Whether to execute until completed or paused")

class ApprovalRequest(BaseModel):
    approved: bool = Field(..., description="True to approve execution, False to reject and stop")

@router.post("/sessions", response_model=AgentSession)
def create_session(req: CreateSessionRequest) -> AgentSession:
    """Create a new agent task session and optionally begin execution."""
    session = engine.create_session(user_goal=req.user_goal)
    if req.auto_run:
        session = engine.run_until_complete_or_paused(session.session_id)
    return session

@router.get("/sessions", response_model=List[AgentSession])
def list_sessions() -> List[AgentSession]:
    """List all agent task sessions."""
    return engine.list_sessions()

@router.get("/sessions/{session_id}", response_model=AgentSession)
def get_session(session_id: str) -> AgentSession:
    """Retrieve details, execution traces, and gating status for a session."""
    session = engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return session

@router.post("/sessions/{session_id}/step", response_model=AgentSession)
def step_session(session_id: str) -> AgentSession:
    """Trigger a single plan -> intercept -> execute cycle."""
    session = engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return engine.step(session_id)

@router.post("/sessions/{session_id}/run", response_model=AgentSession)
def run_session(session_id: str) -> AgentSession:
    """Execute loop until completion or paused for human approval."""
    session = engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return engine.run_until_complete_or_paused(session_id)

@router.post("/sessions/{session_id}/approve", response_model=AgentSession)
def approve_session_step(session_id: str, req: ApprovalRequest) -> AgentSession:
    """Submit human approval decision for a paused step."""
    session = engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    try:
        return engine.resume_approval(session_id, approved=req.approved)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

