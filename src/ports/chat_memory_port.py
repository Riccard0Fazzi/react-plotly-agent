# src/ports/chat_memory_port.py

import abc

class ChatMemoryPort:
    
    def create_conversation(self, conversation_id: str) -> None:
        raise NotImplementedError

    def save_message(
            self,
            conversation_id: str,
            role: str,
            content: str,
            metadata: dict | None = None,
    ) -> None:
        raise NotImplementedError
    
    def load_messages(self, conversation_id: str) -> list[dict[str,str]]:
        raise NotImplementedError
    
    def get_pasts_plots(self, conversation_id: str) -> list[str]:
        raise NotImplementedError