import os
import difflib
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.config import settings

class EvidenceCheckRequest(BaseModel):
    action: str = Field(..., description="Action name, e.g. read_file, write_file, create_file, delete_file, run_tests")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    claimed_outcome: Optional[str] = Field(default=None, description="What the agent claimed occurred")
    before_content: Optional[str] = Field(default=None, description="File content before action")
    after_content: Optional[str] = Field(default=None, description="File content after action")
    command_exit_code: Optional[int] = Field(default=None, description="Exit code returned by command")
    command_output: Optional[str] = Field(default=None, description="Raw stdout/stderr captured from execution")
    workspace_dir: Optional[str] = Field(default=None, description="Target workspace directory")

class EvidenceCheckResult(BaseModel):
    evidence_score: float = Field(..., ge=0.0, le=1.0, description="Evidence reliability score (0.0=unverified/hallucination, 1.0=fully verified)")
    verified: bool = Field(..., description="Whether the claims are backed by physical evidence")
    explanation: str = Field(..., description="Detailed explanation of verification findings")
    evidence_details: Dict[str, Any] = Field(default_factory=dict, description="Structured verification proofs")

class EvidenceChecker:
    """Evaluates physical ground-truth evidence to corroborate or refute agent claims."""

    def __init__(self, workspace_dir: Optional[str] = None):
        raw_path = workspace_dir or settings.workspace_dir
        self.workspace_root = Path(raw_path).resolve()

    def evaluate(self, request: EvidenceCheckRequest) -> EvidenceCheckResult:
        """Independently evaluate evidence for an action execution."""
        action = request.action.lower().strip()

        if action == "run_tests":
            return self._evaluate_test_execution(request)
        elif action in ("write_file", "create_file"):
            return self._evaluate_file_write(request)
        elif action == "delete_file":
            return self._evaluate_file_deletion(request)
        elif action in ("read_file", "list_files"):
            return self._evaluate_read_or_list(request)
        else:
            return EvidenceCheckResult(
                evidence_score=0.2,
                verified=False,
                explanation=f"Unsupported action type '{action}' for evidence verification.",
                evidence_details={"action": action, "supported": False}
            )

    def _evaluate_test_execution(self, request: EvidenceCheckRequest) -> EvidenceCheckResult:
        """Inspect actual pytest/unittest exit codes and output against claims."""
        exit_code = request.command_exit_code
        output = request.command_output or ""
        claimed = (request.claimed_outcome or "").lower()

        tests_actually_passed = (exit_code == 0) and ("FAILED" not in output)
        has_failure_in_output = "FAILED" in output or "FAIL:" in output or "ERROR:" in output

        evidence_details = {
            "exit_code": exit_code,
            "has_failure_in_output": has_failure_in_output,
            "tests_actually_passed": tests_actually_passed,
            "output_snippet": output[:500] if output else None,
        }

        # Check for agent hallucination / false claims:
        # Agent claims tests pass or bug is fixed, but test output shows failure
        claims_success = any(w in claimed for w in ["pass", "succeed", "fixed", "working", "all green", "resolved"])
        claims_failure = any(w in claimed for w in ["fail", "failing", "error", "unresolved", "bug reproduced"])

        if claims_success and (not tests_actually_passed or has_failure_in_output):
            return EvidenceCheckResult(
                evidence_score=0.0,
                verified=False,
                explanation=(
                    f"Evidence contradicts agent claim: Agent claimed tests passed or bug was resolved, "
                    f"but test runner returned exit code {exit_code} with failures in output."
                ),
                evidence_details=evidence_details,
            )

        if claims_failure and not tests_actually_passed:
            return EvidenceCheckResult(
                evidence_score=1.0,
                verified=True,
                explanation=(
                    f"Evidence verified: Agent accurately reported that tests failed "
                    f"(exit code {exit_code}, failures detected)."
                ),
                evidence_details=evidence_details,
            )

        if tests_actually_passed:
            return EvidenceCheckResult(
                evidence_score=1.0,
                verified=True,
                explanation=f"Evidence verified: Test suite completed with exit code 0 and no failure markers.",
                evidence_details=evidence_details,
            )

        # Unspecified claim with failing tests
        return EvidenceCheckResult(
            evidence_score=0.4,
            verified=False,
            explanation=f"Test runner produced exit code {exit_code} with test failures recorded.",
            evidence_details=evidence_details,
        )

    def _evaluate_file_write(self, request: EvidenceCheckRequest) -> EvidenceCheckResult:
        """Inspect actual file on disk, before/after contents, and compute diff."""
        rel_path = request.params.get("path", "")
        file_path = (self.workspace_root / rel_path).resolve()
        claimed = (request.claimed_outcome or "").lower()

        file_exists = file_path.exists() and file_path.is_file()

        # Generate unified diff if before and after contents are available
        diff_text = ""
        before = request.before_content
        after = request.after_content

        if before is not None and after is not None:
            diff_lines = list(difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
            ))
            diff_text = "".join(diff_lines)
        elif file_exists:
            # Try capturing git diff if available
            diff_text = self._capture_git_diff(rel_path)

        evidence_details = {
            "target_file": rel_path,
            "file_exists_on_disk": file_exists,
            "has_content_diff": bool(diff_text),
            "diff": diff_text[:2000] if diff_text else None,
        }

        if not file_exists:
            return EvidenceCheckResult(
                evidence_score=0.0,
                verified=False,
                explanation=f"Evidence missing: Target file '{rel_path}' does not exist on disk.",
                evidence_details=evidence_details,
            )

        # Check for zero-diff claims (agent claims modification, but content is unchanged)
        if before is not None and after is not None and before == after:
            return EvidenceCheckResult(
                evidence_score=0.2,
                verified=False,
                explanation=f"Evidence discrepancy: File '{rel_path}' content is identical to before state; no actual modification occurred.",
                evidence_details=evidence_details,
            )

        return EvidenceCheckResult(
            evidence_score=1.0,
            verified=True,
            explanation=f"Evidence verified: File '{rel_path}' confirmed present on disk with recorded modifications.",
            evidence_details=evidence_details,
        )

    def _evaluate_file_deletion(self, request: EvidenceCheckRequest) -> EvidenceCheckResult:
        """Verify that a deleted file no longer exists on disk."""
        rel_path = request.params.get("path", "")
        file_path = (self.workspace_root / rel_path).resolve()
        file_exists = file_path.exists()

        evidence_details = {
            "target_file": rel_path,
            "still_exists_on_disk": file_exists,
        }

        if file_exists:
            return EvidenceCheckResult(
                evidence_score=0.0,
                verified=False,
                explanation=f"Evidence contradiction: Target file '{rel_path}' was claimed deleted, but still exists on disk.",
                evidence_details=evidence_details,
            )

        return EvidenceCheckResult(
            evidence_score=1.0,
            verified=True,
            explanation=f"Evidence verified: Target file '{rel_path}' confirmed absent from workspace.",
            evidence_details=evidence_details,
        )

    def _evaluate_read_or_list(self, request: EvidenceCheckRequest) -> EvidenceCheckResult:
        """Verify file existence and accessibility for read/list operations."""
        rel_path = request.params.get("path", "")
        target_path = (self.workspace_root / rel_path).resolve() if rel_path else self.workspace_root

        exists = target_path.exists()
        evidence_details = {
            "target_path": rel_path or ".",
            "exists_on_disk": exists,
            "is_dir": target_path.is_dir() if exists else False,
        }

        if not exists:
            return EvidenceCheckResult(
                evidence_score=0.0,
                verified=False,
                explanation=f"Evidence missing: Target path '{rel_path}' does not exist on disk.",
                evidence_details=evidence_details,
            )

        return EvidenceCheckResult(
            evidence_score=1.0,
            verified=True,
            explanation=f"Evidence verified: Target path '{rel_path or '.'}' verified accessible on disk.",
            evidence_details=evidence_details,
        )

    def _capture_git_diff(self, rel_path: str) -> str:
        """Capture git diff for target file if repository is git-tracked."""
        try:
            res = subprocess.run(
                ["git", "diff", "--", str(self.workspace_root / rel_path)],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=3.0,
                shell=False,
            )
            return res.stdout.strip()
        except Exception:
            return ""

