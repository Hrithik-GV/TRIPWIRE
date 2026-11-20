import pytest
from app.tripwire.decision_engine import DecisionEngine, DecisionRequest, Decision

def test_decision_threshold_run():
    engine = DecisionEngine()
    req = DecisionRequest(
        trust_score=0.85,
        risk_level="low",
        risk_score=0.10,
        is_reversible=True,
        action="read_file",
    )
    res = engine.evaluate(req)
    assert res.decision == Decision.RUN
    assert res.requires_snapshot is False
    assert res.requires_human_approval is False
    assert len(res.overrides_applied) == 0

def test_decision_threshold_snapshot_and_run():
    engine = DecisionEngine()
    req = DecisionRequest(
        trust_score=0.65,
        risk_level="medium",
        risk_score=0.45,
        is_reversible=True,
        action="write_file",
    )
    res = engine.evaluate(req)
    assert res.decision == Decision.SNAPSHOT_AND_RUN
    assert res.requires_snapshot is True
    assert res.requires_human_approval is False
    assert len(res.overrides_applied) == 0

def test_decision_threshold_pause_low_trust():
    engine = DecisionEngine()
    req = DecisionRequest(
        trust_score=0.45,
        risk_level="medium",
        risk_score=0.50,
        is_reversible=True,
        action="write_file",
    )
    res = engine.evaluate(req)
    assert res.decision == Decision.PAUSE
    assert res.requires_snapshot is False
    assert res.requires_human_approval is True
    assert "insufficient trust score" in res.explanation

# Safety Overrides Tests

def test_override_critical_risk_blocks_high_trust():
    """Even if trust score is 0.95, critical risk operations must ALWAYS PAUSE."""
    engine = DecisionEngine()
    req = DecisionRequest(
        trust_score=0.95,
        risk_level="critical",
        risk_score=0.95,
        is_reversible=False,
        action="write_file",
    )
    res = engine.evaluate(req)
    assert res.decision == Decision.PAUSE
    assert res.requires_human_approval is True
    assert any("CRITICAL_RISK_OVERRIDE" in o for o in res.overrides_applied)

def test_override_unsupported_operation_never_executes():
    """Unsupported operations like arbitrary shell commands must never execute."""
    engine = DecisionEngine()
    req = DecisionRequest(
        trust_score=0.88,
        risk_level="low",
        risk_score=0.20,
        is_reversible=True,
        action="execute_shell_script",
    )
    res = engine.evaluate(req)
    assert res.decision == Decision.PAUSE
    assert res.requires_human_approval is True
    assert any("Unsupported Action" in o for o in res.overrides_applied)

def test_override_non_recoverable_high_impact():
    """Irreversible high-impact operations (e.g. core file deletion) must ALWAYS PAUSE."""
    engine = DecisionEngine()
    req = DecisionRequest(
        trust_score=0.82,  # Above 0.80 RUN threshold
        risk_level="high",
        risk_score=0.85,
        is_reversible=False,
        action="delete_file",
        impact_scope="core_file_deletion",
    )
    res = engine.evaluate(req)
    # The override downgrades RUN to PAUSE
    assert res.decision == Decision.PAUSE
    assert res.requires_human_approval is True
    assert any("NON_RECOVERABLE_IMPACT_OVERRIDE" in o for o in res.overrides_applied)

