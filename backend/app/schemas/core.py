import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class TaskCreateRequest(BaseModel):
    user_goal: str = Field(..., description="Prompt or goal for the autonomous agent")
    auto_run: bool = Field(default=True, description="Whether to execute until completed or paused")

class ActionDetailResponse(BaseModel):
    id: str
    task_id: str
    step_number: int
    action_name: str
    params: Dict[str, Any] = Field(default_factory=dict)
    rationale: Optional[str] = None
    expected_outcome: Optional[str] = None
    claimed_outcome: Optional[str] = None
    status: str

    # Evaluation Breakdown
    evidence_score: Optional[float] = None
    evidence_verified: Optional[bool] = None
    evidence_explanation: Optional[str] = None
    evidence_details: Dict[str, Any] = Field(default_factory=dict)

    reason_score: Optional[float] = None
    reason_is_relevant: Optional[bool] = None
    reason_explanation: Optional[str] = None
    evaluation_mode: Optional[str] = None

    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    is_reversible: Optional[bool] = None
    risk_explanation: Optional[str] = None
    impact_scope: Optional[str] = None

    trust_score: Optional[float] = None
    trust_explanation: Optional[str] = None

    decision: Optional[str] = None
    decision_reasons: List[str] = Field(default_factory=list)
    overrides_applied: List[str] = Field(default_factory=list)

    # Execution & Snapshot
    snapshot_id: Optional[str] = None
    execution_success: Optional[bool] = None
    execution_exit_code: Optional[int] = None
    execution_output: Optional[str] = None
    execution_error: Optional[str] = None
    execution_time_ms: Optional[float] = None

    # Approval
    human_approval: Optional[bool] = None
    approval_timestamp: Optional[str] = None

    created_at: str
    updated_at: str

class TaskSummaryResponse(BaseModel):
    id: str
    user_goal: str
    state: str
    summary: Optional[str] = None
    action_count: int = 0
    created_at: str
    updated_at: str

class TaskDetailResponse(BaseModel):
    id: str
    user_goal: str
    state: str
    summary: Optional[str] = None
    actions: List[ActionDetailResponse] = Field(default_factory=list)
    created_at: str
    updated_at: str

class ActionApprovalRequest(BaseModel):
    approved: bool = Field(default=True, description="True to authorize execution; False to reject")

class SnapshotItemResponse(BaseModel):
    snapshot_id: str
    description: str
    timestamp: str
    file_count: int
    total_size_bytes: int

class SnapshotRestoreResponse(BaseModel):
    success: bool
    snapshot_id: str
    message: str

class SystemStatsResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    running_tasks: int
    waiting_approval_tasks: int
    stopped_tasks: int
    total_actions: int
    executed_actions: int
    paused_actions: int
    human_approved_count: int
    human_rejected_count: int
    average_trust_score: float
    snapshots_count: int

