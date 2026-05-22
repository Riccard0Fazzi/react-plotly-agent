# src/ports/llm_port.py

import abc

class LLMPort(abc.ABC):

    @abc.abstractmethod
    def chat(self, messages: list[dict[str, str]]) -> str:
        pass