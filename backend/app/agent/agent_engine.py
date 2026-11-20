import uuid
import time
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.agent.planner import AgentPlanner, DeterministicPlanner, ProposedAction, LLMPlanner
from app.tripwire.interceptor import TripwireInterceptor, InterceptionRequest, InterceptionResult
from app.tripwire.decision_engine import Decision
from app.services.executor import WorkspaceExecutor
from app.services.snapshot import SnapshotManager
from app.schemas.actions import ActionRequest, ActionType, ActionResult
from app.config import settings
from app.database import SessionLocal
from app.services.audit_service import audit_service
from app.services.event_service import event_service

class TaskState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"

class ExecutionStep(BaseModel):
    step_number: int
    action_id: Optional[str] = None
    proposed_action: ProposedAction
    interception_result: InterceptionResult
    snapshot_id: Optional[str] = None
    execution_result: Optional[ActionResult] = None
    human_approval: Optional[bool] = None
    timestamp: str

class AgentSession(BaseModel):
    session_id: str
    user_goal: str
    state: TaskState
    current_step: int = 0
    steps: List[ExecutionStep] = Field(default_factory=list)
    pending_approval_step: Optional[ExecutionStep] = None
    created_at: str
    updated_at: str
    summary: Optional[str] = None

class AgentEngine:
    """Orchestrates the autonomous agent lifecycle under Tripwire safety gates with SQLite & SSE."""

    def __init__(
        self,
        workspace_dir: Optional[str] = None,
        planner: Optional[AgentPlanner] = None,
    ):
        self.workspace_dir = workspace_dir or settings.workspace_dir
        self.planner = planner or (LLMPlanner() if settings.llm_judge_api_key else DeterministicPlanner())
        self.interceptor = TripwireInterceptor(workspace_dir=self.workspace_dir)
        self.executor = WorkspaceExecutor(workspace_dir=self.workspace_dir)
        self.snapshot_manager = SnapshotManager(workspace_dir=self.workspace_dir)
        self._sessions: Dict[str, AgentSession] = {}

    def create_session(self, user_goal: str) -> AgentSession:
        """Initialize a new agent task session."""
        now_iso = datetime.now(timezone.utc).isoformat()
        session_id = f"task_{uuid.uuid4().hex[:10]}"
        session = AgentSession(
            session_id=session_id,
            user_goal=user_goal,
            state=TaskState.PENDING,
            current_step=0,
            steps=[],
            pending_approval_step=None,
            created_at=now_iso,
            updated_at=now_iso,
            summary="Task created and pending execution.",
        )
        self._sessions[session_id] = session

        # Persist to SQLite
        try:
            with SessionLocal() as db:
                audit_service.create_task(db, user_goal=user_goal, task_id=session_id)
        except Exception:
            pass

        # Publish live event
        event_service.publish(
            "task_started",
            {"task_id": session_id, "user_goal": user_goal},
            task_id=session_id,
        )

        return session

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[AgentSession]:
        return list(self._sessions.values())

    def step(self, session_id: str) -> AgentSession:
        """Execute a single cycle of plan -> intercept -> guard -> execute."""
        session = self._sessions.get(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")

        if session.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.STOPPED):
            return session

        if session.state == TaskState.WAITING_APPROVAL:
            return session

        session.state = TaskState.RUNNING
        session.updated_at = datetime.now(timezone.utc).isoformat()

        # Update DB state
        try:
            with SessionLocal() as db:
                audit_service.update_task_state(db, session.session_id, "RUNNING")
        except Exception:
            pass

        # Build context from previous steps
        history_records = []
        for s in session.steps:
            history_records.append({
                "step": s.step_number,
                "action": s.proposed_action.action,
                "params": s.proposed_action.params,
                "decision": s.interception_result.decision.decision,
                "execution_result": s.execution_result.model_dump() if s.execution_result else None,
            })

        # 1. Ask planner for next proposed action
        proposed = self.planner.plan_next(
            user_goal=session.user_goal,
            history=history_records,
        )

        if not proposed or proposed.is_terminal:
            session.state = TaskState.COMPLETED
            session.summary = proposed.rationale if proposed else "Task completed successfully."
            session.updated_at = datetime.now(timezone.utc).isoformat()

            # Persist and emit
            try:
                with SessionLocal() as db:
                    audit_service.update_task_state(db, session.session_id, "COMPLETED", summary=session.summary)
            except Exception:
                pass
            event_service.publish(
                "task_completed",
                {"task_id": session.session_id, "summary": session.summary},
                task_id=session.session_id,
            )
            return session

        session.current_step += 1

        # Emit action_proposed
        event_service.publish(
            "action_proposed",
            {
                "task_id": session.session_id,
                "step_number": session.current_step,
                "action": proposed.action,
                "params": proposed.params,
                "rationale": proposed.rationale,
            },
            task_id=session.session_id,
        )

        # 2. Extract before_content if modifying a file
        before_content = None
        target_path = proposed.params.get("path")
        if proposed.action == "write_file" and target_path:
            try:
                read_res = self.executor.read_file(type("P", (), {"path": target_path})())
                before_content = read_res.get("content")
            except Exception:
                before_content = None

        # 3. Submit proposed action to Tripwire Interceptor
        interception_req = InterceptionRequest(
            action=proposed.action,
            params=proposed.params,
            user_goal=session.user_goal,
            action_description=proposed.rationale,
            expected_outcome=proposed.expected_outcome,
            claimed_outcome=proposed.claimed_outcome,
            before_content=before_content,
            after_content=proposed.params.get("content"),
            previous_actions=[h for h in history_records],
            workspace_dir=self.workspace_dir,
        )
        eval_result = self.interceptor.intercept(interception_req)
        decision = eval_result.decision.decision

        # Emit granular evaluation events
        event_service.publish(
            "evidence_checked",
            {
                "task_id": session.session_id,
                "evidence_score": eval_result.evidence.evidence_score,
                "verified": eval_result.evidence.verified,
                "explanation": eval_result.evidence.explanation,
            },
            task_id=session.session_id,
        )
        event_service.publish(
            "reason_checked",
            {
                "task_id": session.session_id,
                "reason_score": eval_result.reason.reason_score,
                "is_relevant": eval_result.reason.is_relevant,
                "explanation": eval_result.reason.explanation,
            },
            task_id=session.session_id,
        )
        event_service.publish(
            "risk_checked",
            {
                "task_id": session.session_id,
                "risk_score": eval_result.risk.risk_score,
                "risk_level": eval_result.risk.risk_level,
                "is_reversible": eval_result.risk.is_reversible,
            },
            task_id=session.session_id,
        )
        event_service.publish(
            "trust_calculated",
            {
                "task_id": session.session_id,
                "trust_score": eval_result.trust.trust_score,
                "weights": eval_result.trust.weights,
            },
            task_id=session.session_id,
        )
        event_service.publish(
            "decision_generated",
            {
                "task_id": session.session_id,
                "decision": decision.value,
                "reasons": eval_result.decision.reasons,
                "overrides": eval_result.decision.overrides_applied,
            },
            task_id=session.session_id,
        )

        # Record action proposal in SQLite
        action_db_id = None
        try:
            with SessionLocal() as db:
                action_rec = audit_service.record_action_proposal(
                    db=db,
                    task_id=session.session_id,
                    step_number=session.current_step,
                    action_name=proposed.action,
                    params=proposed.params,
                    rationale=proposed.rationale,
                    expected_outcome=proposed.expected_outcome,
                    claimed_outcome=proposed.claimed_outcome,
                    interception=eval_result,
                )
                action_db_id = action_rec.id
        except Exception:
            pass

        now_iso = datetime.now(timezone.utc).isoformat()

        # 4. Handle Gating Decisions
        if decision == Decision.PAUSE:
            step_record = ExecutionStep(
                step_number=session.current_step,
                action_id=action_db_id,
                proposed_action=proposed,
                interception_result=eval_result,
                snapshot_id=None,
                execution_result=None,
                human_approval=None,
                timestamp=now_iso,
            )
            session.steps.append(step_record)
            session.pending_approval_step = step_record
            session.state = TaskState.WAITING_APPROVAL
            session.summary = f"Action '{proposed.action}' paused by Tripwire for human approval."
            session.updated_at = now_iso

            # Update DB state and emit approval_requested
            try:
                with SessionLocal() as db:
                    audit_service.update_task_state(db, session.session_id, "WAITING_APPROVAL", summary=session.summary)
            except Exception:
                pass
            event_service.publish(
                "approval_requested",
                {
                    "task_id": session.session_id,
                    "action_id": action_db_id,
                    "action": proposed.action,
                    "reasons": eval_result.decision.reasons,
                    "overrides": eval_result.decision.overrides_applied,
                },
                task_id=session.session_id,
            )
            return session

        snapshot_id = None
        if decision == Decision.SNAPSHOT_AND_RUN:
            snap = self.snapshot_manager.create_snapshot(
                description=f"Snapshot before step {session.current_step}: {proposed.action}"
            )
            snapshot_id = snap.snapshot_id

        # 5. Controlled Execution via executor
        action_type = ActionType(proposed.action)
        action_req = ActionRequest(action=action_type, params=proposed.params)
        exec_result = self.executor.execute(action_req)

        step_record = ExecutionStep(
            step_number=session.current_step,
            action_id=action_db_id,
            proposed_action=proposed,
            interception_result=eval_result,
            snapshot_id=snapshot_id,
            execution_result=exec_result,
            human_approval=None,
            timestamp=now_iso,
        )
        session.steps.append(step_record)
        session.updated_at = now_iso

        # Update action in SQLite
        try:
            with SessionLocal() as db:
                if action_db_id:
                    audit_service.record_action_execution(
                        db=db,
                        action_id=action_db_id,
                        snapshot_id=snapshot_id,
                        exec_result=exec_result,
                    )
        except Exception:
            pass

        # Emit action_executed
        event_service.publish(
            "action_executed",
            {
                "task_id": session.session_id,
                "action_id": action_db_id,
                "action": proposed.action,
                "exit_code": exec_result.exit_code,
                "success": exec_result.success,
                "snapshot_id": snapshot_id,
            },
            task_id=session.session_id,
        )

        return session

    def resume_approval(self, session_id: str, approved: bool) -> AgentSession:
        """Resume a paused action after human approval or rejection."""
        session = self._sessions.get(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")

        if session.state != TaskState.WAITING_APPROVAL or not session.pending_approval_step:
            raise ValueError(f"Session '{session_id}' is not awaiting human approval.")

        pending_step = session.pending_approval_step
        now_iso = datetime.now(timezone.utc).isoformat()
        action_db_id = pending_step.action_id

        # Record decision in SQLite
        try:
            with SessionLocal() as db:
                if action_db_id:
                    audit_service.record_human_approval(db=db, action_id=action_db_id, approved=approved)
        except Exception:
            pass

        if not approved:
            pending_step.human_approval = False
            session.state = TaskState.STOPPED
            session.summary = f"Action '{pending_step.proposed_action.action}' rejected by human operator. Execution stopped."
            session.pending_approval_step = None
            session.updated_at = now_iso

            try:
                with SessionLocal() as db:
                    audit_service.update_task_state(db, session.session_id, "STOPPED", summary=session.summary)
            except Exception:
                pass

            event_service.publish(
                "action_rejected",
                {
                    "task_id": session.session_id,
                    "action_id": action_db_id,
                    "action": pending_step.proposed_action.action,
                },
                task_id=session.session_id,
            )
            return session

        # Operator approved
        pending_step.human_approval = True
        session.state = TaskState.RUNNING

        # Execute through controlled executor
        action_type = ActionType(pending_step.proposed_action.action)
        action_req = ActionRequest(action=action_type, params=pending_step.proposed_action.params)
        exec_result = self.executor.execute(action_req)

        pending_step.execution_result = exec_result
        session.pending_approval_step = None
        session.updated_at = now_iso

        # Update action in SQLite
        try:
            with SessionLocal() as db:
                if action_db_id:
                    audit_service.record_action_execution(
                        db=db,
                        action_id=action_db_id,
                        snapshot_id=None,
                        exec_result=exec_result,
                    )
                audit_service.update_task_state(db, session.session_id, "RUNNING")
        except Exception:
            pass

        event_service.publish(
            "action_executed",
            {
                "task_id": session.session_id,
                "action_id": action_db_id,
                "action": pending_step.proposed_action.action,
                "exit_code": exec_result.exit_code,
                "success": exec_result.success,
            },
            task_id=session.session_id,
        )

        return session

    def run_until_complete_or_paused(self, session_id: str, max_steps: int = 15) -> AgentSession:
        """Run execution loop iteratively until task finishes or pauses for human approval."""
        session = self._sessions.get(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")

        count = 0
        while count < max_steps:
            if session.state in (TaskState.COMPLETED, TaskState.WAITING_APPROVAL, TaskState.FAILED, TaskState.STOPPED):
                break
            self.step(session_id)
            count += 1

        return session
