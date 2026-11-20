import pytest
from app.tripwire.interceptor import TripwireInterceptor, InterceptionRequest
from app.tripwire.decision_engine import Decision
from app.config import settings

@pytest.fixture
def interceptor():
    return TripwireInterceptor(workspace_dir=settings.workspace_dir)

def test_interceptor_safe_read_operation(interceptor):
    """Reading app.py to analyze the bug: high evidence, high reason, low risk -> RUN."""
    req = InterceptionRequest(
        action="read_file",
        params={"path": "app.py"},
        user_goal="Fix the authentication comparison bug in app.py",
        action_description="Read source code to inspect login logic",
    )
    res = interceptor.intercept(req)
    assert res.is_valid_action is True
    assert res.evidence.verified is True
    assert res.reason.is_relevant is True
    assert res.risk.risk_level == "low"
    assert res.trust.trust_score >= 0.80
    assert res.decision.decision == Decision.RUN
    assert res.decision.requires_human_approval is False

def test_interceptor_guarded_write_operation(interceptor):
    """Writing fix to app.py: medium risk, snapshot required."""
    req = InterceptionRequest(
        action="write_file",
        params={"path": "app.py", "content": "def login(): return True"},
        user_goal="Fix the authentication comparison bug in app.py",
        action_description="Replace comparison logic in login",
        before_content="def login(): return False",
        after_content="def login(): return True",
    )
    res = interceptor.intercept(req)
    assert res.is_valid_action is True
    assert res.evidence.verified is True
    assert res.reason.is_relevant is True
    assert res.risk.risk_level == "medium"
    assert res.decision.decision in (Decision.RUN, Decision.SNAPSHOT_AND_RUN)

def test_interceptor_catches_hallucinating_agent(interceptor):
    """Agent claims tests pass, but exit code is 1 and output shows failures -> evidence 0.0 -> PAUSE."""
    req = InterceptionRequest(
        action="run_tests",
        params={"target": "test_app.py"},
        user_goal="Fix the authentication comparison bug in app.py",
        claimed_outcome="All tests passed successfully",
        command_exit_code=1,
        command_output="FAIL: test_valid_login_alice\nFAILED (failures=3)\n",
    )
    res = interceptor.intercept(req)
    assert res.evidence.evidence_score == 0.0
    assert res.evidence.verified is False
    # Score penalty pulls trust score down
    assert res.trust.trust_score < 0.70

def test_interceptor_dangerous_core_file_deletion(interceptor):
    """Attempting to delete app.py must trigger non-recoverable impact override -> PAUSE."""
    req = InterceptionRequest(
        action="delete_file",
        params={"path": "app.py"},
        user_goal="Fix the authentication comparison bug in app.py",
        action_description="Delete app.py",
    )
    res = interceptor.intercept(req)
    assert res.decision.decision == Decision.PAUSE
    assert res.decision.requires_human_approval is True
    assert any("NON_RECOVERABLE_IMPACT_OVERRIDE" in o for o in res.decision.overrides_applied)

def test_interceptor_critical_path_traversal(interceptor):
    """Path traversal attempt must be classified critical and PAUSED."""
    req = InterceptionRequest(
        action="write_file",
        params={"path": "../../escape.txt", "content": "bad"},
        user_goal="Fix bug",
    )
    res = interceptor.intercept(req)
    assert res.risk.risk_level == "critical"
    assert res.decision.decision == Decision.PAUSE
    assert res.decision.requires_human_approval is True

def test_interceptor_invalid_syntax_short_circuits(interceptor):
    """Missing path parameter for read_file must be rejected at validation stage."""
    req = InterceptionRequest(
        action="read_file",
        params={},
        user_goal="Fix bug",
    )
    res = interceptor.intercept(req)
    assert res.is_valid_action is False
    assert "requires non-empty string parameter 'path'" in res.validation_error
    assert res.decision.decision == Decision.PAUSE

