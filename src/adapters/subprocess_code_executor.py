"""
This module contains a function that takes as input a str object which contains the generated python code from the LLM to be executed in a separate process

Requirements:
    - enforce execution timeout
    - restrict filesystem access to temporary working directory (for safety)
    - prevent external network access (the generated script should not be able to access the network)

 """
from pathlib import Path
import tempfile
import subprocess
import sys
import uuid
import pydantic
import shutil
import argparse
import time
from src.domain.models import ExecutionResult
from src.config import SUPPORTED_DATA_EXTENSIONS, EXECUTION_TIMEOUT_SECONDS
from src.ports.code_executor_port import CodeExecutorPort

class SubprocessCodeExecutor(CodeExecutorPort):

    def execute_code(self, code: str, input_data_path: Path) -> ExecutionResult:
        # input validation
        # here is important to not raise exceptions because the ReAct loop can use these as observations and retry
        if not isinstance(code, str):
            return ExecutionResult(
                success = False,
                stderr = "Code must be a string.",
                exit_code = None
            )
        if not code.strip():
            return ExecutionResult(
                success = False,
                stderr = "Received empty code string.",
                exit_code = None
            )
        
        # generation of temporary working directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # copy the input file to this temporary working directory
            tmp_path = Path(tmp_dir)
            print("This is the path to the created temporary directory: ", tmp_path)
            sandbox_data_path = self._prepare_input_data_in_sandbox(input_data_path, tmp_path)

            # now i have both the temporary directory and the temporary copy of the input file data
            # the next step is to save the python script from the llm into a temp .py file
            script_path = tmp_path / "script.py"
            # first we have to clean and ensure that the code given by the LLM is ready to be saved and executed
            cleaned_code = self._clean_generated_code(code)
            # add network access block 
            NETWORK_BLOCKING_CODE = """
import socket

def _blocked_network_call(*args, **kwargs):
    raise RuntimeError("Network access is disabled in the sandbox.")

    socket.socket = _blocked_network_call
    socket.create_connection = _blocked_network_call
"""
            # save the code in the temporary script
            script_path.write_text(
                NETWORK_BLOCKING_CODE + "\n\n" + cleaned_code,
                encoding="utf-8",
            )
            # execute the script into subprocess
            start_time = time.perf_counter()
            try:
                completed_process = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd = tmp_path,
                    capture_output = True,
                    text = True,
                    timeout = EXECUTION_TIMEOUT_SECONDS,
                )

                execution_time = time.perf_counter() - start_time
                # very important, after execution we need to check wheter the html files have been stored
                # because otherwise if are store in the temporary directory we will lose them after this function returns.
                # to identify these files, we don't know which path has written the LLM in the python code, but we know for sure that the script
                # has been executed from the temporary directory, so any relative path will be inside the temp directory

                persistent_outputs = []

                outputs_dir = Path("outputs")
                outputs_dir.mkdir(parents=True, exist_ok=True)

                for html_file in tmp_path.rglob("*.html"):
                    unique_name = f"{int(time.time())}_{html_file.name}"
                    persistent_path = outputs_dir / unique_name

                    shutil.copy2(html_file, persistent_path)
                    persistent_outputs.append(persistent_path.resolve())

                return ExecutionResult(
                    success = completed_process.returncode == 0,
                    stdout = completed_process.stdout,
                    stderr = completed_process.stderr,
                    exit_code = completed_process.returncode,
                    generated_files = persistent_outputs,
                    execution_time_seconds = execution_time,
                    timed_out = False,
                )
            except subprocess.TimeoutExpired as e:
                 execution_time - time.perf_counter() - start_time
                 return ExecutionResult(
                         success = False,
                         stdout = e.stdout or "",
                         stderr = f"Execution timed out after {EXECUTION_TIMEOUT_SECONDS} seconds.",
                         exit_code = None,
                         generated_files = list(tmp_path.glob("*.html")),
                         execution_time_seconds = execution_time,
                         timed_out = True,
                 )
                
    def _prepare_input_data_in_sandbox(self, input_data_path: Path, tmp_path: Path) -> Path:

        input_data_path = input_data_path.resolve()

        if not input_data_path.exists():
            raise FileNotFoundError(f"Input file path not found: {input_data_path}")
        if not input_data_path.is_file():
            raise ValueError(f"Dataset path is not a file: {input_data_path}")

        suffix = input_data_path.suffix.lower()

        if suffix not in SUPPORTED_DATA_EXTENSIONS:
            raise ValueError(
                f"Unsupported dataset format '{suffix}'. "
                f"Supported formats are: {SUPPORTED_DATA_EXTENSIONS}"
            )

        sandbox_data_path = tmp_path / f"input{suffix}"
        shutil.copy2(input_data_path, sandbox_data_path)
        return sandbox_data_path

    def _clean_generated_code(self, code: str) -> str:
        # remove markdown fences
        # skip extra whitespaces
        code = code.strip()
        if code.startswith("```python"):
            code = code.removeprefix("```python")

        if code.startswith("```"):
            code = code.removeprefix("```")

        if code.endswith("```"):
            code = code.removesuffix("```")

        return code.strip()




