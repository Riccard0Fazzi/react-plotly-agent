from src.ports.llm_port import LLMPort
from src.ports.chat_memory_port import ChatMemoryPort
from src.code_executor_port import CodeExecutorPort
from src.domain.models import ExecutionResult
from pathlib import Path
from src.config import SUPPORTED_DATA_EXTENSIONS, MAX_STDERR_CHARS, MAX_STDOUT_CHARS
import pandas as pd
import time 

class Charts_Agent:

    def __init__(
            self,
            llm: LLMPort,
            executor: CodeExecutorPort,
            system_prompt: str,
            memory: ChatMemoryPort = None,
            conversation_id: str = "default",
            max_attempts: int = 10
    ):
        self.system = system_prompt # store the system prompt
        self.messages = [] # conversation history
        self.llm = llm
        self.executor = executor
        self.max_attempts = max_attempts
        self.memory = memory
        self.conversation_id = conversation_id

        if self.memory:
            self.memory.create_conversation(self.conversation_id)

            previous_messages = self.memory.load_messages(self.conversation_id)

            if previous_messages:
                self.messages = previous_messages

        # add system prompt only if no previous history exists
        if not self.messages:
            system_message = {
                "role": "system",
                "content": system_prompt
            }

            self.messages.append(system_message)

            if self.memory:
                self.memory.save_message(
                    self.conversation_id,
                    role="system",
                    content=system_prompt
                )
        


    def __call__(self, message):
        self.messages.append({'role': 'user', 'content': message})
        if self.memory:
            self.memory.save_message(
                self.conversation_id,
                role="user",
                content=message
            )


        result = self.llm.chat(self.messages)
        self.messages.append({'role': 'assistant', 'content': result})

        if self.memory:
            self.memory.save_message(
                self.conversation_id,
                role="assistant",
                content=result
            )

        return result
    
    def _format_execution_result(self, result: ExecutionResult) -> str:
        stderr = result.stderr[-MAX_STDERR_CHARS:] if result.stderr else ""
        stdout = result.stdout[-MAX_STDOUT_CHARS:] if result.stdout else ""
        if result.success and result.generated_files:
            return (
            "Execution succeeded.\n"
            f"STDOUT:\n{stdout}\n\n"
            f"Generated HTML files:\n"
            + "\n".join(str(path) for path in result.generated_files)
        )

        return (
            "Execution failed.\n"
            f"Timed out: {result.timed_out}\n"
            f"Exit code: {result.exit_code}\n\n"
            f"STDOUT:\n{stdout}\n\n"
            f"STDERR:\n{stderr}\n"
        )

    def _inspect_dataset(self, dataset_path: Path) -> str:
        # this function extracts useful information about the input file
        # it directly gives very useful informations to the llm about the structure of the data file
        # so the llm directly has access to informations that otherwise should retrieve by itself spending cycles
        suffix = dataset_path.suffix.lower()
        if suffix not in SUPPORTED_DATA_EXTENSIONS:
            raise ValueError(
                    f"Unsupported dataset format '{suffix}'."
                    f"Supported formats are: {SUPPORTED_DATA_EXTENSIONS}"
            )
        
        if suffix == ".csv":
            df = pd.read_csv(dataset_path)
        elif suffix == ".xlsx":
            df = pd.read_excel(dataset_path)
        elif suffix == ".json":
            df = pd.read_json(dataset_path)

        return (
                f"Columns: {list(df.columns)}\n\n"
                f"Data types: \n{df.dtypes.to_string()}"
                f"Missing values:\n{df.isna().sum().to_string()}"

        )
    
    # generic function that give a python script in a str executes it and return the execution result
    def _execute_python_code(self, code: str, dataset_path: Path) -> tuple[str, ExecutionResult]:
        """Execute the python generated code"""
        result = self.executor.execute_code(code, dataset_path)
        return self._format_execution_result(result), result
    
    def _parse_action(self, llm_output: str) -> str | None:
        if "Action: inspect_dataset" in llm_output:
            return "inspect_dataset"
        if "Action: execute_python_code" in llm_output:
            return "execute_python_code"
        if "Answer:" in llm_output:
            return "answer"
        return None

    def _extract_python_code(self, llm_output: str) -> str | None:
        if "```python" in llm_output:
            return llm_output.split("```python", 1)[1].split("```", 1)[0].strip()
        if "```" in llm_output:
            return llm_output.split("```", 1)[1].split("```", 1)[0].strip()
        return None
    
    # ReAct LOOP
    def run(self, user_request: str, dataset_path: Path) -> ExecutionResult:

        suffix = dataset_path.suffix.lower()

        prompt = self._build_initial_prompt(
            user_request=user_request,
            dataset_extension=suffix,
        )
        last_result = None

        for attempt in range(1, self.max_attempts + 1):
            print(f"\n=== Attempt {attempt}/{self.max_attempts} ===")
            llm_output = self(prompt)
            action = self._parse_action(llm_output)
            print("\nAssistant:")
            print(llm_output)

            if action == "inspect_dataset":
                observation = self._inspect_dataset(dataset_path)
                prompt = f"Observation:\n{observation}"
            elif action == "execute_python_code":
                code = self._extract_python_code(llm_output)
                if code is None:
                    prompt = self._build_recovery_prompt("missing_code_block")
                    continue
                observation, result = self._execute_python_code(code, dataset_path)
                last_result = result

                print(observation)
                
                # check result
                if result.success and result.generated_files:
                    print("Execution: success")
                    # if memory enabled store generated plot paths
                    if self.memory:
                        self.memory.save_message(
                            self.conversation_id,
                            role="assistant",
                            content="Plot generated successfully.",
                            metadata={
                                "generated_files": [str(path) for path in result.generated_files]
                            },
                        )
                    prompt = (
                        "Observation:\n"
                        f"{observation}\n\n"
                        "The plot was generated successfully. Provide the final answer."
                    )
                else:
                    prompt = self._build_recovery_prompt(
                        failure_type="execution_failed",
                        observation=observation,
                    )

            elif action == "answer":
                print("Final answer received.")
                return last_result
            
            else:
                prompt = self._build_recovery_prompt("invalid_action")
                continue

    def _build_initial_prompt(
        self,
        user_request: str,
        dataset_extension: str,
    ) -> str:

        return f"""
    User request:
    {user_request}

    The dataset inside the sandbox is available as:
    input{dataset_extension}

    Start by deciding the next action according to the ReAct protocol.
    """.strip()

    def _build_recovery_prompt(self, failure_type: str, observation: str = "") -> str:

        if failure_type == "invalid_action":
             return """
Observation:
I could not parse a valid action.

Please use exactly one of:
- Action: inspect_dataset
- Action: execute_python_code
- Answer: <short final answer>
""".strip()
        
        elif failure_type == "missing_code_block":
            return """
Observation:
You selected Action: execute_python_code, but no Python code block was found.

Please retry using this format:

Action: execute_python_code
```python
# executable Python code here
```
PAUSE
""".strip()

        elif failure_type == "execution_failed":
            return f"""
Observation from previous execution:
{observation}

The Python code failed or did not generate a valid HTML plot.

Decide the next action using the ReAct protocol.
Use the error message in the Observation to fix the code.
If the error is related to missing or wrong columns, use inspect_dataset.
Otherwise, retry with execute_python_code and corrected code.
""".strip()



