import os
import pathlib
from click.testing import CliRunner
import pytest

from cli import main  # Import from cli.py

@pytest.mark.integration
def test_e2e_dependency_update_real_api(tmp_path):
    # Skip test if required environment variables are not set.
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is not set; skipping real API integration test")
    if not os.environ.get("GITHUB_TOKEN"):
        pytest.skip("GITHUB_TOKEN is not set; skipping real API integration test")
    
    target_dir = str(tmp_path / "dummy_repos")
    os.makedirs(target_dir, exist_ok=True)
    sample_repos = []
    from git import Repo
    for i in range(2):
        repo_path = f"{target_dir}/dummy_repo_{i}"
        os.makedirs(repo_path, exist_ok=True)
        repo = Repo.init(repo_path)
        file_path = f"{repo_path}/requirements.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("some-dependency==0.1.0\n")
        repo.index.add(["requirements.txt"])
        repo.index.commit("Initial commit")
        sample_repos.append(repo_path)
  
    repos_csv = ",".join(sample_repos)
    args = [
        "--repos", repos_csv,
        "--files", "requirements.txt",
        "--prompt", "Please update some-dependency to version 1.2.3",
        "--branch-name", "update-dependency",
        "--pr-title", "Update Dependencies",
        "--pr-body", "Updating to 1.2.3 for all repos",
        "--dry-run"  # Remove this flag to actually commit/push and create a PR.
    ]
  
    runner = CliRunner()
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(main, args)
    finally:
        os.chdir(original_dir)
  
    assert result.exit_code == 0, f"CLI failed with output: {result.output}"
