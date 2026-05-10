


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

---

# Main Features

- ReAct-style autonomous agent loop
- Automatic Plotly chart generation
- Sandboxed Python execution
- Retry and self-correction mechanisms
- Dockerized local LLM inference through Ollama
- Neo4j-based conversation memory and persistence
- Interactive HTML dashboard generation
- Fully local execution (no cloud APIs)

---

# Architecture

The project follows a lightweight Ports & Adapters organization.

## Folder Structure

```text
src/
├── adapters/
├── ports/
├── use_cases/
├── domain/
```

---

# ports/

Contains the abstract interfaces used by the agent.

Examples:

- LLMPort
- CodeExecutorPort
- ChatMemoryPort

These interfaces make it easier to replace implementations without changing the main agent logic.

For example, the LLM could be switched from Ollama to another provider without modifying the agent itself.

Example:
```python
class CodeExecutorPort(abc.ABC):

    @abc.abstractmethod
    def execute_code(self, code: str, input_data_path: Path) -> ExecutionResult:
        raise NotImplementedError
```
---

# adapters/

Contains the concrete implementations of the interfaces.

Current adapters:

- OllamaLLMAdapter
- SubprocessCodeExecutor
- Neo4jChatMemoryAdapter

These components handle external tools and infrastructure such as:

- HTTP requests,
- code execution,
- database persistence.
---
# use_cases/

Contains the main application logic.

The central component is:

ReactChartAgent

This class manages:

- the ReAct loop,
- prompt generation,
- action parsing,
- retry handling,
- execution observations.
---
# domain/

Contains shared models and data structures used across the project.

Current model:

ExecutionResult

This model is used to store information about code execution results such as:

- stdout,
- stderr,
- generated files,
- execution time,
- timeout status.

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

Alternative recommended model:

```text
qwen2.5-coder:7b
```
The 3B model was mainly used due to limited local computational resources and faster inference speed on CPU-only systems.

However, during development it was observed that the 7B model provides significantly better reasoning, retry behavior, and code generation reliability, especially for more complex plotting tasks and recovery scenarios.

For more stable behavior, the 7B model should generally be preferred when hardware resources allow it.

Observed tradeoff:

- 7B provides significantly better reasoning and code quality,
- 3B is faster but less reliable on complex tasks.

For local inference, I mainly looked at open-source coding models such as Qwen and DeepSeek.

Due to limited computational resources, I started with smaller local models that could run reasonably well on CPU-only systems.

In the end, I selected Qwen2.5-Coder because it provided a good balance between:

- inference speed,
- code generation quality,
- reasoning capability,
- local hardware requirements.

During development, the 7B version consistently produced better reasoning and retry behavior, while the 3B version was faster but less reliable on more complex tasks.

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

- better understanding of the execution flow,
- full control over the reasoning loop,
- easier debugging during development,
- simpler architecture for the scope of the project.

---

# Requirements

- Python 3.11+
- Docker Desktop 
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

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

# Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

# Start Docker Services

The project includes a `docker-compose.yml` configuration file used to start:

- Ollama
- Neo4j


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

# Configuration

Main configuration parameters can be modified inside:

```text
src/config.py
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
"Now create a histogram using the same column as before." \
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
- Only local Ollama inference is supported.
- Neo4j metadata is stored as JSON strings for simplicity.
- The sandbox is process-isolated but not VM-level isolated.

---

# Author

Riccardo Fazzi
