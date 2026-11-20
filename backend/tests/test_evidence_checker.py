import tempfile
from pathlib import Path
import pytest

from app.tripwire.evidence_checker import EvidenceChecker, EvidenceCheckRequest

@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir).resolve()

def test_evidence_tests_pass_verified(temp_workspace):
    checker = EvidenceChecker(workspace_dir=str(temp_workspace))
    req = EvidenceCheckRequest(
        action="run_tests",
        claimed_outcome="All tests passed successfully",
        command_exit_code=0,
        command_output="Ran 5 tests in 0.002s\n\nOK\n",
    )
    res = checker.evaluate(req)
    assert res.verified is True
    assert res.evidence_score == 1.0
    assert "exit code 0" in res.explanation

def test_evidence_catches_agent_hallucination_on_test_failure(temp_workspace):
    """When an agent claims tests passed or bug was resolved, but exit code is 1 and output has FAIL."""
    checker = EvidenceChecker(workspace_dir=str(temp_workspace))
    req = EvidenceCheckRequest(
        action="run_tests",
        claimed_outcome="I fixed the login bug and all tests pass now",
        command_exit_code=1,
        command_output=".F.FF\nFAIL: test_invalid_password\nFAILED (failures=3)\n",
    )
    res = checker.evaluate(req)
    assert res.verified is False
    assert res.evidence_score == 0.0
    assert "contradicts agent claim" in res.explanation
    assert res.evidence_details["has_failure_in_output"] is True

def test_evidence_agent_accurately_reports_test_failure(temp_workspace):
    checker = EvidenceChecker(workspace_dir=str(temp_workspace))
    req = EvidenceCheckRequest(
        action="run_tests",
        claimed_outcome="Tests failed due to authentication bug",
        command_exit_code=1,
        command_output="FAIL: test_invalid_password\nFAILED (failures=3)\n",
    )
    res = checker.evaluate(req)
    assert res.verified is True
    assert res.evidence_score == 1.0
    assert "accurately reported that tests failed" in res.explanation

def test_evidence_file_write_verified_with_diff(temp_workspace):
    checker = EvidenceChecker(workspace_dir=str(temp_workspace))
    test_file = temp_workspace / "app.py"
    test_file.write_text("def login(): return True", encoding="utf-8")

    req = EvidenceCheckRequest(
        action="write_file",
        params={"path": "app.py"},
        claimed_outcome="Fixed login function return value",
        before_content="def login(): return False",
        after_content="def login(): return True",
    )
    res = checker.evaluate(req)
    assert res.verified is True
    assert res.evidence_score == 1.0
    assert res.evidence_details["file_exists_on_disk"] is True
    assert res.evidence_details["has_content_diff"] is True
    assert "diff" in res.evidence_details

def test_evidence_zero_diff_discrepancy(temp_workspace):
    """Agent claims code was modified, but before and after content are identical."""
    checker = EvidenceChecker(workspace_dir=str(temp_workspace))
    test_file = temp_workspace / "app.py"
    test_file.write_text("def login(): return False", encoding="utf-8")

    req = EvidenceCheckRequest(
        action="write_file",
        params={"path": "app.py"},
        claimed_outcome="Updated login logic",
        before_content="def login(): return False",
        after_content="def login(): return False",
    )
    res = checker.evaluate(req)
    assert res.verified is False
    assert res.evidence_score < 0.5
    assert "identical to before state" in res.explanation

def test_evidence_claimed_file_missing_on_disk(temp_workspace):
    checker = EvidenceChecker(workspace_dir=str(temp_workspace))
    req = EvidenceCheckRequest(
        action="create_file",
        params={"path": "phantom.py"},
        claimed_outcome="Created phantom helper",
    )
    res = checker.evaluate(req)
    assert res.verified is False
    assert res.evidence_score == 0.0
    assert "does not exist on disk" in res.explanation

def test_evidence_file_deletion_verified(temp_workspace):
    checker = EvidenceChecker(workspace_dir=str(temp_workspace))
    req = EvidenceCheckRequest(
        action="delete_file",
        params={"path": "removed.txt"},
        claimed_outcome="Deleted temp file",
    )
    res = checker.evaluate(req)
    assert res.verified is True
    assert res.evidence_score == 1.0
    assert "confirmed absent" in res.explanation

def test_evidence_file_deletion_failed(temp_workspace):
    checker = EvidenceChecker(workspace_dir=str(temp_workspace))
    existing = temp_workspace / "not_deleted.txt"
    existing.write_text("still here", encoding="utf-8")

    req = EvidenceCheckRequest(
        action="delete_file",
        params={"path": "not_deleted.txt"},
        claimed_outcome="Deleted file",
    )
    res = checker.evaluate(req)
    assert res.verified is False
    assert res.evidence_score == 0.0
    assert "still exists on disk" in res.explanation

