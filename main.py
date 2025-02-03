import os
import sys
import logging
import requests
from rich.progress import track

from git_ops import clone_or_pull_repo, create_branch, commit_and_push
from llm_ops import set_openai_api_key, get_llm_suggestion, apply_llm_changes

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
    Orchestrates the multi-repo LLM-based code update workflow.
    """
    # Set up logging
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/workflow.log",
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )

    # Optionally set your OpenAI key here or rely on env var
    if "OPENAI_API_KEY" in os.environ:
        logging.debug("Setting OpenAI API key from environment.")
        set_openai_api_key(os.environ["OPENAI_API_KEY"])
    else:
        logging.warning("OPENAI_API_KEY not found in environment.")

    for repo_url in track(repo_list, description="Processing repositories..."):
        try:
            logging.info(f"Processing repo: {repo_url}")
            repo_path = clone_or_pull_repo(repo_url)

            # Create or checkout branch
            create_branch(repo_path, branch_name)

            # For each file, get LLM suggestion and apply
            for file_relative_path in file_list:
                file_path = os.path.join(repo_path, file_relative_path)
                if not os.path.exists(file_path):
                    print(f"File {file_relative_path} not found in {repo_url}, skipping...")
                    logging.warning(f"File {file_relative_path} not found in {repo_url}, skipping...")
                    continue

                with open(file_path, "r", encoding="utf-8") as f:
                    original_content = f.read()

                # Get LLM suggestion
                new_content = get_llm_suggestion(original_content, llm_prompt)

                # Apply changes
                apply_llm_changes(original_content, new_content, file_path)

            if not dry_run:
                # Commit and push changes
                commit_and_push(repo_path, branch_name, f"{pr_title}")

                # Open PR
                open_pull_request(repo_url, branch_name, pr_title, pr_body)
        except Exception as e:
            print(f"Error in workflow for {repo_url}: {e}")
            logging.error(f"Error in workflow for {repo_url}: {e}")


def open_pull_request(repo_url, branch_name, pr_title, pr_body):
    """
    Example function to create a PR on GitHub using the REST API.
    (Assumes the user has a GitHub personal access token.)
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("No GITHUB_TOKEN found. Skipping PR creation.")
        logging.warning("No GITHUB_TOKEN found. Skipping PR creation.")
        return

    # Parse owner/repo from the clone URL
    # e.g., "https://github.com/user/repo.git"
    # or     "git@github.com:user/repo.git"
    try:
        # This simplistic approach may need refinement for various URL formats
        if repo_url.startswith("http"):
            parts = repo_url.rstrip(".git").split("/")
            owner = parts[-2]
            repo_name = parts[-1]
        else:
            # git@github.com:user/repo.git
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
            "head": branch_name,  # e.g. "feature-branch"
            "base": "main"        # or "master", or something else
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
