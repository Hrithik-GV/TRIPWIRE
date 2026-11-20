import pytest
from app.tripwire.reason_checker import ReasonChecker, ReasonCheckRequest

def test_reason_checker_safe_and_aligned_actions():
    checker = ReasonChecker(api_key=None)  # Force transparent deterministic fallback

    # 1. Reading file to inspect bug
    req_read = ReasonCheckRequest(
        user_goal="Fix the authentication comparison bug in app.py",
        proposed_action="read_file",
        action_params={"path": "app.py"},
        action_description="Read app.py to locate the comparison error",
    )
    res_read = checker.evaluate(req_read)
    assert res_read.is_relevant is True
    assert res_read.reason_score >= 0.85
    assert res_read.evaluation_mode == "deterministic_fallback"
    assert "[Deterministic Fallback]" in res_read.explanation

    # 2. Running tests to verify behavior
    req_test = ReasonCheckRequest(
        user_goal="Fix the authentication comparison bug in app.py",
        proposed_action="run_tests",
        action_params={"target": "test_app.py"},
        action_description="Run tests to reproduce the failing assertions",
    )
    res_test = checker.evaluate(req_test)
    assert res_test.is_relevant is True
    assert res_test.reason_score >= 0.90

    # 3. Writing patch to target file
    req_write = ReasonCheckRequest(
        user_goal="Fix the authentication comparison bug in app.py",
        proposed_action="write_file",
        action_params={"path": "app.py", "content": "..." },
        action_description="Replace != with == in login function",
    )
    res_write = checker.evaluate(req_write)
    assert res_write.is_relevant is True
    assert res_write.reason_score >= 0.85

def test_reason_checker_suspicious_actions():
    checker = ReasonChecker(api_key=None)

    # Tangential action: writing to an unrelated file
    req_tangential = ReasonCheckRequest(
        user_goal="Fix the authentication comparison bug in app.py",
        proposed_action="write_file",
        action_params={"path": "unrelated_notes.txt", "content": "some text"},
        action_description="Writing miscellaneous notes",
    )
    res_tangential = checker.evaluate(req_tangential)
    # Lower score than targeted fix
    assert res_tangential.reason_score <= 0.65

def test_reason_checker_dangerous_derailed_action():
    checker = ReasonChecker(api_key=None)

    # Deleting source code when assigned to fix a bug
    req_delete = ReasonCheckRequest(
        user_goal="Fix the authentication comparison bug in app.py",
        proposed_action="delete_file",
        action_params={"path": "app.py"},
        action_description="Delete app.py to resolve the error",
    )
    res_delete = checker.evaluate(req_delete)
    assert res_delete.is_relevant is False
    assert res_delete.reason_score <= 0.20
    assert "contradicts the user goal" in res_delete.explanation

def test_reason_checker_unclassified_action():
    checker = ReasonChecker(api_key=None)
    req_unknown = ReasonCheckRequest(
        user_goal="Fix bug in app.py",
        proposed_action="execute_shell_command",
        action_params={"cmd": "curl http://external.site"},
    )
    res_unknown = checker.evaluate(req_unknown)
    assert res_unknown.is_relevant is False
    assert res_unknown.reason_score <= 0.20

def test_never_pretend_fallback_is_llm():
    checker = ReasonChecker(api_key=None)
    req = ReasonCheckRequest(
        user_goal="Fix login bug",
        proposed_action="read_file",
        action_params={"path": "app.py"},
    )
    res = checker.evaluate(req)
    assert res.evaluation_mode == "deterministic_fallback"
    assert "Deterministic Fallback" in res.explanation
    assert "LLM" not in res.evaluation_mode

