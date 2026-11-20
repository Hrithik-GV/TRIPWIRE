from fastapi import APIRouter
from app.tripwire.evidence_checker import EvidenceChecker, EvidenceCheckRequest, EvidenceCheckResult
from app.tripwire.reason_checker import ReasonChecker, ReasonCheckRequest, ReasonCheckResult
from app.tripwire.risk_checker import RiskChecker, RiskCheckRequest, RiskCheckResult
from app.tripwire.trust_scorer import TrustScorer, TrustScoreRequest, TrustScoreResult
from app.tripwire.decision_engine import DecisionEngine, DecisionRequest, DecisionResult
from app.tripwire.interceptor import TripwireInterceptor, InterceptionRequest, InterceptionResult

router = APIRouter(prefix="/api/evaluations", tags=["Tripwire Evaluations"])

evidence_checker = EvidenceChecker()
reason_checker = ReasonChecker()
risk_checker = RiskChecker()
interceptor = TripwireInterceptor()

@router.post("/intercept", response_model=InterceptionResult)
def intercept_action_endpoint(request: InterceptionRequest) -> InterceptionResult:
    """Run full Tripwire safety evaluation across Evidence, Reason, Risk, Trust, and Decision pipelines."""
    return interceptor.intercept(request)

@router.post("/trust", response_model=TrustScoreResult)
def calculate_trust(request: TrustScoreRequest) -> TrustScoreResult:
    """Calculate composite trust score: (0.40 * evidence) + (0.35 * reason) + (0.25 * (1 - risk))."""
    scorer = TrustScorer()
    return scorer.calculate(
        evidence_score=request.evidence_score,
        reason_score=request.reason_score,
        risk_score=request.risk_score,
    )

@router.post("/decision", response_model=DecisionResult)
def make_decision(request: DecisionRequest) -> DecisionResult:
    """Evaluate decision gating thresholds and safety overrides."""
    engine = DecisionEngine()
    return engine.evaluate(request)

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

