from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.tripwire.evidence_checker import EvidenceChecker, EvidenceCheckRequest, EvidenceCheckResult
from app.tripwire.reason_checker import ReasonChecker, ReasonCheckRequest, ReasonCheckResult
from app.tripwire.risk_checker import RiskChecker, RiskCheckRequest, RiskCheckResult
from app.tripwire.trust_scorer import TrustScorer, TrustScoreResult
from app.tripwire.decision_engine import DecisionEngine, DecisionRequest, DecisionResult, Decision

class InterceptionRequest(BaseModel):
    action: str = Field(..., description="Action name to evaluate")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    user_goal: str = Field(..., description="Stated objective of the user session")
    action_description: Optional[str] = Field(default=None, description="Agent's description of what it is doing")
    expected_outcome: Optional[str] = Field(default=None, description="What the agent expects to happen")
    claimed_outcome: Optional[str] = Field(default=None, description="Agent's claim regarding prior or expected output")
    before_content: Optional[str] = Field(default=None, description="Target file content prior to action")
    after_content: Optional[str] = Field(default=None, description="Target file content proposed or after action")
    command_exit_code: Optional[int] = Field(default=None, description="Exit code from command if verifying execution")
    command_output: Optional[str] = Field(default=None, description="Execution stdout/stderr if verifying test/command")
    previous_actions: List[Dict[str, Any]] = Field(default_factory=list, description="Prior actions in current session")
    workspace_dir: Optional[str] = Field(default=None, description="Target workspace directory")

class InterceptionResult(BaseModel):
    action: str
    params: Dict[str, Any]
    is_valid_action: bool
    validation_error: Optional[str] = None
    evidence: EvidenceCheckResult
    reason: ReasonCheckResult
    risk: RiskCheckResult
    trust: TrustScoreResult
    decision: DecisionResult
    timestamp: str

class TripwireInterceptor:
    """Central gateway that evaluates actions through Evidence, Reason, Risk, Trust, and Decision pipelines."""

    def __init__(
        self,
        workspace_dir: Optional[str] = None,
        llm_api_key: Optional[str] = None,
    ):
        self.evidence_checker = EvidenceChecker(workspace_dir=workspace_dir)
        self.reason_checker = ReasonChecker(api_key=llm_api_key)
        self.risk_checker = RiskChecker()
        self.trust_scorer = TrustScorer()
        self.decision_engine = DecisionEngine()

    def intercept(self, request: InterceptionRequest) -> InterceptionResult:
        """Evaluate an action through the full 6-stage Tripwire safety pipeline.
        
        NOTE: Does NOT execute the action directly. Returns the comprehensive safety evaluation.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        action = request.action.strip()
        params = request.params or {}

        # Stage 1: Validate action syntax & parameters
        is_valid, val_err = self._validate_action(action, params)

        if not is_valid:
            # Short-circuit invalid or dangerous syntax
            evidence_res = EvidenceCheckResult(
                evidence_score=0.0,
                verified=False,
                explanation=f"Validation failed: {val_err}",
                evidence_details={"validation_error": val_err},
            )
            reason_res = ReasonCheckResult(
                reason_score=0.0,
                is_relevant=False,
                explanation=f"Action invalid: {val_err}",
                evaluation_mode="deterministic_fallback",
                alignment_signals={"valid": False},
            )
            risk_res = RiskCheckResult(
                risk_score=1.00,
                risk_level="critical",
                is_reversible=False,
                explanation=f"Invalid action syntax: {val_err}",
                impact_scope="invalid_action",
                risk_factors=["invalid_action_structure"],
            )
            trust_res = self.trust_scorer.calculate(0.0, 0.0, 1.0)
            dec_req = DecisionRequest(
                trust_score=trust_res.trust_score,
                risk_level="critical",
                risk_score=1.00,
                is_reversible=False,
                action=action,
                impact_scope="invalid_action",
            )
            dec_res = self.decision_engine.evaluate(dec_req)

            return InterceptionResult(
                action=action,
                params=params,
                is_valid_action=False,
                validation_error=val_err,
                evidence=evidence_res,
                reason=reason_res,
                risk=risk_res,
                trust=trust_res,
                decision=dec_res,
                timestamp=now_iso,
            )

        # Stage 2: Evidence Check
        evidence_req = EvidenceCheckRequest(
            action=action,
            params=params,
            claimed_outcome=request.claimed_outcome,
            before_content=request.before_content,
            after_content=request.after_content,
            command_exit_code=request.command_exit_code,
            command_output=request.command_output,
            workspace_dir=request.workspace_dir,
        )
        evidence_res = self.evidence_checker.evaluate(evidence_req)

        # Stage 3: Reason Check
        reason_req = ReasonCheckRequest(
            user_goal=request.user_goal,
            proposed_action=action,
            action_params=params,
            action_description=request.action_description,
            expected_outcome=request.expected_outcome,
            previous_actions=request.previous_actions,
        )
        reason_res = self.reason_checker.evaluate(reason_req)

        # Stage 4: Risk Check
        risk_req = RiskCheckRequest(
            action=action,
            params=params,
        )
        risk_res = self.risk_checker.evaluate(risk_req)

        # Stage 5: Trust Scorer
        trust_res = self.trust_scorer.calculate(
            evidence_score=evidence_res.evidence_score,
            reason_score=reason_res.reason_score,
            risk_score=risk_res.risk_score,
        )

        # Stage 6: Decision Engine
        dec_req = DecisionRequest(
            trust_score=trust_res.trust_score,
            risk_level=risk_res.risk_level,
            risk_score=risk_res.risk_score,
            is_reversible=risk_res.is_reversible,
            action=action,
            impact_scope=risk_res.impact_scope,
            evidence_score=evidence_res.evidence_score,
            reason_score=reason_res.reason_score,
        )
        dec_res = self.decision_engine.evaluate(dec_req)

        return InterceptionResult(
            action=action,
            params=params,
            is_valid_action=True,
            validation_error=None,
            evidence=evidence_res,
            reason=reason_res,
            risk=risk_res,
            trust=trust_res,
            decision=dec_res,
            timestamp=now_iso,
        )

    def _validate_action(self, action: str, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate action schema structure before evaluation."""
        if not action:
            return False, "Action name cannot be empty"

        requires_path = {"read_file", "write_file", "create_file", "delete_file"}
        if action in requires_path:
            p = params.get("path")
            if not p or not isinstance(p, str) or not p.strip():
                return False, f"Action '{action}' requires non-empty string parameter 'path'"

        if action == "write_file" and "content" not in params:
            return False, "Action 'write_file' requires 'content' parameter"

        return True, None

# Convenience functional entrypoint
_default_interceptor = TripwireInterceptor()

def intercept_action(request: InterceptionRequest) -> InterceptionResult:
    """Central standalone interception function."""
    return _default_interceptor.intercept(request)

