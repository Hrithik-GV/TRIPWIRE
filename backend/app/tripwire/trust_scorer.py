from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

class TrustScoreRequest(BaseModel):
    evidence_score: float = Field(..., description="Evidence verification score from 0.0 to 1.0")
    reason_score: float = Field(..., description="Reason alignment score from 0.0 to 1.0")
    risk_score: float = Field(..., description="Operational risk score from 0.0 to 1.0")

    @field_validator("evidence_score", "reason_score", "risk_score")
    @classmethod
    def validate_score_bounds(cls, v: float, info) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"{info.field_name} must be between 0.0 and 1.0, got {v}")
        return v

class TrustScoreResult(BaseModel):
    evidence_score: float = Field(..., ge=0.0, le=1.0)
    reason_score: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    trust_score: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    weights: Dict[str, float] = Field(default_factory=dict)

class TrustScorer:
    """Computes composite trust score: (0.40 * evidence) + (0.35 * reason) + (0.25 * (1 - risk))."""

    EVIDENCE_WEIGHT = 0.40
    REASON_WEIGHT = 0.35
    RISK_WEIGHT = 0.25

    def calculate(
        self,
        evidence_score: float,
        reason_score: float,
        risk_score: float,
    ) -> TrustScoreResult:
        """Validate input bounds and compute weighted composite trust score."""
        req = TrustScoreRequest(
            evidence_score=evidence_score,
            reason_score=reason_score,
            risk_score=risk_score,
        )

        # Weighted calculation
        raw_trust = (
            (self.EVIDENCE_WEIGHT * req.evidence_score)
            + (self.REASON_WEIGHT * req.reason_score)
            + (self.RISK_WEIGHT * (1.0 - req.risk_score))
        )
        trust_score = round(max(0.0, min(1.0, raw_trust)), 4)

        explanation = (
            f"Trust Score {trust_score:.4f} computed via weighted synthesis: "
            f"Evidence ({req.evidence_score:.2f} * {self.EVIDENCE_WEIGHT:.2f}) + "
            f"Reason ({req.reason_score:.2f} * {self.REASON_WEIGHT:.2f}) + "
            f"Inverted Risk ({(1.0 - req.risk_score):.2f} * {self.RISK_WEIGHT:.2f})."
        )

        return TrustScoreResult(
            evidence_score=req.evidence_score,
            reason_score=req.reason_score,
            risk_score=req.risk_score,
            trust_score=trust_score,
            explanation=explanation,
            weights={
                "evidence": self.EVIDENCE_WEIGHT,
                "reason": self.REASON_WEIGHT,
                "risk_inverted": self.RISK_WEIGHT,
            },
        )

