from fastapi import APIRouter
from app.tripwire.evidence_checker import EvidenceChecker, EvidenceCheckRequest, EvidenceCheckResult
from app.tripwire.reason_checker import ReasonChecker, ReasonCheckRequest, ReasonCheckResult
from app.tripwire.risk_checker import RiskChecker, RiskCheckRequest, RiskCheckResult

router = APIRouter(prefix="/api/evaluations", tags=["Tripwire Evaluations"])

evidence_checker = EvidenceChecker()
reason_checker = ReasonChecker()
risk_checker = RiskChecker()

@router.post("/evidence", response_model=EvidenceCheckResult)
def evaluate_evidence(request: EvidenceCheckRequest) -> EvidenceCheckResult:
    """Verify physical ground-truth evidence, diffs, and test output."""
    return evidence_checker.evaluate(request)

@router.post("/reason", response_model=ReasonCheckResult)
def evaluate_reason(request: ReasonCheckRequest) -> ReasonCheckResult:
    """Evaluate action alignment with user goal using LLM judge or deterministic fallback."""
    return reason_checker.evaluate(request)

@router.post("/risk", response_model=RiskCheckResult)
def evaluate_risk(request: RiskCheckRequest) -> RiskCheckResult:
    """Classify operation risk, reversibility, and blast radius."""
    return risk_checker.evaluate(request)

