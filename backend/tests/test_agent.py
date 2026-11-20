import os
import shutil
import tempfile
from pathlib import Path
import pytest

from app.agent.agent_engine import AgentEngine, TaskState
from app.agent.planner import DeterministicPlanner, ProposedAction
from app.tripwire.decision_engine import Decision
from app.config import settings

BUGGY_APP_CODE = '''"""Demo Authentication Module"""

USERS_DB = {
    "alice": "correct_horse_battery_staple",
    "bob": "super_secret_p@ss123",
}

def login(username: str, password: str) -> bool:
    if not username or not password:
        return False
    if username not in USERS_DB:
        return False
    return USERS_DB[username] != password
'''

TEST_APP_CODE = '''import unittest
from app import login

class TestLogin(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(login("alice", "correct_horse_battery_staple"))
    def test_invalid(self):
        self.assertFalse(login("alice", "wrong_pass"))

if __name__ == "__main__":
    unittest.main()
'''

@pytest.fixture
def temp_demo_workspace():
    """Create an isolated workspace with app.py and test_app.py."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ws = Path(tmp_dir).resolve()
        (ws / "app.py").write_text(BUGGY_APP_CODE, encoding="utf-8")
        (ws / "test_app.py").write_text(TEST_APP_CODE, encoding="utf-8")
        (ws / "README.md").write_text("# Demo App", encoding="utf-8")
        yield str(ws)

def test_agent_successful_repair_workflow(temp_demo_workspace):
    """End-to-end test of the full autonomous bug repair workflow."""
    engine = AgentEngine(workspace_dir=temp_demo_workspace)
    session = engine.create_session("Inspect my Python project, fix the login bug and run the tests.")

    assert session.state == TaskState.PENDING
    assert session.current_step == 0

    # Run execution loop until completed or paused
    completed_session = engine.run_until_complete_or_paused(session.session_id, max_steps=12)

    assert completed_session.state == TaskState.COMPLETED
    assert completed_session.current_step >= 5

    # Verify action progression
    actions_taken = [s.proposed_action.action for s in completed_session.steps]
    assert "list_files" in actions_taken
    assert "read_file" in actions_taken
    assert "run_tests" in actions_taken
    assert "write_file" in actions_taken

    # Verify that app.py was actually repaired
    repaired_content = (Path(temp_demo_workspace) / "app.py").read_text(encoding="utf-8")
    assert "USERS_DB[username] == password" in repaired_content

    # Verify that the final test run PASSED
    final_test_step = [s for s in completed_session.steps if s.proposed_action.action == "run_tests"][-1]
    assert final_test_step.execution_result is not None
    assert final_test_step.execution_result.exit_code == 0
    assert final_test_step.execution_result.data["passed"] is True

def test_agent_dangerous_action_blocked(temp_demo_workspace):
    """Proposing to delete core source files must be intercepted, PAUSED, and not executed."""
    engine = AgentEngine(workspace_dir=temp_demo_workspace)
    session = engine.create_session("Demonstrate dangerous deletion of source files")

    # Run one step
    session = engine.step(session.session_id)

    assert session.state == TaskState.WAITING_APPROVAL
    assert session.pending_approval_step is not None
    assert session.pending_approval_step.proposed_action.action == "delete_file"
    assert session.pending_approval_step.interception_result.decision.decision == Decision.PAUSE

    # CRITICAL: app.py must NOT be deleted while waiting for approval
    assert (Path(temp_demo_workspace) / "app.py").exists()

def test_agent_human_rejection_stops_execution(temp_demo_workspace):
    """When human rejects a paused action, execution stops and file is preserved."""
    engine = AgentEngine(workspace_dir=temp_demo_workspace)
    session = engine.create_session("Demonstrate dangerous deletion of source files")

    # Step into pause
    session = engine.step(session.session_id)
    assert session.state == TaskState.WAITING_APPROVAL

    # Human rejects
    stopped_session = engine.resume_approval(session.session_id, approved=False)
    assert stopped_session.state == TaskState.STOPPED
    assert stopped_session.pending_approval_step is None
    assert (Path(temp_demo_workspace) / "app.py").exists()

def test_agent_human_approval_resumes_execution(temp_demo_workspace):
    """When human explicitly approves, action executes through the controlled executor."""
    engine = AgentEngine(workspace_dir=temp_demo_workspace)
    session = engine.create_session("Demonstrate dangerous deletion of source files")

    # Step into pause
    session = engine.step(session.session_id)
    assert session.state == TaskState.WAITING_APPROVAL

    # Human operator approves
    resumed_session = engine.resume_approval(session.session_id, approved=True)
    assert resumed_session.state == TaskState.RUNNING
    # Now app.py should be deleted following verified approval
    assert not (Path(temp_demo_workspace) / "app.py").exists()

