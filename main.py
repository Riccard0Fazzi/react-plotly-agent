from src.agents.react_agent import Charts_Agent
import argparse
from pathlib import Path
from src.adapters.subprocess_code_executor import SubprocessCodeExecutor
from src.adapters.ollama_llm_adapter import OllamaLLMAdapter


SYSTEM_PROMPT = """
You are a Python data visualization agent.
Your task is to generate Python code for data analysis and Plotly visualization.
You work iteratively: generate code, observe execution results, and fix errors if needed.
""".strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--input_file", required = True)
    args = parser.parse_args()
    
    input_file = Path(args.input_file)
    llm = OllamaLLMAdapter()
    executor = SubprocessCodeExecutor()

    agent = Charts_Agent(llm, executor, SYSTEM_PROMPT, max_attempts = 3)

    result = agent.run(args.query, input_file)
    print(result)

if __name__ == "__main__":
    main()
