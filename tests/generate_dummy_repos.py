#!/usr/bin/env python
import argparse
import os
import shutil
import subprocess
from pathlib import Path

# Dummy file contents for dependency files.
DUMMY_FILES = {
    "requirements.txt": """\
some-dependency==0.1.0
another-package==0.5.2
""",
    "pom.xml": """\
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>dummy-project</artifactId>
  <version>1.0.0</version>
  <dependencies>
    <dependency>
      <groupId>com.example</groupId>
      <artifactId>some-dependency</artifactId>
      <version>0.1.0</version>
    </dependency>
  </dependencies>
</project>
""",
    "package.json": """\
{
  "name": "dummy-project",
  "version": "1.0.0",
  "dependencies": {
    "some-dependency": "0.1.0",
    "another-package": "0.5.2"
  }
}
"""
}

def generate_files(target_path: str):
    """
    Generate dummy dependency files in the target_path.
    Only creates/overwrites the files if they do not exist.
    """
    os.makedirs(target_path, exist_ok=True)
    for filename, content in DUMMY_FILES.items():
        file_path = os.path.join(target_path, filename)
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Generated {file_path}")
        else:
            print(f"{file_path} already exists; skipping generation.")

def init_git_repo(repo_path: str):
    """
    Initialize a Git repository in repo_path.
    """
    try:
        subprocess.run(["git", "init", repo_path], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Initialized Git repository at {repo_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to initialize Git repo at {repo_path}: {e}")

def commit_dummy_files(repo_path: str):
    """
    Stage all files and commit them with a default message.
    """
    try:
        subprocess.run(["git", "-C", repo_path, "add", "."],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", repo_path, "commit", "-m", "Initial commit with dummy files"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Committed dummy files in {repo_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to commit dummy files in {repo_path}: {e}")

def generate_dummy_repos(target_dir: str, num_repos: int):
    """
    Generate 'num_repos' dummy repositories inside target_dir.
    For each repository:
      - If the repository does not already exist, create it, add dummy files,
        initialize it as a Git repository, and commit the files.
      - If the repository already exists, do nothing.
    """
    target_dir = Path(target_dir).resolve()
    os.makedirs(target_dir, exist_ok=True)
    repo_paths = []
    for i in range(num_repos):
        repo_name = f"dummy_repo_{i}"
        repo_path = target_dir / repo_name
        if not repo_path.exists():
            os.makedirs(repo_path, exist_ok=True)
            generate_files(str(repo_path))
            init_git_repo(str(repo_path))
            commit_dummy_files(str(repo_path))
        else:
            print(f"Repository {repo_path} already exists; skipping file generation and commit.")
        repo_paths.append(str(repo_path))
    print(f"Generated {num_repos} dummy repositories in {target_dir}")
    return repo_paths

def main():
    parser = argparse.ArgumentParser(
        description="Generate a specified number of dummy Git repositories with dummy dependency files."
    )
    parser.add_argument(
        "--target-dir", "-t",
        type=str,
        required=True,
        help="The target directory where dummy repositories will be created."
    )
    parser.add_argument(
        "--num-repos", "-n",
        type=int,
        required=True,
        help="The number of dummy repositories to create."
    )
    args = parser.parse_args()
    generate_dummy_repos(args.target_dir, args.num_repos)

if __name__ == "__main__":
    main()
