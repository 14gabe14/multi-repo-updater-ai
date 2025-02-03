# Multi-Repo LLM Code Update Tool

This tool automates code changes across multiple Git repositories by:
- Cloning or updating repositories locally.
- Creating a new branch for changes.
- Using an LLM (e.g., OpenAI GPT) to modify specified files.
- Committing and pushing changes.
- Opening a pull request for each repository.

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

- Ensure you have an OpenAI API key.  
- Optionally set your GitHub token in an environment variable:
  ```bash
  export GITHUB_TOKEN=<YOUR_GITHUB_PERSONAL_ACCESS_TOKEN>
  ```
  or use any other token approach your organization requires.

## Usage

Example:
```bash
python main.py \
    --repos "https://github.com/user/repo1.git,https://github.com/user/repo2.git" \
    --files "src/app.py" \
    --prompt "Update the dependency version to 1.2.3" \
    --branch-name "update-dependency" \
    --pr-title "Dependency Update" \
    --pr-body "This PR updates the dependency to version 1.2.3"
```

## Features

1. **Multiple Repo Handling**  
   - Clones or updates each repository.  
   - Creates a dedicated branch for changes.  

2. **LLM Integration**  
   - Sends the file content and prompt to the LLM for suggestions.  
   - Validates returned suggestions (e.g., Python syntax check).  

3. **Pull Request Creation**  
   - Opens a PR automatically via GitHub REST API (or other providers, if extended).  

4. **Error Handling & Logging**  
   - Logs all operations to a `logs/` directory.  
   - Retries or gracefully exits on critical errors.  

