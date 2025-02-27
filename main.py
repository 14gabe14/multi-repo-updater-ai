# main.py

import os
import sys
import logging
import requests
from rich.progress import track

from git_ops import clone_or_pull_repo, create_branch, commit_and_push
from llm_ops import set_openai_api_key, extract_snippets, transform_snippet, apply_llm_changes

def run_workflow(
    repo_list,
    file_list,
    llm_prompt,
    branch_name,
    pr_title,
    pr_body,
    dry_run=False
):
    """
    Orchestrates the multi-repo LLM-based code update workflow using a two-step LLM approach:
    1. Extraction: Identify and extract relevant code snippets (with line numbers) from each file.
    2. Transformation: For each snippet, generate a minimal patch.
    
    Patches are applied in reverse order (from the bottom of the file to the top)
    to prevent shifting line numbers.
    """
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/workflow.log",
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )

    if "OPENAI_API_KEY" in os.environ:
        logging.debug("Setting OpenAI API key from environment.")
        set_openai_api_key(os.environ["OPENAI_API_KEY"])
    else:
        logging.warning("OPENAI_API_KEY not found in environment.")

    for repo_url in track(repo_list, description="Processing repositories..."):
        try:
            logging.info(f"Processing repo: {repo_url}")
            repo_path = clone_or_pull_repo(repo_url)

            create_branch(repo_path, branch_name)

            for file_relative_path in file_list:
                file_path = os.path.join(repo_path, file_relative_path)
                if not os.path.exists(file_path):
                    print(f"File {file_relative_path} not found in {repo_url}, skipping...")
                    logging.warning(f"File {file_relative_path} not found in {repo_url}, skipping...")
                    continue

                with open(file_path, "r", encoding="utf-8") as f:
                    original_content = f.read()

                # Extraction Phase: Extract relevant code snippets using LLM1.
                snippets = extract_snippets(original_content, llm_prompt)
                if not snippets:
                    print(f"No relevant snippets found in {file_relative_path}.")
                    continue

                patches = []
                # For each snippet, call LLM2 individually to generate a minimal patch.
                for snippet in snippets:
                    patch = transform_snippet(snippet, llm_prompt)
                    patches.append(patch)

                # Sort patches in reverse order by start_line to avoid line shifting issues.
                patches.sort(key=lambda p: p["start_line"], reverse=True)
                
                # Apply each patch to the file content.
                lines = original_content.splitlines()
                for patch in patches:
                    start = patch["start_line"] - 1  # Convert to 0-index
                    end = patch["end_line"]
                    new_lines = patch["new_code"].splitlines()
                    lines = lines[:start] + new_lines + lines[end:]
                updated_content = "\n".join(lines)

                apply_llm_changes(original_content, updated_content, file_path)

            if not dry_run:
                commit_and_push(repo_path, branch_name, f"{pr_title}")
                open_pull_request(repo_url, branch_name, pr_title, pr_body)
        except Exception as e:
            print(f"Error in workflow for {repo_url}: {e}")
            logging.error(f"Error in workflow for {repo_url}: {e}")

def open_pull_request(repo_url, branch_name, pr_title, pr_body):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("No GITHUB_TOKEN found. Skipping PR creation.")
        logging.warning("No GITHUB_TOKEN found. Skipping PR creation.")
        return

    try:
        if repo_url.startswith("http"):
            parts = repo_url.rstrip(".git").split("/")
            owner = parts[-2]
            repo_name = parts[-1]
        else:
            segment = repo_url.split(":")[1]
            segment = segment.rstrip(".git")
            owner, repo_name = segment.split("/")

        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "title": pr_title,
            "body": pr_body,
            "head": branch_name,
            "base": "main"
        }

        response = requests.post(api_url, json=data, headers=headers)
        if response.status_code == 201:
            print(f"Opened PR for {repo_name}: {response.json().get('html_url')}")
            logging.info(f"Opened PR for {repo_name}: {response.json().get('html_url')}")
        else:
            print(f"Failed to open PR for {repo_name}: {response.text}")
            logging.error(f"Failed to open PR for {repo_name}: {response.text}")
    except Exception as e:
        print(f"Failed to parse or create PR for {repo_url}: {e}")
        logging.error(f"Failed to parse or create PR for {repo_url}: {e}")

