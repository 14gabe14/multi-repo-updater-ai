# llm_ops.py

import os
import ast
import time
import json
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

def extract_snippets(file_content: str, user_prompt: str, extraction_model: str = "gpt-3.5-turbo", max_retries: int = 3) -> list:
    """
    Uses LLM1 to extract minimal code snippets that need to be updated.
    The LLM is instructed to output JSON in the following format:
    
    {
      "snippets": [
         {"start_line": <number>, "end_line": <number>, "code": "<snippet code>"},
         ...
      ]
    }
    
    If no changes are needed, it should return { "snippets": [] }.
    """
    if client is None:
        raise RuntimeError("OpenAI client is not initialized. Call set_openai_api_key() first.")
    
    prompt_message = (
        "You are an expert code analyzer. Given the file content and user instructions, "
        "identify and extract only the minimal code snippets that need to be changed. "
        "For each snippet, output its starting and ending line numbers and the exact code snippet. "
        "Return your answer as valid JSON with the key 'snippets'.\n\n"
        "Output format:\n"
        '{ "snippets": [ { "start_line": 5, "end_line": 7, "code": "..." }, { "start_line": 1020, "end_line": 1022, "code": "..." } ] }\n\n'
        "Do not output any extra text.\n\n"
        "File content:\n"
        "```"
        f"{file_content}"
        "```\n\n"
        "User instructions:\n"
        f"{user_prompt}\n\n"
        "Extract only the parts that require updates."
    )
    
    attempt = 0
    while attempt < max_retries:
        try:
            llm_logger.info("Extraction Request (attempt %d): %s", attempt + 1, prompt_message)
            response = client.chat.completions.create(
                model=extraction_model,
                messages=[
                    {"role": "system", "content": "You are a code analysis assistant."},
                    {"role": "user", "content": prompt_message}
                ],
                temperature=0.2
            )
            result_text = response.choices[0].message.content
            llm_logger.info("Extraction Response (attempt %d): %s", attempt + 1, result_text)
            snippets_data = json.loads(result_text)
            return snippets_data.get("snippets", [])
        except Exception as e:
            llm_logger.error("Extraction LLM error on attempt %d: %s", attempt + 1, e)
            attempt += 1
            time.sleep(2)
    llm_logger.warning("Extraction LLM did not return a successful response after %d attempts.", max_retries)
    return []

def transform_snippet(snippet: dict, user_instruction: str, transformation_model: str = "gpt-4", max_retries: int = 3) -> dict:
    """
    Uses LLM2 to generate a minimal patch for the provided snippet.
    The LLM is instructed to output a JSON object with:
    
    {
       "start_line": <number>,
       "end_line": <number>,
       "new_code": "<modified code snippet>"
    }
    """
    if client is None:
        raise RuntimeError("OpenAI client is not initialized. Call set_openai_api_key() first.")
    
    prompt_message = (
        "You are a code transformation assistant. Given the following code snippet and a user instruction, "
        "generate a minimal patch that updates only the necessary lines. Do not return the entire file; "
        "output only the modified snippet.\n\n"
        f"Snippet (lines {snippet['start_line']} to {snippet['end_line']}):\n"
        "```"
        f"{snippet['code']}"
        "```\n\n"
        "User instruction:\n"
        f"{user_instruction}\n\n"
        "Return your answer in valid JSON with the keys 'start_line', 'end_line', and 'new_code'."
    )
    
    attempt = 0
    while attempt < max_retries:
        try:
            llm_logger.info("Transformation Request (attempt %d): %s", attempt + 1, prompt_message)
            response = client.chat.completions.create(
                model=transformation_model,
                messages=[
                    {"role": "system", "content": "You are a code transformation assistant."},
                    {"role": "user", "content": prompt_message}
                ],
                temperature=0.2
            )
            result_text = response.choices[0].message.content
            llm_logger.info("Transformation Response (attempt %d): %s", attempt + 1, result_text)
            patch_data = json.loads(result_text)
            return patch_data
        except Exception as e:
            llm_logger.error("Transformation LLM error on attempt %d: %s", attempt + 1, e)
            attempt += 1
            time.sleep(2)
    llm_logger.warning("Transformation LLM did not return a successful response after %d attempts. Returning original snippet.", max_retries)
    return {"start_line": snippet["start_line"], "end_line": snippet["end_line"], "new_code": snippet["code"]}

def validate_python_syntax(new_content: str) -> bool:
    try:
        ast.parse(new_content)
        return True
    except SyntaxError:
        return False

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
