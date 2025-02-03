import os
import shutil
from git import Repo, GitCommandError

def clone_or_pull_repo(repo_url: str, base_dir: str = "repos") -> str:
    # Use os.path.basename and os.path.normpath to handle Windows paths.
    repo_name = os.path.basename(os.path.normpath(repo_url))
    repo_path = os.path.join(base_dir, repo_name)

    if not os.path.exists(repo_path):
        # If repo_url is a local path, copy it.
        if os.path.exists(repo_url):
            try:
                shutil.copytree(repo_url, repo_path)
                print(f"Copied repository from {repo_url} to {repo_path}")
            except Exception as e:
                raise RuntimeError(f"Failed to copy local repository from {repo_url}: {e}")
        else:
            try:
                Repo.clone_from(repo_url, repo_path)
                print(f"Cloned repository: {repo_url}")
            except GitCommandError as e:
                raise RuntimeError(f"Failed to clone {repo_url}: {e}")
    else:
        try:
            repo = Repo(repo_path)
            # Check if there is a remote named "origin"
            if "origin" in repo.remotes:
                origin = repo.remotes["origin"]
                origin.pull()
                print(f"Pulled latest changes in: {repo_path}")
            else:
                print(f"No remote named 'origin' found in {repo_path}; skipping pull.")
        except GitCommandError as e:
            print(f"Error pulling {repo_url}: {e}")

    return repo_path

def create_branch(repo_path: str, branch_name: str):
    """
    Creates and checks out a new branch in the repository.
    """
    repo = Repo(repo_path)
    try:
        # If the branch already exists locally, checkout instead
        if branch_name in repo.heads:
            repo.git.checkout(branch_name)
        else:
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
        print(f"Checked out branch: {branch_name} in {repo_path}")
    except GitCommandError as e:
        raise RuntimeError(f"Error creating or checking out branch {branch_name} in {repo_path}: {e}")


def commit_and_push(repo_path: str, branch_name: str, commit_message: str, remote_name: str = "origin"):
    """
    Commits changes and pushes to the remote branch.
    """
    repo = Repo(repo_path)
    repo.git.add(all=True)
    if repo.is_dirty():
        try:
            repo.index.commit(commit_message)
            print(f"Committed changes in {repo_path}")
        except GitCommandError as e:
            raise RuntimeError(f"Error committing changes in {repo_path}: {e}")
    else:
        print(f"No changes to commit in {repo_path}")

    try:
        repo.remotes[remote_name].push(refspec=f"{branch_name}:{branch_name}")
        print(f"Pushed changes to {remote_name}/{branch_name}")
    except GitCommandError as e:
        raise RuntimeError(f"Error pushing to {remote_name}/{branch_name} in {repo_path}: {e}")
