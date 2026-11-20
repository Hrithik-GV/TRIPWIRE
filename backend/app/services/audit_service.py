import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import TaskModel, ActionModel
from app.schemas import ActionDetailResponse, TaskSummaryResponse, TaskDetailResponse, SystemStatsResponse
from app.services.snapshot import SnapshotManager

def utcnow():
    return datetime.now(timezone.utc)

class AuditService:
    """Handles SQLite persistence for tasks, actions, evaluations, execution results, and approvals."""

    def create_task(self, db: Session, user_goal: str, task_id: Optional[str] = None) -> TaskModel:
        tid = task_id or f"task_{uuid.uuid4().hex[:10]}"
        task = TaskModel(
            id=tid,
            user_goal=user_goal,
            state="PENDING",
            summary="Task initialized",
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def update_task_state(
        self,
        db: Session,
        task_id: str,
        state: str,
        summary: Optional[str] = None,
    ) -> Optional[TaskModel]:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            return None
        task.state = state
        if summary is not None:
            task.summary = summary
        task.updated_at = utcnow()
        db.commit()
        db.refresh(task)
        return task

    def record_action_proposal(
        self,
        db: Session,
        task_id: str,
        step_number: int,
        action_name: str,
        params: Dict[str, Any],
        rationale: Optional[str],
        expected_outcome: Optional[str],
        claimed_outcome: Optional[str],
        interception: Any,
    ) -> ActionModel:
        action_id = f"act_{uuid.uuid4().hex[:10]}"
        ev = interception.evidence
        rs = interception.reason
        rk = interception.risk
        tr = interception.trust
        dc = interception.decision

        action_record = ActionModel(
            id=action_id,
            task_id=task_id,
            step_number=step_number,
            action_name=action_name,
            params_json=json.dumps(params or {}),
            rationale=rationale,
            expected_outcome=expected_outcome,
            claimed_outcome=claimed_outcome,
            status="PAUSED" if dc.decision.value == "PAUSE" else "PENDING",

            # Evidence
            evidence_score=ev.evidence_score,
            evidence_verified=ev.verified,
            evidence_explanation=ev.explanation,
            evidence_details_json=json.dumps(ev.evidence_details or {}),

            # Reason
            reason_score=rs.reason_score,
            reason_is_relevant=rs.is_relevant,
            reason_explanation=rs.explanation,
            evaluation_mode=rs.evaluation_mode,

            # Risk
            risk_score=rk.risk_score,
            risk_level=rk.risk_level,
            is_reversible=rk.is_reversible,
            risk_explanation=rk.explanation,
            impact_scope=rk.impact_scope,

            # Trust
            trust_score=tr.trust_score,
            trust_explanation=tr.explanation,

            # Decision
            decision=dc.decision.value,
            decision_reasons_json=json.dumps(dc.reasons or []),
            overrides_applied_json=json.dumps(dc.overrides_applied or []),

            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(action_record)
        db.commit()
        db.refresh(action_record)
        return action_record

    def record_action_execution(
        self,
        db: Session,
        action_id: str,
        snapshot_id: Optional[str],
        exec_result: Any,
    ) -> Optional[ActionModel]:
        action = db.query(ActionModel).filter(ActionModel.id == action_id).first()
        if not action:
            return None

        action.snapshot_id = snapshot_id
        action.status = "EXECUTED" if exec_result.success else "FAILED"
        action.execution_success = exec_result.success
        action.execution_exit_code = exec_result.exit_code
        action.execution_error = exec_result.error
        action.execution_time_ms = exec_result.execution_time_ms

        if isinstance(exec_result.data, dict) and "output" in exec_result.data:
            action.execution_output = exec_result.data["output"]
        elif exec_result.data is not None:
            action.execution_output = json.dumps(exec_result.data)

        action.updated_at = utcnow()
        db.commit()
        db.refresh(action)
        return action

    def record_human_approval(
        self,
        db: Session,
        action_id: str,
        approved: bool,
    ) -> Optional[ActionModel]:
        action = db.query(ActionModel).filter(ActionModel.id == action_id).first()
        if not action:
            return None

        action.human_approval = approved
        action.approval_timestamp = utcnow()
        action.status = "APPROVED" if approved else "REJECTED"
        action.updated_at = utcnow()
        db.commit()
        db.refresh(action)
        return action

    def get_task(self, db: Session, task_id: str) -> Optional[TaskModel]:
        return db.query(TaskModel).filter(TaskModel.id == task_id).first()

    def list_tasks(self, db: Session, limit: int = 50) -> List[TaskModel]:
        return db.query(TaskModel).order_by(TaskModel.created_at.desc()).limit(limit).all()

    def get_action(self, db: Session, action_id: str) -> Optional[ActionModel]:
        return db.query(ActionModel).filter(ActionModel.id == action_id).first()

    def list_actions(
        self,
        db: Session,
        status: Optional[str] = None,
        task_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ActionModel]:
        query = db.query(ActionModel)
        if status:
            query = query.filter(ActionModel.status == status)
        if task_id:
            query = query.filter(ActionModel.task_id == task_id)
        return query.order_by(ActionModel.created_at.desc()).limit(limit).all()

    def get_stats(self, db: Session) -> SystemStatsResponse:
        """Compute live system statistics dynamically from SQLite records."""
        total_tasks = db.query(TaskModel).count()
        completed_tasks = db.query(TaskModel).filter(TaskModel.state == "COMPLETED").count()
        running_tasks = db.query(TaskModel).filter(TaskModel.state == "RUNNING").count()
        waiting_approval = db.query(TaskModel).filter(TaskModel.state == "WAITING_APPROVAL").count()
        stopped_tasks = db.query(TaskModel).filter(TaskModel.state == "STOPPED").count()

        total_actions = db.query(ActionModel).count()
        executed_actions = db.query(ActionModel).filter(ActionModel.status == "EXECUTED").count()
        paused_actions = db.query(ActionModel).filter(ActionModel.decision == "PAUSE").count()
        human_approved = db.query(ActionModel).filter(ActionModel.human_approval == True).count()
        human_rejected = db.query(ActionModel).filter(ActionModel.human_approval == False).count()

        avg_trust_raw = db.query(func.avg(ActionModel.trust_score)).scalar()
        avg_trust = round(float(avg_trust_raw), 4) if avg_trust_raw is not None else 0.0

        snapshots_count = len(SnapshotManager().list_snapshots())

        return SystemStatsResponse(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            running_tasks=running_tasks,
            waiting_approval_tasks=waiting_approval,
            stopped_tasks=stopped_tasks,
            total_actions=total_actions,
            executed_actions=executed_actions,
            paused_actions=paused_actions,
            human_approved_count=human_approved,
            human_rejected_count=human_rejected,
            average_trust_score=avg_trust,
            snapshots_count=snapshots_count,
        )

    def to_action_response(self, action: ActionModel) -> ActionDetailResponse:
        """Convert SQLAlchemy ActionModel to Pydantic ActionDetailResponse."""
        return ActionDetailResponse(
            id=action.id,
            task_id=action.task_id,
            step_number=action.step_number,
            action_name=action.action_name,
            params=json.loads(action.params_json or "{}"),
            rationale=action.rationale,
            expected_outcome=action.expected_outcome,
            claimed_outcome=action.claimed_outcome,
            status=action.status,

            evidence_score=action.evidence_score,
            evidence_verified=action.evidence_verified,
            evidence_explanation=action.evidence_explanation,
            evidence_details=json.loads(action.evidence_details_json or "{}"),

            reason_score=action.reason_score,
            reason_is_relevant=action.reason_is_relevant,
            reason_explanation=action.reason_explanation,
            evaluation_mode=action.evaluation_mode,

            risk_score=action.risk_score,
            risk_level=action.risk_level,
            is_reversible=action.is_reversible,
            risk_explanation=action.risk_explanation,
            impact_scope=action.impact_scope,

            trust_score=action.trust_score,
            trust_explanation=action.trust_explanation,

            decision=action.decision,
            decision_reasons=json.loads(action.decision_reasons_json or "[]"),
            overrides_applied=json.loads(action.overrides_applied_json or "[]"),

            snapshot_id=action.snapshot_id,
            execution_success=action.execution_success,
            execution_exit_code=action.execution_exit_code,
            execution_output=action.execution_output,
            execution_error=action.execution_error,
            execution_time_ms=action.execution_time_ms,

            human_approval=action.human_approval,
            approval_timestamp=action.approval_timestamp.isoformat() if action.approval_timestamp else None,

            created_at=action.created_at.isoformat() if action.created_at else "",
            updated_at=action.updated_at.isoformat() if action.updated_at else "",
        )

audit_service = AuditService()

