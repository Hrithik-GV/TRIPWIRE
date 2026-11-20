from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.schemas.actions import (
    ActionRequest,
    ActionResult,
    ActionType,
    ListFilesParams,
    RunTestsParams,
)
from app.services.executor import WorkspaceExecutor

router = APIRouter(prefix="/api/actions", tags=["Actions"])

# Singleton or factory for executor
executor = WorkspaceExecutor()

@router.post("/execute", response_model=ActionResult)
def execute_action(request: ActionRequest) -> ActionResult:
    """Execute a controlled agent action inside the protected workspace."""
    result = executor.execute(request)
    return result

@router.post("/run-tests", response_model=ActionResult)
def run_tests_endpoint(target: Optional[str] = Query(default=None)) -> ActionResult:
    """Convenience endpoint to trigger the permitted unit test suite."""
    request = ActionRequest(
        action=ActionType.RUN_TESTS,
        params={"target": target} if target else {},
    )
    return executor.execute(request)

@router.get("/files", response_model=ActionResult)
def list_workspace_files(path: Optional[str] = Query(default="")) -> ActionResult:
    """Convenience endpoint to list files in the protected workspace."""
    request = ActionRequest(
        action=ActionType.LIST_FILES,
        params={"path": path or ""},
    )
    return executor.execute(request)

