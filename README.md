# Multi-Repo LLM Code Update Tool

This tool automates code changes across multiple Git repositories by:
- Cloning or updating repositories locally.
- Creating a new branch for changes.
- Using an LLM (e.g., OpenAI GPT) to modify specified files.
- Committing and pushing changes.
- Opening a pull request for each repository.

> **Note:** To help avoid accidental updates to your original repositories, you can use the `--sandbox-path` flag to direct all operations to a sandboxed copy. Alternatively, use the `prepare` command to create a sandbox from your original workspace.

## Installation

1. Clone this project:
   ```bash
   git clone <this-repo-url>
   ```
2. Install dependencies:
   ```bash
   cd <this-repo>
   pip install -r requirements.txt
   ```

## Setup

Create a `workspace-config.yaml` file with the following structure:

```yaml
global:
  default_branch: master
  directory: "C:/Users/gabri/Documents/GitHub"
repos:
  - name: dummy_repo_0
    url: "https://github.com/owner/dummy_repo_0.git"  # Remote URL used to clone if the repo is not found locally.
    default_branch: develop                           # Repository-specific default branch.
    tags: [core, backend]                             # Tags for filtering subsets.
  - name: dummy_repo_1
    url: "https://github.com/owner/dummy_repo_1.git"
    default_branch: develop
    tags: [experimental]
  - name: dummy_repo_2
    directory: "C:/Users/gabri/Documents/repos"       # Custom directory; if not overridden, updates apply here.
    tags: [core, frontend]
```

- **Global Section:**  
  Contains the default branch and the workspace directory where your repositories are normally located.

- **Repos Section:**  
  Each repository can specify:
  - A `url` for cloning (if not found locally).
  - A custom `directory` if the repo is located outside the global workspace.
  - Optional `tags` for filtering subsets.

## Usage

### Run Command

The `run` command applies updates across your repositories. By default, it uses the paths from the configuration file. However, you can override behavior with the following options:

- **Subset Filtering:**  
  Use the `--subset` flag to specify a comma-separated list of repository names or tags.
  
- **Sandbox Mode:**  
  Use `--sandbox-path` to force all operations into a sandbox directory (ignoring repository-specific directories).

**Examples:**

- **Standard Run (using configuration paths):**

  ```bash
  python cli.py run \
    --subset "dummy_repo_0,dummy_repo_1" \
    --files "requirements.txt" \
    --prompt "Update dependency version to 1.2.3" \
    --branch-name "update-dependency" \
    --pr-title "Dependency Update" \
    --pr-body "This PR updates the dependency version to 1.2.3" \
    --dry-run
  ```

- **Run in Sandbox Mode:**

  ```bash
  python cli.py run \
    --subset "core,dummy_repo_1" \
    --files "src/app.py,requirements.txt" \
    --prompt "Update dependency version to 1.2.3" \
    --branch-name "update-dependency" \
    --pr-title "Dependency Update" \
    --pr-body "This PR updates the dependency version to 1.2.3" \
    --dry-run \
    --sandbox-path "C:/Users/gabri/Documents/LLMSandbox"
  ```

### Undo Command

The `undo` command reverts the changes by deleting the update branch and optionally restoring specific files.

**Examples:**

- **Standard Undo:**

  ```bash
  python cli.py undo \
    --subset "dummy_repo_0,dummy_repo_1" \
    --branch-name "update-dependency" \
    --restore-files "src/app.py,requirements.txt"
  ```

- **Undo in Sandbox Mode:**

  ```bash
  python cli.py undo \
    --subset "core" \
    --branch-name "update-dependency" \
    --restore-files "src/app.py,requirements.txt" \
    --sandbox-path "C:/Users/gabri/Documents/LLMSandbox"
  ```

### Prepare Command

The `prepare` command copies repositories from your global workspace to a specified target directory (i.e., creating a sandbox).

**Example:**

```bash
python cli.py prepare --target-path "C:/Users/gabri/Documents/LLMSandbox"
```

This command copies each repository (using paths resolved from the configuration) into the target directory, so you can run updates in isolation.

## Features

1. **Multiple Repo Handling**  
   - Clones or updates each repository as needed.
   - Creates a dedicated branch for changes.

2. **LLM Integration**  
   - Sends file content and user prompts to an LLM for update suggestions.
   - Validates suggestions (e.g., ensuring Python syntax is correct).

3. **Pull Request Creation**  
   - Automatically opens a pull request via the GitHub API (or other providers if extended).

4. **Sandbox Option**  
   - The `--sandbox-path` flag and `prepare` command let you operate on a sandbox copy to avoid accidental updates to your original repositories.

5. **Error Handling & Logging**  
   - Logs operations to a `logs/` directory.
   - Implements retry logic and graceful error exits.

## Additional Notes

- Ensure you set up your environment with an OpenAI API key and, if required, a GitHub token.
- The sandbox override helps prevent unintended modifications. Always double-check your paths before running update workflows in production.


