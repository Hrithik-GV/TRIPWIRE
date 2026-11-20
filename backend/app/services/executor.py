import os
import sys
import re
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from app.config import settings
from app.schemas.actions import (
    ActionType,
    ActionRequest,
    ActionResult,
    ListFilesParams,
    ReadFileParams,
    WriteFileParams,
    CreateFileParams,
    DeleteFileParams,
    RunTestsParams,
    FileItem,
    TestRunResult,
)

class SecurityError(Exception):
    """Raised when an operation violates workspace security boundaries."""
    pass

class WorkspaceExecutor:
    """Controlled action execution engine restricted to a designated workspace."""

    def __init__(
        self,
        workspace_dir: Optional[str] = None,
        command_timeout_seconds: Optional[float] = None,
        max_output_chars: Optional[int] = None,
        max_file_size_bytes: Optional[int] = None,
    ):
        raw_path = workspace_dir or settings.workspace_dir
        self.workspace_root = Path(raw_path).resolve()
        self.command_timeout_seconds = command_timeout_seconds or settings.command_timeout_seconds
        self.max_output_chars = max_output_chars or settings.max_output_chars
        self.max_file_size_bytes = max_file_size_bytes or settings.max_file_size_bytes

        # Ensure the workspace directory exists
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def resolve_safe_path(
        self,
        rel_path: str,
        allow_root: bool = False,
        must_exist: bool = False,
    ) -> Path:
        """Validate and resolve a relative path strictly within the workspace root.
        
        Rejects:
        - Absolute paths (POSIX and Windows drives)
        - Path traversal sequences ('..')
        - Null bytes
        - Symlink escapes
        """
        if rel_path is None:
            raise SecurityError("Path must not be None")

        cleaned = str(rel_path).strip()

        if "\0" in cleaned:
            raise SecurityError("Null bytes are prohibited in paths")

        if not cleaned:
            if allow_root:
                return self.workspace_root
            raise SecurityError("Path must not be empty")

        # Reject absolute paths (POSIX '/' or Windows 'C:' or leading slashes)
        if (
            Path(cleaned).is_absolute()
            or os.path.isabs(cleaned)
            or cleaned.startswith(("/", "\\"))
            or bool(re.match(r"^[a-zA-Z]:", cleaned))
        ):
            raise SecurityError(f"Absolute paths are prohibited: '{rel_path}'")

        # Check for path traversal components
        path_parts = Path(cleaned).parts
        if ".." in path_parts or any(p.strip() == ".." for p in path_parts):
            raise SecurityError(f"Path traversal ('..') is prohibited: '{rel_path}'")

        # Construct and resolve candidate path
        candidate = (self.workspace_root / cleaned).resolve()

        # Boundary check against workspace root
        if not candidate.is_relative_to(self.workspace_root):
            raise SecurityError(f"Path '{rel_path}' escapes workspace boundary")

        # Symlink escape verification: verify all parent segments
        current = candidate
        while current != self.workspace_root and current != current.parent:
            if current.is_symlink():
                resolved_link = current.resolve()
                if not resolved_link.is_relative_to(self.workspace_root):
                    raise SecurityError(f"Symlink escape detected in '{rel_path}'")
            current = current.parent

        if must_exist and not candidate.exists():
            raise FileNotFoundError(f"File or directory not found: '{rel_path}'")

        return candidate

    def execute(self, request: ActionRequest) -> ActionResult:
        """Route and execute a validated action request."""
        start_time = time.perf_counter()
        action = request.action
        params = request.params or {}

        try:
            if action == ActionType.LIST_FILES:
                parsed_params = ListFilesParams(**params)
                data = self.list_files(parsed_params)
                exit_code = 0
            elif action == ActionType.READ_FILE:
                parsed_params = ReadFileParams(**params)
                data = self.read_file(parsed_params)
                exit_code = 0
            elif action == ActionType.WRITE_FILE:
                parsed_params = WriteFileParams(**params)
                data = self.write_file(parsed_params)
                exit_code = 0
            elif action == ActionType.CREATE_FILE:
                parsed_params = CreateFileParams(**params)
                data = self.create_file(parsed_params)
                exit_code = 0
            elif action == ActionType.DELETE_FILE:
                parsed_params = DeleteFileParams(**params)
                data = self.delete_file(parsed_params)
                exit_code = 0
            elif action == ActionType.RUN_TESTS:
                parsed_params = RunTestsParams(**params)
                test_result = self.run_tests(parsed_params)
                data = test_result.model_dump()
                exit_code = test_result.exit_code
            else:
                raise ValueError(f"Unsupported action: {action}")

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ActionResult(
                success=True,
                action=action,
                data=data,
                exit_code=exit_code,
                execution_time_ms=round(elapsed_ms, 2),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ActionResult(
                success=False,
                action=action,
                error=str(exc),
                exit_code=1,
                execution_time_ms=round(elapsed_ms, 2),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    def list_files(self, params: ListFilesParams) -> List[Dict[str, Any]]:
        """List files and directories in the target workspace directory."""
        target_dir = self.resolve_safe_path(params.path or "", allow_root=True, must_exist=True)

        if not target_dir.is_dir():
            raise NotADirectoryError(f"Path is not a directory: '{params.path}'")

        items: List[Dict[str, Any]] = []
        for entry in sorted(target_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            # Skip hidden files or caches
            if entry.name == "__pycache__" or entry.name.startswith("."):
                continue

            rel_entry_path = str(entry.relative_to(self.workspace_root)).replace("\\", "/")
            stat = entry.stat()
            file_item = FileItem(
                name=entry.name,
                path=rel_entry_path,
                is_directory=entry.is_dir(),
                size_bytes=0 if entry.is_dir() else stat.st_size,
                modified_time=stat.st_mtime,
            )
            items.append(file_item.model_dump())

        return items

    def read_file(self, params: ReadFileParams) -> Dict[str, Any]:
        """Read text content from a file inside the workspace."""
        file_path = self.resolve_safe_path(params.path, allow_root=False, must_exist=True)

        if file_path.is_dir():
            raise IsADirectoryError(f"Cannot read directory as file: '{params.path}'")

        size = file_path.stat().st_size
        if size > self.max_file_size_bytes:
            raise ValueError(
                f"File size ({size} bytes) exceeds maximum limit ({self.max_file_size_bytes} bytes)"
            )

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        rel_path = str(file_path.relative_to(self.workspace_root)).replace("\\", "/")
        return {
            "path": rel_path,
            "content": content,
            "size_bytes": size,
            "lines": len(content.splitlines()),
        }

    def write_file(self, params: WriteFileParams) -> Dict[str, Any]:
        """Write text content to a file inside the workspace (overwrites existing)."""
        file_path = self.resolve_safe_path(params.path, allow_root=False, must_exist=False)

        encoded = params.content.encode("utf-8")
        if len(encoded) > self.max_file_size_bytes:
            raise ValueError(
                f"Content size ({len(encoded)} bytes) exceeds maximum limit ({self.max_file_size_bytes} bytes)"
            )

        # Ensure parent directory exists within workspace
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(params.content)

        rel_path = str(file_path.relative_to(self.workspace_root)).replace("\\", "/")
        return {
            "path": rel_path,
            "bytes_written": len(encoded),
            "lines": len(params.content.splitlines()),
        }

    def create_file(self, params: CreateFileParams) -> Dict[str, Any]:
        """Create a new file inside the workspace; fails if file already exists."""
        file_path = self.resolve_safe_path(params.path, allow_root=False, must_exist=False)

        if file_path.exists():
            raise FileExistsError(f"File already exists: '{params.path}'")

        content = params.content or ""
        encoded = content.encode("utf-8")
        if len(encoded) > self.max_file_size_bytes:
            raise ValueError(
                f"Content size ({len(encoded)} bytes) exceeds maximum limit ({self.max_file_size_bytes} bytes)"
            )

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        rel_path = str(file_path.relative_to(self.workspace_root)).replace("\\", "/")
        return {
            "path": rel_path,
            "created": True,
            "bytes_written": len(encoded),
        }

    def delete_file(self, params: DeleteFileParams) -> Dict[str, Any]:
        """Delete a file or empty directory inside the workspace."""
        target_path = self.resolve_safe_path(params.path, allow_root=False, must_exist=True)

        if target_path == self.workspace_root:
            raise SecurityError("Cannot delete workspace root directory")

        rel_path = str(target_path.relative_to(self.workspace_root)).replace("\\", "/")

        if target_path.is_file() or target_path.is_symlink():
            target_path.unlink()
        elif target_path.is_dir():
            target_path.rmdir()
        else:
            raise FileNotFoundError(f"Target not found: '{params.path}'")

        return {
            "path": rel_path,
            "deleted": True,
        }

    def run_tests(self, params: RunTestsParams) -> TestRunResult:
        """Run the permitted test suite inside the workspace without invoking arbitrary shell commands.
        
        Only python -m unittest is permitted. Shell is strictly False.
        """
        # Determine Python executable
        python_bin = sys.executable

        # Prepare strictly fixed command list (NO arbitrary shell invocation)
        cmd: List[str] = [python_bin, "-m", "unittest"]

        target_file = None
        if params.target:
            cleaned_target = params.target.strip()
            # Ensure target is a valid test file name without command flags or shell characters
            if cleaned_target.startswith("-") or not re.match(r"^[a-zA-Z0-9_\-\./\\]+\.py$", cleaned_target):
                raise SecurityError(f"Invalid test target specification: '{params.target}'")

            target_path = self.resolve_safe_path(cleaned_target, allow_root=False, must_exist=True)
            target_file = str(target_path.relative_to(self.workspace_root)).replace("\\", "/")
            cmd.append(target_file)
        else:
            cmd.extend(["discover", "-s", str(self.workspace_root), "-p", "*test*.py"])

        try:
            process = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=self.command_timeout_seconds,
                shell=False,  # CRITICAL: Prevent shell injection
            )

            # Combine stdout and stderr (unittest outputs test summaries on stderr)
            combined_output = (process.stdout or "") + ("\n" if process.stdout and process.stderr else "") + (process.stderr or "")

            # Truncate if exceeds output limit
            if len(combined_output) > self.max_output_chars:
                combined_output = (
                    combined_output[: self.max_output_chars]
                    + f"\n[TRIPWIRE WARNING: Output truncated after {self.max_output_chars} characters]"
                )

            passed = (process.returncode == 0)
            return TestRunResult(
                passed=passed,
                exit_code=process.returncode,
                output=combined_output,
                target=target_file,
                timed_out=False,
            )

        except subprocess.TimeoutExpired as exc:
            partial_out = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            return TestRunResult(
                passed=False,
                exit_code=-1,
                output=partial_out,
                error=f"Execution timed out after {self.command_timeout_seconds} seconds",
                target=target_file,
                timed_out=True,
            )
        except Exception as exc:
            return TestRunResult(
                passed=False,
                exit_code=-1,
                output="",
                error=str(exc),
                target=target_file,
                timed_out=False,
            )
