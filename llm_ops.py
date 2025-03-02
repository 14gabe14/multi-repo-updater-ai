# llm_ops.py

import os
import ast
import time
from openai import OpenAI  # Ensure you have the updated OpenAI SDK installed
import logging

# Global client; initially None.
client = None

# Ensure the logs directory exists
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Set up a dedicated logger for LLM conversations
llm_logger = logging.getLogger("llm_conversation")
llm_logger.setLevel(logging.INFO)
llm_handler = logging.FileHandler(os.path.join(log_dir, "llm_conversation.log"), mode="a", encoding="utf-8")
llm_formatter = logging.Formatter("%(asctime)s - %(message)s")
llm_handler.setFormatter(llm_formatter)
llm_logger.addHandler(llm_handler)

def set_openai_api_key(api_key: str):
    """
    Set the OpenAI API key and initialize the global client.
    """
    global client
    client = OpenAI(api_key=api_key)
    os.environ["OPENAI_API_KEY"] = api_key

def validate_python_syntax(new_content: str) -> bool:
    try:
        ast.parse(new_content)
        return True
    except SyntaxError:
        return False

def process_chunk(chunk: dict, user_instruction: str, model: str = "gpt-4o-mini", max_retries: int = 1) -> str:
    """
    Processes a code chunk with a single LLM call.
    
    The LLM is instructed:
    "Given the following code chunk and user instruction, if this chunk requires changes,
    output the updated code snippet enclosed in triple backticks (```).
    If no changes are required, output exactly 'false'."
    
    Returns:
      - The new code as a string (with backticks removed), if changes are required.
      - None if the output is "false".
    """
    attempt = 0
    while attempt < max_retries:
        try:
            prompt_message = (
                "You are a code transformation assistant. "
                "Given the following code chunk and a user instruction, "
                "if this chunk requires changes, output the updated code snippet enclosed in triple backticks (```). "
                "Do not include any extra text. "
                "If no changes are required, output exactly 'false'.\n\n"
                f"Code chunk (complete function or class block):\n"
                "```python\n"
                f"{chunk['code']}\n"
                "```\n\n"
                "User instruction:\n"
                f"{user_instruction}\n\n"
                "Output exactly as described."
            )
            logging.info("Process Chunk Request (attempt %d): %s", attempt + 1, prompt_message)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a code transformation assistant."},
                    {"role": "user", "content": prompt_message}
                ],
                temperature=0.2
            )
            result_text = response.choices[0].message.content.strip()
            logging.info("Process Chunk Response (attempt %d): %s", attempt + 1, result_text)
            
            if result_text.lower() == "false":
                return None
            # Extract code from triple backticks.
            if result_text.startswith("```") and result_text.endswith("```"):
                lines = result_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                updated_code = "\n".join(lines).strip()
                return updated_code
            else:
                # If formatting is off, assume the entire result is the code.
                return result_text
        except Exception as e:
            logging.error("Process Chunk LLM error on attempt %d: %s", attempt + 1, e)
            attempt += 1
            time.sleep(2)
    logging.warning("Process Chunk LLM did not return a successful response after %d attempts.", max_retries)
    return None

def apply_llm_changes(original_content: str, new_content: str, file_path: str) -> None:
    """
    Writes the new content to the file if valid.
    """
    if file_path.endswith(".py") and not validate_python_syntax(new_content):
        print(f"LLM suggested invalid Python syntax for {file_path}. Keeping original content.")
        return
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Applied changes to {file_path}")

def chunk_code_by_ast(file_content: str) -> list:
    """
    Parse the file content using AST and return a list of code chunks.
    Each chunk is a dict with:
      - 'start_line': int,
      - 'end_line': int,
      - 'code': str (the source segment corresponding to a function or class)
    If AST parsing fails, return the entire file as a single chunk.
    """
    chunks = []
    try:
        tree = ast.parse(file_content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                segment = ast.get_source_segment(file_content, node)
                if segment:
                    start_line = node.lineno
                    end_line = getattr(node, "end_lineno", start_line)
                    chunks.append({
                        "start_line": start_line,
                        "end_line": end_line,
                        "code": segment
                    })
    except Exception as e:
        # Fallback: return entire file if AST parsing fails
        chunks.append({
            "start_line": 1,
            "end_line": len(file_content.splitlines()),
            "code": file_content
        })
    return chunks
