import os
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from git_ops import clone_or_pull_repo, create_branch, commit_and_push

def test_clone_or_pull_repo(tmp_path):
    repo_url = "C:/fake/path/fake_repo.git"
    base_dir = str(tmp_path)
    repo_name = "fake_repo.git"  # os.path.basename(repo_url)

    # Fake os.path.exists: return False for the target repo path.
    def fake_exists(path):
        target = os.path.join(base_dir, repo_name)
        if path == target:
            return False
        return False

    with patch("os.path.exists", side_effect=fake_exists) as mock_exists, \
         patch("git_ops.Repo.clone_from") as mock_clone:
        mock_clone.return_value = None
        result_path = clone_or_pull_repo(repo_url, base_dir=base_dir)
        mock_clone.assert_called_with(repo_url, result_path)

        # Now simulate that the target repository directory exists.
        repo_dir = Path(result_path)
        repo_dir.mkdir(exist_ok=True)
        (repo_dir / ".git").mkdir(exist_ok=True)
        
        def fake_exists2(path):
            target = os.path.join(base_dir, repo_name)
            if path == target:
                return True
            return False
        mock_exists.side_effect = fake_exists2
        result_path_2 = clone_or_pull_repo(repo_url, base_dir=base_dir)
        assert result_path == result_path_2

def test_create_branch(tmp_path):
    mock_repo_instance = MagicMock()
    with patch("git_ops.Repo", side_effect=lambda repo_path, **kwargs: mock_repo_instance):
        repo_path = str(tmp_path / "fake_repo")
        os.makedirs(repo_path, exist_ok=True)
        git_dir = os.path.join(repo_path, ".git")
        os.makedirs(git_dir, exist_ok=True)
        # Create a minimal HEAD file to simulate a valid repo.
        with open(os.path.join(git_dir, "HEAD"), "w") as f:
            f.write("ref: refs/heads/master")
        create_branch(repo_path, "test-branch")
        mock_repo_instance.create_head.assert_called_with("test-branch")


def test_commit_and_push(tmp_path):
    mock_repo_instance = MagicMock()
    with patch("git_ops.Repo", side_effect=lambda repo_path, **kwargs: mock_repo_instance):
        mock_repo_instance.is_dirty.return_value = True
        repo_path = str(tmp_path / "fake_repo")
        os.makedirs(repo_path, exist_ok=True)
        git_dir = os.path.join(repo_path, ".git")
        os.makedirs(git_dir, exist_ok=True)
        with open(os.path.join(git_dir, "HEAD"), "w") as f:
            f.write("ref: refs/heads/master")
        commit_and_push(repo_path, "my-branch", "Test commit")
        mock_repo_instance.git.add.assert_called_with(all=True)
        mock_repo_instance.index.commit.assert_called_with("Test commit")
        mock_repo_instance.remotes.__getitem__.return_value.push.assert_called()
