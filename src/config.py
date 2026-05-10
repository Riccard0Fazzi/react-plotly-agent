# src/config.py

"""
Central configuration for the React Plotly Agent.

These values are intentionally kept simple for local reproducibility.
For a production system, secrets and environment-specific values should be
loaded from environment variables or a dedicated configuration layer.
"""

SUPPORTED_DATA_EXTENSIONS = {".csv", ".xlsx", ".json"}

# Code execution limits
EXECUTION_TIMEOUT_SECONDS = 30

# LLM configuration
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:3b"
LLM_TIMEOUT_SECONDS = 1000

# Limit the amount of execution output passed back to the LLM.
# This prevents long stdout/stderr traces from making the prompt too large,
# which is especially important when running local models.
MAX_STDOUT_CHARS = 1000
MAX_STDERR_CHARS = 2000

# Neo4j local development configuration.
# These values match the credentials defined in docker-compose.yml:
# NEO4J_AUTH=neo4j/password
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"