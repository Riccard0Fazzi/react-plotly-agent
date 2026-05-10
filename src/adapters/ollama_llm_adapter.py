# src/adapters/ollama_llm_adapter.py

import requests
from src.config import LLM_TIMEOUT_SECONDS, DEFAULT_OLLAMA_MODEL, BASE_URL_OLLAMA
from src.ports.llm_port import LLMPort

class OllamaLLMAdapter(LLMPort):
    def __init__(
        self,
        base_url: str = BASE_URL_OLLAMA,
        model: str = DEFAULT_OLLAMA_MODEL,
        timeout_seconds: int = LLM_TIMEOUT_SECONDS,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def chat(self, messages: list[dict[str, str]]) -> str:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": 500,
                    "num_ctx": 2048,
                },
            },
            timeout=self.timeout_seconds,
        )

        response.raise_for_status()

        data = response.json()

        if "message" not in data:
            raise RuntimeError(f"Unexpected Ollama response: {data}")

        return data["message"]["content"]
