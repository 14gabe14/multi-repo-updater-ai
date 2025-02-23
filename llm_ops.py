# llm_ops.py

import os
import ast
import time
from typing import Tuple
from openai import OpenAI  # Ensure you have the updated OpenAI SDK installed
import logging

# Global client; initially None.
client = None

# Ensure the logs directory exists
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)  # Creates the directory if it doesn’t exist

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
    # Optionally, you can also store the api_key in the environment:
    os.environ["OPENAI_API_KEY"] = api_key

def get_llm_suggestion(file_content: str, user_prompt: str, max_retries: int = 3) -> str:
    """
    Sends file content and user prompt to the LLM and returns the suggested modification.
    Logs the input prompt and the raw LLM output for debugging.
    Includes basic retry logic.
    """
    if client is None:
        raise RuntimeError("OpenAI client is not initialized. Call set_openai_api_key() first.")
        
    attempt = 0
    while attempt < max_retries:
        try:
            # Construct the prompt message.
            prompt_message = (
                f"File content:\n```{file_content}```\n"
                f"User instructions:\n{user_prompt}\n\n"
                "Please provide updated file content without overwriting unrelated code."
            )
            # Log the prompt message.
            llm_logger.info("LLM Request (attempt %d): %s", attempt + 1, prompt_message)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a coding assistant."},
                    {"role": "user", "content": prompt_message}
                ],
                temperature=0.2
            )
            
            suggestion = response.choices[0].message.content
            # Log the LLM response.
            llm_logger.info("LLM Response (attempt %d): %s", attempt + 1, suggestion)
            
            return suggestion
        except Exception as e:
            llm_logger.error("LLM API error on attempt %d: %s", attempt + 1, e)
            attempt += 1
            time.sleep(2)

    # If no successful response, log and return original content.
    llm_logger.warning("LLM did not return a successful response after %d attempts. Returning original content.", max_retries)

    return file_content

def validate_python_syntax(new_content: str) -> bool:
    """
    Validate that new_content is valid Python syntax. Return True if valid, False otherwise.
    """
    try:
        ast.parse(new_content)
        return True
    except SyntaxError:
        return False

def apply_llm_changes(original_content: str, new_content: str, file_path: str) -> None:
    """
    Writes the new content to the file if valid. For files that are likely to be code,
    it attempts to strip markdown formatting and only replace the dependency line.
    """
    # If the output is wrapped in triple backticks, extract only the inner content.
    if new_content.startswith("```") and new_content.endswith("```"):
        new_content = new_content.strip("`").strip()
    
    # Optionally: use a regex to find the updated dependency line.
    import re
    # Assume the dependency line follows the pattern 'some-dependency==<version>'
    pattern = r'(some-dependency==)[\d\.]+'
    match = re.search(pattern, new_content)
    if match:
        updated_line = match.group(0)
        # Now, replace the corresponding line in the original content.
        def replace_line(match_obj):
            return updated_line
        new_file_content = re.sub(pattern, replace_line, original_content)
    else:
        # If no dependency line is found, default to replacing entire content.
        new_file_content = new_content

    # (Optional) Validate syntax if file is Python.
    if file_path.endswith(".py") and not validate_python_syntax(new_file_content):
        print(f"LLM suggested invalid Python syntax for {file_path}. Keeping original content.")
        return

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_file_content)
    print(f"Applied changes to {file_path}")
