import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class RiskCheckRequest(BaseModel):
    action: str = Field(..., description="Action name (e.g. read_file, write_file, create_file, delete_file, run_tests, or arbitrary)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the action")
    content_length: Optional[int] = Field(default=None, description="Size of content to write in bytes")

class RiskCheckResult(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk severity score from 0.0 (benign) to 1.0 (critical/destructive)")
    risk_level: str = Field(..., description="Risk tier: 'low', 'medium', 'high', 'critical'")
    is_reversible: bool = Field(..., description="Whether this action can be trivially undone without snapshot rollback")
    explanation: str = Field(..., description="Justification for risk classification")
    impact_scope: str = Field(..., description="Blast radius and scope of impact")
    risk_factors: List[str] = Field(default_factory=list, description="Specific risk signals detected")

class RiskChecker:
    """Classifies operation risk based on action type, target criticality, reversibility, and blast radius."""

    CRITICAL_TARGET_PATTERNS = [
        r"^\.?env(\..+)?$",
        r"config\.py$",
        r"settings\.py$",
        r"\.git.*",
        r"\.bash.*",
        r"\.profile.*",
    ]

    CORE_CODE_FILES = ["app.py", "test_app.py", "main.py"]

    SUPPORTED_ACTIONS = {
        "list_files",
        "read_file",
        "write_file",
        "create_file",
        "delete_file",
        "run_tests",
    }

    def evaluate(self, request: RiskCheckRequest) -> RiskCheckResult:
        """Classify risk for a proposed operation."""
        action = request.action.lower().strip()
        params = request.params or {}
        raw_path = str(params.get("path") or params.get("target") or "").strip()
        norm_path = raw_path.replace("\\", "/").lower()

        # 1. Critical: Unsupported, arbitrary shell, or sandbox escape attempts
        if action not in self.SUPPORTED_ACTIONS:
            return RiskCheckResult(
                risk_score=0.95,
                risk_level="critical",
                is_reversible=False,
                explanation=f"Unsupported or arbitrary operation '{action}'. Destructive/unregistered actions are critical risk.",
                impact_scope="unauthorized_execution",
                risk_factors=["unregistered_action_type", "potential_arbitrary_execution"],
            )

        if ".." in norm_path or norm_path.startswith("/") or bool(re.match(r"^[a-zA-Z]:", raw_path)):
            return RiskCheckResult(
                risk_score=1.00,
                risk_level="critical",
                is_reversible=False,
                explanation=f"Path traversal or absolute path target '{raw_path}' detected. Sandbox escape attempt.",
                impact_scope="sandbox_escape_attempt",
                risk_factors=["path_traversal", "sandbox_boundary_violation"],
            )

        # 2. Deletions (High Risk)
        if action == "delete_file":
            if not raw_path or norm_path in (".", "./", "*"):
                return RiskCheckResult(
                    risk_score=1.00,
                    risk_level="critical",
                    is_reversible=False,
                    explanation="Mass deletion or workspace root deletion attempt.",
                    impact_scope="workspace_destruction",
                    risk_factors=["root_deletion_attempt", "catastrophic_blast_radius"],
                )

            is_core = any(core in norm_path for core in self.CORE_CODE_FILES)
            risk_score = 0.85 if is_core else 0.75
            factors = ["file_deletion", "permanent_data_loss_without_snapshot"]
            if is_core:
                factors.append("core_code_destruction")

            return RiskCheckResult(
                risk_score=risk_score,
                risk_level="high",
                is_reversible=False,
                explanation=f"File deletion of '{raw_path}' permanently destroys data unless rolled back via snapshot.",
                impact_scope="core_file_deletion" if is_core else "file_deletion",
                risk_factors=factors,
            )

        # 3. File modifications (Medium to High Risk)
        if action == "write_file":
            is_sensitive_config = any(re.search(pat, Path(norm_path).name) for pat in self.CRITICAL_TARGET_PATTERNS)
            if is_sensitive_config:
                return RiskCheckResult(
                    risk_score=0.70,
                    risk_level="high",
                    is_reversible=True,
                    explanation=f"Modifying sensitive configuration/environment file '{raw_path}'.",
                    impact_scope="environment_configuration_mutation",
                    risk_factors=["sensitive_config_modification", "environment_alteration"],
                )

            return RiskCheckResult(
                risk_score=0.45,
                risk_level="medium",
                is_reversible=True,
                explanation=f"Modifying existing file '{raw_path}'. Mutates workspace code.",
                impact_scope="file_content_modification",
                risk_factors=["code_modification", "reversible_via_snapshot"],
            )

        if action == "create_file":
            return RiskCheckResult(
                risk_score=0.35,
                risk_level="medium",
                is_reversible=True,
                explanation=f"Creating new file '{raw_path}'. Adds workspace artifact.",
                impact_scope="file_creation",
                risk_factors=["workspace_addition", "reversible_by_deletion"],
            )

        # 4. Tests and Reads (Low Risk)
        if action == "run_tests":
            return RiskCheckResult(
                risk_score=0.20,
                risk_level="low",
                is_reversible=True,
                explanation="Executing predefined, sandboxed test suite without mutating files.",
                impact_scope="sandboxed_test_execution",
                risk_factors=["read_only_execution", "process_sandboxing"],
            )

        if action == "read_file":
            is_sensitive = any(re.search(pat, Path(norm_path).name) for pat in self.CRITICAL_TARGET_PATTERNS)
            if is_sensitive:
                return RiskCheckResult(
                    risk_score=0.28,
                    risk_level="low",
                    is_reversible=True,
                    explanation=f"Reading sensitive file '{raw_path}'. Potential secret inspection.",
                    impact_scope="sensitive_read",
                    risk_factors=["sensitive_target_read"],
                )
            return RiskCheckResult(
                risk_score=0.10,
                risk_level="low",
                is_reversible=True,
                explanation=f"Read-only inspection of '{raw_path}'.",
                impact_scope="file_read",
                risk_factors=["read_only"],
            )

        if action == "list_files":
            return RiskCheckResult(
                risk_score=0.05,
                risk_level="low",
                is_reversible=True,
                explanation="Read-only directory listing. Zero state mutation.",
                impact_scope="metadata_read",
                risk_factors=["read_only", "zero_mutation"],
            )

        # Default fallback
        return RiskCheckResult(
            risk_score=0.50,
            risk_level="medium",
            is_reversible=False,
            explanation=f"Operation '{action}' with unclassified risk parameters.",
            impact_scope="unclassified_impact",
            risk_factors=["unclassified"],
        )

