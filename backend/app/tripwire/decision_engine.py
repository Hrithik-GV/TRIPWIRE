from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Decision(str, Enum):
    RUN = "RUN"
    SNAPSHOT_AND_RUN = "SNAPSHOT_AND_RUN"
    PAUSE = "PAUSE"

class DecisionRequest(BaseModel):
    trust_score: float = Field(..., ge=0.0, le=1.0, description="Calculated composite trust score")
    risk_level: str = Field(..., description="Operational risk level: low, medium, high, critical")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Raw risk score")
    is_reversible: bool = Field(default=True, description="Whether action can be rolled back trivially")
    action: str = Field(..., description="Proposed action name")
    impact_scope: Optional[str] = Field(default=None, description="Blast radius categorization")
    evidence_score: Optional[float] = Field(default=None, description="Optional raw evidence score")
    reason_score: Optional[float] = Field(default=None, description="Optional raw reason score")

class DecisionResult(BaseModel):
    decision: Decision
    trust_score: float
    requires_snapshot: bool
    requires_human_approval: bool
    overrides_applied: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    explanation: str

class DecisionEngine:
    """Evaluates trust score against policy thresholds and enforces non-bypassable safety overrides."""

    RUN_THRESHOLD = 0.80
    SNAPSHOT_THRESHOLD = 0.50

    SUPPORTED_ACTIONS = {
        "list_files",
        "read_file",
        "write_file",
        "create_file",
        "delete_file",
        "run_tests",
    }

    def evaluate(self, request: DecisionRequest) -> DecisionResult:
        """Determine gating decision (RUN, SNAPSHOT_AND_RUN, or PAUSE) with strict safety overrides."""
        trust = request.trust_score
        risk_lvl = request.risk_level.lower().strip()
        action = request.action.lower().strip()

        # Step 1: Base threshold evaluation
        if trust >= self.RUN_THRESHOLD:
            base_decision = Decision.RUN
            requires_snapshot = False
            requires_human_approval = False
            base_reason = f"Trust score ({trust:.2f}) meets or exceeds autonomous execution threshold ({self.RUN_THRESHOLD:.2f})."
        elif trust >= self.SNAPSHOT_THRESHOLD:
            base_decision = Decision.SNAPSHOT_AND_RUN
            requires_snapshot = True
            requires_human_approval = False
            base_reason = f"Trust score ({trust:.2f}) qualifies for guarded execution; filesystem snapshot mandatory before run."
        else:
            base_decision = Decision.PAUSE
            requires_snapshot = False
            requires_human_approval = True
            base_reason = f"Trust score ({trust:.2f}) falls below safe execution threshold ({self.SNAPSHOT_THRESHOLD:.2f}). Human review required."

        final_decision = base_decision
        overrides: List[str] = []
        reasons: List[str] = [base_reason]

        # Step 2: Safety Overrides (CANNOT be bypassed by trust score)

        # Override A: Unsupported operations must NEVER execute
        if action not in self.SUPPORTED_ACTIONS:
            final_decision = Decision.PAUSE
            requires_human_approval = True
            requires_snapshot = False
            override_msg = f"UNSUPPORTED_OPERATION_OVERRIDE [Unsupported Action]: Operation '{action}' is unrecognized and blocked from execution."
            overrides.append(override_msg)
            reasons.append(override_msg)

        # Override B: Critical-risk operations must ALWAYS PAUSE
        if risk_lvl == "critical" or request.risk_score >= 0.90:
            final_decision = Decision.PAUSE
            requires_human_approval = True
            requires_snapshot = False
            override_msg = f"CRITICAL_RISK_OVERRIDE: Operation severity is critical (risk_score={request.risk_score:.2f}). Autonomous execution blocked."
            overrides.append(override_msg)
            reasons.append(override_msg)

        # Override C: Non-recoverable high-impact operations must ALWAYS PAUSE
        if not request.is_reversible and (risk_lvl == "high" or request.risk_score >= 0.70):
            final_decision = Decision.PAUSE
            requires_human_approval = True
            requires_snapshot = False
            override_msg = (
                f"NON_RECOVERABLE_IMPACT_OVERRIDE: Operation '{action}' on '{request.impact_scope or 'resource'}' "
                "is irreversible and high-risk. Mandatory human authorization required."
            )
            overrides.append(override_msg)
            reasons.append(override_msg)

        if final_decision == Decision.RUN:
            explanation = f"Action '{action}' approved for autonomous execution (Trust Score: {trust:.2f})."
        elif final_decision == Decision.SNAPSHOT_AND_RUN:
            explanation = f"Action '{action}' approved with pre-execution snapshot guard (Trust Score: {trust:.2f})."
        else:
            if overrides:
                explanation = f"Action '{action}' PAUSED due to safety overrides: {'; '.join(overrides)}"
            else:
                explanation = f"Action '{action}' PAUSED due to insufficient trust score ({trust:.2f} < {self.SNAPSHOT_THRESHOLD:.2f})."

        return DecisionResult(
            decision=final_decision,
            trust_score=trust,
            requires_snapshot=requires_snapshot,
            requires_human_approval=requires_human_approval,
            overrides_applied=overrides,
            reasons=reasons,
            explanation=explanation,
        )
