# src/ports/code_executor_port.py

import abc
from pathlib import Path

from src.domain.models import ExecutionResult


class CodeExecutorPort(abc.ABC):

    @abc.abstractmethod
    def execute_code(self, code: str, input_data_path: Path) -> ExecutionResult:
        raise NotImplementedError