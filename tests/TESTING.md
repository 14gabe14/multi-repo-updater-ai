# Testing the Multi-Repo LLM Code Update Tool

This document explains how to run the tests for the tool, including both unit tests, end-to-end (E2E) tests using mocks, and integration tests that target the real APIs.

## 1. Overview

- **Unit Tests:** Validate core functions (Git operations, LLM integration, CLI parsing) using mocks.
- **E2E Tests (Mocked):** Run the full workflow with dummy repositories while mocking external API calls.
- **Integration Tests (Real API):** Run the full workflow against the actual APIs. (These are marked with `@pytest.mark.integration` and require valid API credentials.)

## 2. Generating Dummy Repositories

A script `generate_dummy_repos.py` is provided to generate dummy Git repositories that include dependency files (e.g., `requirements.txt`, `pom.xml`, and `package.json`).

### Usage:
```bash
python generate_dummy_repos.py --target-dir /path/to/dummy_repos --num-repos 3
```
This command creates 3 dummy repositories under `/path/to/dummy_repos`, each initialized as a Git repository with the dummy files.

## 3. Running Tests

### a) Installation

Install the dependencies:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

### b) Running Unit Tests and E2E Tests with Mocks

Run:
```bash
pytest --cov=. --cov-report=term-missing -m "not integration"
```
This command runs all tests except the real API integration tests. The E2E tests in `tests/test_e2e_mocks.py` use mocks to simulate external API calls.

### c) Running Integration Tests (Real API)

Integration tests are marked with the `integration` marker. To run them, use:
```bash
pytest -m integration --cov=. --cov-report=term-missing
```
Before running these tests, ensure that your environment variables (e.g., `OPENAI_API_KEY` and `GITHUB_TOKEN`) are set to valid credentials.

## 4. Test Structure

- **`tests/test_cli.py`:** Tests for CLI parsing using Click's `CliRunner`.
- **`tests/test_git_ops.py`:** Unit tests for Git operations (clone, branch creation, commit/push) using mocks.
- **`tests/test_llm_ops.py`:** Unit tests for LLM integration functions.
- **`tests/test_e2e_mocks.py`:** E2E tests running the CLI workflow in-process with mocked API calls.
- **`tests/test_e2e_real.py`:** Integration tests running the CLI workflow with real API calls (requires valid credentials).

## 5. Adding New Test Cases

- Follow the naming convention `test_<component>.py`.
- Use Pytest fixtures for setup/teardown.
- Use `unittest.mock` for external dependency patching in unit tests.
- For integration tests, use the `@pytest.mark.integration` marker.

For further assistance, please contact the development team.
