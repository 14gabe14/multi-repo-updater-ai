import pytest
from click.testing import CliRunner
from cli import main

def test_cli_required_arguments():
    """
    Test that missing required arguments result in an error.
    """
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code != 0
    assert "Missing option" in result.output

def test_cli_success():
    """
    Test that valid arguments trigger the correct parse.
    """
    runner = CliRunner()
    result = runner.invoke(main, [
        "--repos", "repo1,repo2",
        "--files", "file1,file2",
        "--prompt", "Update version",
        "--branch-name", "test-branch",
        "--pr-title", "Test PR",
        "--pr-body", "Body of PR"
    ])
    assert result.exit_code == 0
    # We cannot fully verify side effects here,
    # but we can confirm no parse errors occurred.
