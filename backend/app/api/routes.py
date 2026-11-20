import json
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TaskModel, ActionModel
from app.schemas import (
    TaskCreateRequest,
    TaskSummaryResponse,
    TaskDetailResponse,
    ActionDetailResponse,
    ActionApprovalRequest,
    SnapshotItemResponse,
    SnapshotRestoreResponse,
    SystemStatsResponse,
)
from app.schemas.actions import ActionRequest, ActionType, ActionResult, RunTestsParams
from app.services.audit_service import audit_service
from app.services.event_service import event_service
from app.services.snapshot import SnapshotManager
from app.agent.agent_engine import AgentEngine, TaskState
from app.config import settings

router = APIRouter(prefix="/api", tags=["TRIPWIRE Core API"])

# Shared engine instance for API executions
agent_engine = AgentEngine()
snapshot_manager = SnapshotManager()

# -------------------------------------------------------------
# Health Probe
# -------------------------------------------------------------
@router.get("/health")
def health_check():
    """Verify backend health, service name, version, and timestamp."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "subtitle": settings.app_subtitle,
        "version": settings.version,
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# -------------------------------------------------------------
# Tasks Endpoints
# -------------------------------------------------------------
@router.post("/tasks", response_model=TaskDetailResponse, status_code=status.HTTP_201_CREATED)
def create_task(req: TaskCreateRequest, db: Session = Depends(get_db)):
    """Create a new agent task and optionally execute until completion or pause."""
    session = agent_engine.create_session(user_goal=req.user_goal)
    if req.auto_run:
        session = agent_engine.run_until_complete_or_paused(session.session_id)

    task = audit_service.get_task(db, session.session_id)
    if not task:
        raise HTTPException(status_code=500, detail="Failed to retrieve created task from database")

    actions_resp = [audit_service.to_action_response(a) for a in task.actions]
    return TaskDetailResponse(
        id=task.id,
        user_goal=task.user_goal,
        state=task.state,
        summary=task.summary,
        actions=actions_resp,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )

@router.get("/tasks", response_model=List[TaskSummaryResponse])
def list_tasks(limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db)):
    """List all persisted tasks with status and action counts."""
    tasks = audit_service.list_tasks(db, limit=limit)
    return [
        TaskSummaryResponse(
            id=t.id,
            user_goal=t.user_goal,
            state=t.state,
            summary=t.summary,
            action_count=len(t.actions),
            created_at=t.created_at.isoformat(),
            updated_at=t.updated_at.isoformat(),
        )
        for t in tasks
    ]

@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get full details and execution step trace for a specific task."""
    task = audit_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    actions_resp = [audit_service.to_action_response(a) for a in task.actions]
    return TaskDetailResponse(
        id=task.id,
        user_goal=task.user_goal,
        state=task.state,
        summary=task.summary,
        actions=actions_resp,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )

@router.post("/tasks/{task_id}/stop", response_model=TaskDetailResponse)
def stop_task(task_id: str, db: Session = Depends(get_db)):
    """Stop an ongoing or paused task."""
    task = audit_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    session = agent_engine.get_session(task_id)
    if session:
        session.state = TaskState.STOPPED
        session.summary = "Task halted by operator command."
        session.pending_approval_step = None

    task = audit_service.update_task_state(db, task_id, "STOPPED", summary="Task halted by operator command.")
    event_service.publish("task_completed", {"task_id": task_id, "summary": "Task halted by operator"}, task_id=task_id)

    actions_resp = [audit_service.to_action_response(a) for a in task.actions]
    return TaskDetailResponse(
        id=task.id,
        user_goal=task.user_goal,
        state=task.state,
        summary=task.summary,
        actions=actions_resp,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )

# -------------------------------------------------------------
# Actions Endpoints
# -------------------------------------------------------------
@router.get("/actions/files", response_model=ActionResult)
def list_workspace_files(path: Optional[str] = Query(default="")):
    """List files in the protected demo workspace."""
    request = ActionRequest(action=ActionType.LIST_FILES, params={"path": path or ""})
    return agent_engine.executor.execute(request)

@router.post("/actions/execute", response_model=ActionResult)
def execute_controlled_action(request: ActionRequest):
    """Directly execute a controlled action within workspace boundaries."""
    return agent_engine.executor.execute(request)

@router.post("/actions/run-tests", response_model=ActionResult)
def run_controlled_tests(target: Optional[str] = Query(default=None)):
    """Execute permitted test runner without shell injection."""
    request = ActionRequest(action=ActionType.RUN_TESTS, params={"target": target} if target else {})
    return agent_engine.executor.execute(request)

@router.get("/actions", response_model=List[ActionDetailResponse])
def list_actions(
    status: Optional[str] = Query(default=None, description="Filter by status (PENDING, PAUSED, EXECUTED, REJECTED)"),
    task_id: Optional[str] = Query(default=None, description="Filter by task ID"),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List audited actions with complete evaluation and execution details."""
    actions = audit_service.list_actions(db, status=status, task_id=task_id, limit=limit)
    return [audit_service.to_action_response(a) for a in actions]

@router.get("/actions/{action_id}", response_model=ActionDetailResponse)
def get_action(action_id: str, db: Session = Depends(get_db)):
    """Retrieve full details for a single audited action."""
    action = audit_service.get_action(db, action_id)
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")
    return audit_service.to_action_response(action)

@router.post("/actions/{action_id}/approve", response_model=ActionDetailResponse)
def approve_action(action_id: str, db: Session = Depends(get_db)):
    """Human-in-the-loop: Authorize a PAUSED action to execute through the controlled executor."""
    action = audit_service.get_action(db, action_id)
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")

    session = agent_engine.get_session(action.task_id)
    if not session or session.state != TaskState.WAITING_APPROVAL:
        raise HTTPException(status_code=400, detail=f"Action '{action_id}' is not currently awaiting approval.")

    # Record approval in DB
    audit_service.record_human_approval(db, action_id, approved=True)

    # Resume agent execution
    agent_engine.resume_approval(session.session_id, approved=True)
    agent_engine.run_until_complete_or_paused(session.session_id)

    db.refresh(action)
    return audit_service.to_action_response(action)

@router.post("/actions/{action_id}/reject", response_model=ActionDetailResponse)
def reject_action(action_id: str, db: Session = Depends(get_db)):
    """Human-in-the-loop: Reject a PAUSED action and halt task execution."""
    action = audit_service.get_action(db, action_id)
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")

    session = agent_engine.get_session(action.task_id)
    if not session or session.state != TaskState.WAITING_APPROVAL:
        raise HTTPException(status_code=400, detail=f"Action '{action_id}' is not currently awaiting approval.")

    # Record rejection in DB
    audit_service.record_human_approval(db, action_id, approved=False)

    # Resume agent rejection
    agent_engine.resume_approval(session.session_id, approved=False)

    db.refresh(action)
    return audit_service.to_action_response(action)

# -------------------------------------------------------------
# Snapshots Endpoints
# -------------------------------------------------------------
@router.get("/snapshots", response_model=List[SnapshotItemResponse])
def list_snapshots():
    """List point-in-time workspace rollback checkpoints."""
    snaps = snapshot_manager.list_snapshots()
    return [
        SnapshotItemResponse(
            snapshot_id=s["snapshot_id"],
            description="Automatic guarded checkpoint",
            timestamp=datetime.fromtimestamp(s["created_at"], tz=timezone.utc).isoformat(),
            file_count=s["file_count"],
            total_size_bytes=0,
        )
        for s in snaps
    ]

@router.post("/snapshots/{snapshot_id}/restore", response_model=SnapshotRestoreResponse)
def restore_snapshot(snapshot_id: str):
    """Roll back the workspace to a specified snapshot."""
    try:
        snapshot_manager.restore_snapshot(snapshot_id)
        return SnapshotRestoreResponse(
            success=True,
            snapshot_id=snapshot_id,
            message=f"Workspace successfully rolled back to snapshot '{snapshot_id}'.",
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Snapshot '{snapshot_id}' not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# -------------------------------------------------------------
# Dynamic Statistics Endpoint
# -------------------------------------------------------------
@router.get("/stats", response_model=SystemStatsResponse)
def get_system_stats(db: Session = Depends(get_db)):
    """Return live system statistics calculated dynamically from SQLite audit records."""
    return audit_service.get_stats(db)

# -------------------------------------------------------------
# Server-Sent Events (SSE) Live Feed
# -------------------------------------------------------------
@router.get("/events")
async def sse_events_stream():
    """Server-Sent Events endpoint streaming real-time agent lifecycle and evaluation updates."""
    return StreamingResponse(
        event_service.subscribe(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
