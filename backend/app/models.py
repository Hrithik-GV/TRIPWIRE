import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True, index=True)
    user_goal = Column(Text, nullable=False)
    state = Column(String(32), nullable=False, default="PENDING", index=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    actions = relationship(
        "ActionModel",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="ActionModel.step_number",
    )

class ActionModel(Base):
    __tablename__ = "actions"

    id = Column(String(64), primary_key=True, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    action_name = Column(String(64), nullable=False)
    params_json = Column(Text, nullable=False, default="{}")
    rationale = Column(Text, nullable=True)
    expected_outcome = Column(Text, nullable=True)
    claimed_outcome = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="PENDING", index=True)

    # Tripwire Evaluations
    evidence_score = Column(Float, nullable=True)
    evidence_verified = Column(Boolean, nullable=True)
    evidence_explanation = Column(Text, nullable=True)
    evidence_details_json = Column(Text, nullable=True)

    reason_score = Column(Float, nullable=True)
    reason_is_relevant = Column(Boolean, nullable=True)
    reason_explanation = Column(Text, nullable=True)
    evaluation_mode = Column(String(32), nullable=True)

    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(32), nullable=True)
    is_reversible = Column(Boolean, nullable=True)
    risk_explanation = Column(Text, nullable=True)
    impact_scope = Column(String(64), nullable=True)

    trust_score = Column(Float, nullable=True)
    trust_explanation = Column(Text, nullable=True)

    decision = Column(String(32), nullable=True)  # RUN, SNAPSHOT_AND_RUN, PAUSE
    decision_reasons_json = Column(Text, nullable=True)
    overrides_applied_json = Column(Text, nullable=True)

    # Execution & Snapshot
    snapshot_id = Column(String(64), nullable=True)
    execution_success = Column(Boolean, nullable=True)
    execution_exit_code = Column(Integer, nullable=True)
    execution_output = Column(Text, nullable=True)
    execution_error = Column(Text, nullable=True)
    execution_time_ms = Column(Float, nullable=True)

    # Human-in-the-loop
    human_approval = Column(Boolean, nullable=True)  # True = approved, False = rejected, None = pending
    approval_timestamp = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    task = relationship("TaskModel", back_populates="actions")

