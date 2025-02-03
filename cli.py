import click
import json
import os
import logging

@click.group()
def cli():
    """Multi-Repo LLM Code Update Tool"""
    pass

@cli.command("run")
@click.option('--repos', help="Comma-separated list of Git repository URLs.")
@click.option('--config-file', default="workspace-config.json", help="Path to JSON config file containing 'workspace' and 'repos'.")
@click.option('--files', required=True, help="Comma-separated list of file paths to edit.")
@click.option('--prompt', required=True, help="Prompt instructions for the LLM.")
@click.option('--branch-name', required=True, help="Branch name to create for the updates.")
@click.option('--pr-title', required=True, help="Title for the pull request.")
@click.option('--pr-body', required=True, help="Body description for the pull request.")
@click.option('--dry-run', is_flag=True, default=False, help="Run steps without pushing or creating PR.")
def run(repos, config_file, files, prompt, branch_name, pr_title, pr_body, dry_run):
    """
    Run the multi-repo update workflow.
    """
    # Determine the repository list: either from --config-file or from --repos.
    if config_file:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            raise click.BadParameter(f"Failed to read config file: {e}")
        workspace = config.get("workspace")
        repo_names = config.get("repos")
        if not workspace or not repo_names:
            raise click.BadParameter("Config file must contain both 'workspace' and 'repos' keys.")
        repo_list = [os.path.join(workspace, repo_name) for repo_name in repo_names]
    elif repos:
        repo_list = [r.strip() for r in repos.split(',')]
    else:
        raise click.BadParameter("Either --repos or --config-file must be provided.")

    file_list = [f.strip() for f in files.split(',')]
    logging.debug(f"Using repositories: {repo_list}")
    logging.debug(f"Files to edit: {file_list}")
    
    # Pass data to the main workflow function.
    from main import run_workflow
    run_workflow(
        repo_list=repo_list,
        file_list=file_list,
        llm_prompt=prompt,
        branch_name=branch_name,
        pr_title=pr_title,
        pr_body=pr_body,
        dry_run=dry_run
    )

@cli.command("undo")
@click.option('--repos', help="Comma-separated list of Git repository URLs.")
@click.option('--config-file', default="workspace-config.json", help="Path to JSON config file containing 'workspace' and 'repos'.")
@click.option('--branch-name', required=True, help="Name of the branch to delete (undo changes).")
@click.option('--restore-files', help="Comma-separated list of file paths to restore to HEAD (default branch).")
def undo(repos, config_file, branch_name, restore_files):
    """
    Undo the changes made by the tool by deleting the created branch in each repository
    and restoring specified files to their state in the default branch.
    """
    if config_file:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            raise click.BadParameter(f"Failed to read config file: {e}")
        workspace = config.get("workspace")
        repo_names = config.get("repos")
        if not workspace or not repo_names:
            raise click.BadParameter("Config file must contain both 'workspace' and 'repos' keys.")
        repo_list = [os.path.join(workspace, repo_name) for repo_name in repo_names]
    elif repos:
        repo_list = [r.strip() for r in repos.split(',')]
    else:
        raise click.BadParameter("Either --repos or --config-file must be provided.")

    restore_list = None
    if restore_files:
        restore_list = [f.strip() for f in restore_files.split(',')]
    
    from main import undo_workflow
    undo_workflow(repo_list, branch_name, restore_list)

if __name__ == "__main__":
    cli()