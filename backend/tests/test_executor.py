import os
import sys
import tempfile
import pytest
from pathlib import Path

from app.schemas.actions import (
    ActionRequest,
    ActionType,
    ListFilesParams,
    ReadFileParams,
    WriteFileParams,
    CreateFileParams,
    DeleteFileParams,
    RunTestsParams,
)
from app.services.executor import WorkspaceExecutor, SecurityError
from app.config import settings

@pytest.fixture
def temp_workspace():
    """Create an isolated temporary workspace for unit tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace_path = Path(tmp_dir).resolve()
        executor = WorkspaceExecutor(
            workspace_dir=str(workspace_path),
            command_timeout_seconds=5.0,
            max_output_chars=1000,
            max_file_size_bytes=10000,
        )
        yield executor, workspace_path

def test_list_files(temp_workspace):
    executor, workspace_path = temp_workspace
    (workspace_path / "hello.py").write_text("print('hello')", encoding="utf-8")
    (workspace_path / "sub").mkdir()
    (workspace_path / "sub" / "inner.txt").write_text("inner", encoding="utf-8")

    result = executor.execute(ActionRequest(
        action=ActionType.LIST_FILES,
        params={"path": ""}
    ))

    assert result.success is True
    assert result.exit_code == 0
    items = result.data
    names = [i["name"] for i in items]
    assert "hello.py" in names
    assert "sub" in names

def test_create_and_read_file(temp_workspace):
    executor, workspace_path = temp_workspace
    
    # Create file
    create_res = executor.execute(ActionRequest(
        action=ActionType.CREATE_FILE,
        params={"path": "notes.txt", "content": "Sample note content"}
    ))
    assert create_res.success is True
    assert (workspace_path / "notes.txt").exists()

    # Read file
    read_res = executor.execute(ActionRequest(
        action=ActionType.READ_FILE,
        params={"path": "notes.txt"}
    ))
    assert read_res.success is True
    assert read_res.data["content"] == "Sample note content"
    assert read_res.data["lines"] == 1

def test_create_file_already_exists(temp_workspace):
    executor, workspace_path = temp_workspace
    (workspace_path / "existing.txt").write_text("orig", encoding="utf-8")

    res = executor.execute(ActionRequest(
        action=ActionType.CREATE_FILE,
        params={"path": "existing.txt", "content": "new"}
    ))
    assert res.success is False
    assert "already exists" in res.error

def test_write_file(temp_workspace):
    executor, workspace_path = temp_workspace
    (workspace_path / "target.py").write_text("x = 1", encoding="utf-8")

    res = executor.execute(ActionRequest(
        action=ActionType.WRITE_FILE,
        params={"path": "target.py", "content": "x = 2\ny = 3"}
    ))
    assert res.success is True
    assert (workspace_path / "target.py").read_text(encoding="utf-8") == "x = 2\ny = 3"

def test_delete_file(temp_workspace):
    executor, workspace_path = temp_workspace
    (workspace_path / "obsolete.txt").write_text("delete me", encoding="utf-8")
    assert (workspace_path / "obsolete.txt").exists()

    res = executor.execute(ActionRequest(
        action=ActionType.DELETE_FILE,
        params={"path": "obsolete.txt"}
    ))
    assert res.success is True
    assert not (workspace_path / "obsolete.txt").exists()

def test_delete_nonexistent_file(temp_workspace):
    executor, _ = temp_workspace
    res = executor.execute(ActionRequest(
        action=ActionType.DELETE_FILE,
        params={"path": "does_not_exist.txt"}
    ))
    assert res.success is False
    assert "not found" in res.error

# Security Restrictions Tests

def test_reject_absolute_paths(temp_workspace):
    executor, _ = temp_workspace
    # Windows drive
    res_win = executor.execute(ActionRequest(
        action=ActionType.READ_FILE,
        params={"path": "C:\\Windows\\System32\\drivers\\etc\\hosts"}
    ))
    assert res_win.success is False
    assert "Absolute paths are prohibited" in res_win.error

    # POSIX slash
    res_posix = executor.execute(ActionRequest(
        action=ActionType.READ_FILE,
        params={"path": "/etc/passwd"}
    ))
    assert res_posix.success is False
    assert "Absolute paths are prohibited" in res_posix.error

def test_reject_path_traversal(temp_workspace):
    executor, _ = temp_workspace
    res = executor.execute(ActionRequest(
        action=ActionType.READ_FILE,
        params={"path": "../../backend/app/main.py"}
    ))
    assert res.success is False
    assert "Path traversal" in res.error

def test_reject_windows_path_traversal(temp_workspace):
    executor, _ = temp_workspace
    res = executor.execute(ActionRequest(
        action=ActionType.READ_FILE,
        params={"path": "..\\..\\secret.env"}
    ))
    assert res.success is False
    assert "Path traversal" in res.error

def test_reject_null_bytes(temp_workspace):
    executor, _ = temp_workspace
    res = executor.execute(ActionRequest(
        action=ActionType.READ_FILE,
        params={"path": "file.txt\0.hack"}
    ))
    assert res.success is False
    assert "Null bytes are prohibited" in res.error

def test_reject_deleting_workspace_root(temp_workspace):
    executor, _ = temp_workspace
    res = executor.execute(ActionRequest(
        action=ActionType.DELETE_FILE,
        params={"path": ""}
    ))
    assert res.success is False

def test_reject_arbitrary_shell_in_tests(temp_workspace):
    executor, _ = temp_workspace
    # Trying to pass flags or command injection
    res = executor.execute(ActionRequest(
        action=ActionType.RUN_TESTS,
        params={"target": "-k test_app"}
    ))
    assert res.success is False
    assert "Invalid test target specification" in res.error

    res2 = executor.execute(ActionRequest(
        action=ActionType.RUN_TESTS,
        params={"target": "test_app.py; rm -rf /"}
    ))
    assert res2.success is False
    assert "Invalid test target specification" in res2.error

def test_file_size_limit(temp_workspace):
    executor, _ = temp_workspace
    huge_content = "A" * 20000  # Exceeds max_file_size_bytes (10,000)
    res = executor.execute(ActionRequest(
        action=ActionType.WRITE_FILE,
        params={"path": "huge.txt", "content": huge_content}
    ))
    assert res.success is False
    assert "exceeds maximum limit" in res.error

def test_demo_workspace_tests_execution():
    """Verify that run_tests executes the actual demo_workspace and catches the intentional failure."""
    executor = WorkspaceExecutor(workspace_dir=settings.workspace_dir)

    # 1. Verify app.py and test_app.py are present
    list_res = executor.execute(ActionRequest(action=ActionType.LIST_FILES, params={"path": ""}))
    assert list_res.success is True
    filenames = [item["name"] for item in list_res.data]
    assert "app.py" in filenames
    assert "test_app.py" in filenames

    # 2. Run the tests
    test_res = executor.execute(ActionRequest(
        action=ActionType.RUN_TESTS,
        params={"target": "test_app.py"}
    ))
    assert test_res.success is True
    # The intentional bug in demo_workspace/app.py causes the test suite to fail
    assert test_res.exit_code != 0
    assert test_res.data["passed"] is False
    assert "FAILED (failures=3)" in test_res.data["output"]

