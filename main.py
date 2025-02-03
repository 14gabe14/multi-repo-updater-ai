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
        print("Warning: OPENAI_API_KEY not found in environment.")
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

                new_content = get_llm_suggestion(original_content, llm_prompt)
                apply_llm_changes(original_content, new_content, file_path)

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

def undo_workflow(repo_list, branch_name, restore_files=None):
    """
    For each repository in repo_list, check out the default branch (try 'main', then 'master'),
    optionally restore specified files, and then delete the branch specified by branch_name.
    """
    from git import Repo, GitCommandError
    for repo_url in repo_list:
        try:
            # Assume repo_url is a local path.
            repo_path = repo_url  
            repo = Repo(repo_path)
            # Determine the default branch.
            default_branch = None
            if "main" in repo.heads:
                default_branch = repo.heads["main"]
            elif "master" in repo.heads:
                default_branch = repo.heads["master"]
            else:
                print(f"Default branch not found in {repo_path}. Cannot undo changes.")
                continue

            # Checkout default branch.
            default_branch.checkout()

            # If restore_files is provided, restore each file to HEAD.
            if restore_files:
                for file_rel in restore_files:
                    try:
                        # Use git checkout to restore the file from HEAD.
                        repo.git.checkout("--", file_rel)
                        print(f"Restored {file_rel} in {repo_path}")
                    except Exception as e:
                        print(f"Failed to restore {file_rel} in {repo_path}: {e}")

            # Delete the update branch if it exists.
            if branch_name in repo.heads:
                repo.delete_head(branch_name, force=True)
                print(f"Deleted branch '{branch_name}' in {repo_path}")
            else:
                print(f"Branch '{branch_name}' does not exist in {repo_path}; nothing to undo.")

            # Optionally, delete the remote branch if desired.
            if repo.remotes and "origin" in repo.remotes:
                try:
                    repo.remotes["origin"].push(refspec=f":{branch_name}")
                    print(f"Deleted remote branch '{branch_name}' in {repo_path}")
                except GitCommandError as e:
                    print(f"Could not delete remote branch '{branch_name}' in {repo_path}: {e}")

        except Exception as e:
            print(f"Error undoing changes for {repo_url}: {e}")
            
if __name__ == "__main__":
    # If run directly (without using the CLI group), you can call run_workflow with parameters.
    # Otherwise, the CLI (cli.py) will handle command-line arguments.
    pass
