from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ActionType(str, Enum):
    LIST_FILES = "list_files"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    CREATE_FILE = "create_file"
    DELETE_FILE = "delete_file"
    RUN_TESTS = "run_tests"

class ListFilesParams(BaseModel):
    path: Optional[str] = Field(default="", description="Relative directory path to list")

class ReadFileParams(BaseModel):
    path: str = Field(..., description="Relative path of file to read")

class WriteFileParams(BaseModel):
    path: str = Field(..., description="Relative path of file to write")
    content: str = Field(..., description="Content to write to file")

class CreateFileParams(BaseModel):
    path: str = Field(..., description="Relative path of file to create")
    content: Optional[str] = Field(default="", description="Initial content for the created file")

class DeleteFileParams(BaseModel):
    path: str = Field(..., description="Relative path of file to delete")

class RunTestsParams(BaseModel):
    target: Optional[str] = Field(default=None, description="Optional relative test module (e.g. test_app.py)")

class ActionRequest(BaseModel):
    action: ActionType
    params: Dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")

class FileItem(BaseModel):
    name: str
    path: str
    is_directory: bool
    size_bytes: int
    modified_time: float

class TestRunResult(BaseModel):
    passed: bool
    exit_code: int
    output: str
    error: Optional[str] = None
    target: Optional[str] = None
    timed_out: bool = False

class ActionResult(BaseModel):
    success: bool
    action: ActionType
    data: Optional[Any] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time_ms: Optional[float] = None
    timestamp: str

