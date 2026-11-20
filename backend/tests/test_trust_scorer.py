import pytest
from app.tripwire.trust_scorer import TrustScorer, TrustScoreRequest

def test_trust_score_exact_formula():
    scorer = TrustScorer()
    
    # trust = (0.40 * 1.0) + (0.35 * 0.8) + (0.25 * (1 - 0.2))
    # trust = 0.40 + 0.28 + 0.20 = 0.88
    res = scorer.calculate(evidence_score=1.0, reason_score=0.8, risk_score=0.2)
    assert res.evidence_score == 1.0
    assert res.reason_score == 0.8
    assert res.risk_score == 0.2
    assert abs(res.trust_score - 0.88) < 0.0001
    assert "Trust Score 0.8800" in res.explanation

def test_trust_score_boundary_max():
    scorer = TrustScorer()
    # (0.40 * 1.0) + (0.35 * 1.0) + (0.25 * 1.0) = 1.0
    res = scorer.calculate(evidence_score=1.0, reason_score=1.0, risk_score=0.0)
    assert res.trust_score == 1.0

def test_trust_score_boundary_min():
    scorer = TrustScorer()
    # (0.40 * 0.0) + (0.35 * 0.0) + (0.25 * 0.0) = 0.0
    res = scorer.calculate(evidence_score=0.0, reason_score=0.0, risk_score=1.0)
    assert res.trust_score == 0.0

def test_trust_score_hallucination_penalty():
    scorer = TrustScorer()
    # Evidence is 0.0 (agent hallucinated or lied about test pass)
    # Reason is 0.90, Risk is 0.40
    # trust = (0.40 * 0) + (0.35 * 0.9) + (0.25 * 0.6) = 0 + 0.315 + 0.15 = 0.465 (Below 0.50 -> PAUSE)
    res = scorer.calculate(evidence_score=0.0, reason_score=0.90, risk_score=0.40)
    assert abs(res.trust_score - 0.465) < 0.0001

def test_trust_score_input_validation():
    scorer = TrustScorer()
    # Scores > 1.0 rejected
    with pytest.raises(ValueError):
        scorer.calculate(evidence_score=1.5, reason_score=0.5, risk_score=0.2)

    # Scores < 0.0 rejected
    with pytest.raises(ValueError):
        scorer.calculate(evidence_score=0.5, reason_score=-0.1, risk_score=0.2)

    with pytest.raises(ValueError):
        scorer.calculate(evidence_score=0.5, reason_score=0.5, risk_score=1.2)

