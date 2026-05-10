# src/adapters/neo4j_chat_memory_adapter.py
from neo4j import GraphDatabase
import json
from src.ports.chat_memory_port import ChatMemoryPort

class Neo4jChatMemoryAdapter(ChatMemoryPort):

    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def create_conversation(self, conversation_id: str) -> None:
        query = """
        MERGE (c:Conversation {id: $conversation_id})
        ON CREATE SET c.created_at = datetime()
        """

        with self.driver.session() as session:
            session.run(query, conversation_id = conversation_id)

    def save_message(
            self,
            conversation_id: str,
            role: str,
            content: str,
            metadata: dict | None = None,
    ) -> None:
        query = """
        MATCH (c:Conversation {id: $conversation_id})
        CREATE (m:Message {
            role: $role,
            content: $content,
            timestamp: datetime(),
            metadata: $metadata
        })
        CREATE (c)-[:HAS_MESSAGE]->(m)
        """
        with self.driver.session() as session:
            session.run(
                query,
                conversation_id=conversation_id,
                role=role,
                content=content,
                metadata=json.dumps(metadata or {}),
            )

    def load_messages(self, conversation_id: str) -> list[dict]:
        query = """
        MATCH (:Conversation {id: $conversation_id})-[:HAS_MESSAGE]->(m:Message)
        RETURN m.role AS role, m.content AS content
        ORDER BY m.timestamp ASC
        """

        with self.driver.session() as session:
            result = session.run(query, conversation_id=conversation_id)

            return [
                {
                    "role": record["role"],
                    "content": record["content"],
                }
                for record in result
            ]
