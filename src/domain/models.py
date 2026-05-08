"""

"""

from pydantic import BaseModel, Field 
from pathlib import Path

class ExecutionResult(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    generated_files: list[Path] = Field(default_factory=list) # to prevent different instances to access to the same list
    execution_time_seconds: float = 0.0
    timed_out: bool = False
