import os
import pathlib
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
import pytest
from git import Repo

# Import the CLI entry point from cli.py
from cli import main  

@pytest.fixture
def temp_workspace():
    import tempfile, shutil
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

@pytest.fixture
def sample_repos(temp_workspace):
    from git import Repo
    repos_info = []
    for i in range(2):
        repo_path = os.path.join(temp_workspace, f"dummy_repo_{i}")
        os.makedirs(repo_path, exist_ok=True)
        repo = Repo.init(repo_path)
        file_path = os.path.join(repo_path, "requirements.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("some-dependency==0.1.0\n")
        repo.index.add(["requirements.txt"])
        repo.index.commit("Initial commit")
        repos_info.append(os.path.abspath(repo_path))
    return repos_info

def test_e2e_dependency_update_with_mocks(temp_workspace, sample_repos):
    with patch("openai.resources.chat.Completions.create") as mock_openai, \
         patch("requests.post") as mock_requests_post:

        mock_openai.return_value = {
            "choices": [
                {"message": {"content": "some-dependency==1.2.3\n"}}
            ]
        }
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"html_url": "http://fake-pr-url"}
        mock_requests_post.return_value = mock_response

        repos_csv = ",".join(sample_repos)
        # Remove the --dry-run flag so that PR creation is executed.
        args = [
            "--repos", repos_csv,
            "--files", "requirements.txt",
            "--prompt", "Please update some-dependency to version 1.2.3",
            "--branch-name", "update-dependency",
            "--pr-title", "Update Dependencies",
            "--pr-body", "Updating to 1.2.3 for all repos"
        ]

        runner = CliRunner()
        original_dir = os.getcwd()
        try:
            os.chdir(temp_workspace)
            result = runner.invoke(main, args)
        finally:
            os.chdir(original_dir)

        assert result.exit_code == 0, f"CLI failed with output: {result.output}"

        # Verify that for each source repo, the cloned repository exists and has the updates.
        for source_repo in sample_repos:
            repo_name = os.path.basename(os.path.normpath(source_repo))
            cloned_repo_path = os.path.join(temp_workspace, "repos", repo_name)
            assert os.path.exists(cloned_repo_path), f"Cloned repository not found at {cloned_repo_path}"
            repo = Repo(cloned_repo_path)
            branch_names = [h.name for h in repo.heads]
            assert "update-dependency" in branch_names, f"Branch not created in {cloned_repo_path}"
            req_file_path = os.path.join(cloned_repo_path, "requirements.txt")
            with open(req_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "1.2.3" in content, "Dependency version was not updated."

        # Now, ensure that requests.post was called.
        mock_requests_post.assert_called()
