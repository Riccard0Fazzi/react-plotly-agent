


# React Plotly Agent

> Local AI agent for dataset analysis and autonomous Plotly visualization generation using a ReAct-style workflow.

---

## Demo — Persistent Memory with Neo4j

This demo shows the agent generating an initial Plotly chart, storing the conversation in Neo4j, and then using the same `conversation_id` to handle a follow-up request that refers to the previous chart context.



https://github.com/user-attachments/assets/b8ffa562-9789-4b07-8840-b31af1ce96dd



The interactive HTML charts generated during the demo are available in:

- `demo/outputs/color_pie_chart.html`
- `demo/outputs/color_histogram.html`
---
# Project Overview

This project implements a local AI agent capable of:

- analyzing tabular datasets,
- generating Python code,
- executing generated code inside a sandboxed environment,
- producing interactive Plotly visualizations as HTML files.

The system follows a ReAct-style workflow based on:

- reasoning,
- action selection,
- observation,
- iterative correction.

The implementation prioritizes:

- simplicity,
- modularity,
- local reproducibility,
- robustness,
- explainability of agent behavior.

---

# Main Features

- ReAct-style autonomous agent loop
- Dataset inspection and schema awareness
- Automatic Plotly chart generation
- Sandboxed Python execution
- Retry and self-correction mechanisms
- Dockerized local LLM inference through Ollama
- Neo4j-based conversation memory and persistence
- Interactive HTML dashboard generation
- Fully local execution (no cloud APIs)

---

# Architecture

The project follows a lightweight Ports & Adapters (Hexagonal/Clean Architecture-inspired) organization.

## Folder Structure

```text
src/
├── adapters/
├── ports/
├── use_cases/
├── domain/
```

---

# Ports Layer

The `ports/` layer defines abstract interfaces used by the application logic.

Examples:

- `LLMPort`
- `CodeExecutorPort`
- `ChatMemoryPort`

Purpose:

- decouple business logic from concrete implementations,
- allow adapter replacement without changing the agent logic,
- enforce dependency inversion.

Example:

```python
class CodeExecutorPort:
    def execute_code(
        self,
        code: str,
        input_data_path: Path
    ) -> ExecutionResult:
        raise NotImplementedError
```

The agent depends on abstractions rather than concrete implementations.

---

# Adapters Layer

The `adapters/` layer contains concrete implementations of the ports.

Current adapters:

- `OllamaLLMAdapter`
- `SubprocessCodeExecutor`
- `Neo4jChatMemoryAdapter`

Responsibilities:

- external communication,
- infrastructure handling,
- sandbox execution,
- persistence,
- HTTP communication.

---

# Use Cases Layer

The `use_cases/` layer contains the application orchestration logic.

Main component:

- `ReactChartAgent`

Responsibilities:

- maintain the ReAct loop,
- build prompts,
- parse actions,
- execute tools,
- handle retries,
- manage observations.

The agent does not directly depend on infrastructure details.

---

# Domain Layer

Contains shared domain models and data structures.

Current model:

- `ExecutionResult`

Purpose:

- centralize execution metadata,
- standardize communication between components.

---

# ReAct Agent Design

The agent follows a ReAct-inspired loop:

```text
Thought
Action
PAUSE
Observation
```

Supported actions:

- `inspect_dataset`
- `execute_python_code`
- `Answer`

---

# Dataset Inspection Strategy

A dedicated inspection step was introduced before code generation.

Purpose:

- reduce hallucinations,
- provide schema awareness,
- improve code generation reliability.

The inspection returns:

- dataset columns,
- data types,
- missing values.

---

# Retry and Recovery Strategies

Handled scenarios:

- invalid actions,
- missing Python code blocks,
- failed execution,
- missing HTML generation,
- invalid column names,
- runtime exceptions.

Strategy:

- execution errors are fed back to the LLM as observations,
- the model attempts self-correction,
- retries are bounded by `max_attempts`.

---

# Sandboxed Code Execution

Generated code is executed inside a restricted environment.

Implemented protections:

- execution in a separate subprocess,
- timeout enforcement,
- isolated temporary working directory,
- restricted filesystem scope,
- network access disabled.

---

# Local LLM Strategy

The system uses local inference through Ollama.

Reasons:

- offline execution,
- reproducibility,
- no API costs,
- portability.

Default model:

```text
qwen2.5-coder:3b
```

Alternative model:

```text
qwen2.5-coder:7b
```

Observed tradeoff:

- 7B provides significantly better reasoning and code quality,
- 3B is faster but less reliable on complex tasks.

---

# Docker-Based Deployment

The final system uses Dockerized Ollama rather than local native execution.

Reasons:

- easier reproducibility,
- simplified setup,
- identical execution environment,
- easier evaluation by reviewers.

The setup also includes:

- Neo4j Docker container,
- automatic Ollama model download,
- persistent Docker volumes.

---

# Prompt Engineering Decisions

The prompts were iteratively refined to:

- minimize hallucinations,
- encourage valid ReAct formatting,
- reduce unnecessary inspection calls,
- improve retry quality.

---

# Performance Optimizations

Implemented improvements:

- reduced inspection verbosity,
- truncated stderr/stdout in retry prompts,
- reduced context size,
- limited generated tokens,
- configurable timeout values.

---

# Chat Memory and Persistence

A Neo4j-based persistence layer was designed to support:

- conversation storage,
- message history,
- generated plot tracking,
- conversation resumption.

Stored entities:

- `Conversation`
- `Message`

Stored metadata includes:

- role,
- content,
- timestamp,
- generated plot paths.

---

# Strategic Tradeoffs

## Manual ReAct Loop vs LangGraph

The ReAct orchestration was implemented manually rather than using LangGraph.

Reasons:

- educational value,
- full control over execution flow,
- transparency of the reasoning pipeline,
- easier debugging during development.

---

## Simplicity vs Overengineering

The architecture intentionally avoids:

- excessive abstractions,
- unnecessary framework layers,
- premature optimization.

---

# Requirements

- Python 3.11+
- Docker Desktop or Docker Engine
- Docker Compose v2

If using WSL2 on Windows:

Docker Desktop must have WSL integration enabled for the target Linux distribution.

---

# Installation

## Clone Repository

```bash
git clone <repository-url>
cd react-plotly-agent
```

---

# Create Virtual Environment

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

# Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

# Start Docker Services

```bash
docker compose up -d
```

This starts:

- Ollama
- Neo4j

---

# Verify Running Containers

```bash
docker ps
```

Expected containers:

```text
react-plotly-ollama
react-chart-agent-neo4j
```

---

# Running the Agent

Example:

```bash
python -m main \
"Create a pie chart using exactly the column 'Color'." \
--input_file data/products-100.csv
```

---

# Memory-Enabled Execution

```bash
python -m main \
"Create a pie chart using exactly the column 'Color'." \
--input_file data/products-100.csv \
--enable_memory \
--conversation_id color_demo
```

Follow-up request:

```bash
python -m main \
"Now convert it into a donut chart and use a dark theme." \
--input_file data/products-100.csv \
--enable_memory \
--conversation_id color_demo
```

---

# Neo4j Browser

Neo4j Browser is available at:

```text
http://localhost:7474
```

Credentials:

```text
username: neo4j
password: password
```

Example query:

```cypher
MATCH (c:Conversation)-[:HAS_MESSAGE]->(m:Message)
RETURN c, m
LIMIT 50
```

---

# Example Datasets

Included example datasets:

- Titanic dataset
- Products dataset

Supported formats:

- `.csv`
- `.xlsx`
- `.json`

---

# Current Limitations

- The current implementation stores full ReAct traces in memory.
- Memory retrieval currently loads recent messages only.
- Only local Ollama inference is supported.
- Neo4j metadata is stored as JSON strings for simplicity.
- The sandbox is process-isolated but not VM-level isolated.

---

# Future Improvements

Possible future extensions:

- semantic retrieval over conversation history,
- vector database integration,
- structured plot metadata indexing,
- streaming LLM responses,
- improved sandbox isolation,
- support for additional charting libraries,
- automatic column similarity matching,
- LangGraph-based orchestration alternative.

---

# Author

Riccardo Fazzi
