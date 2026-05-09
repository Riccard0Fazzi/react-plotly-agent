import requests
from src.config import LLM_TIMEOUT_SECONDS, DEFAULT_OLLAMA_MODEL
class OllamaLLMAdapter:
    def __init__(
        self,
        base_url: str = "http://localhost:11435",
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
                    "temperature": 0.1,
                    "num_predict": 700,
                },
            },
            timeout=self.timeout_seconds,
        )
        return response.json()["message"]["content"]
