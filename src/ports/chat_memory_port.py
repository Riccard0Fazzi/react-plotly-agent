# src/ports/chat_memory_port.py

import abc

class ChatMemoryPort(abc.ABC):
    
    @abc.abstractmethod
    def create_conversation(self, conversation_id: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def save_message(
            self,
            conversation_id: str,
            role: str,
            content: str,
            metadata: dict | None = None,
    ) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def load_messages(self, conversation_id: str) -> list[dict[str,str]]:
        raise NotImplementedError
    
