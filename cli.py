import click
import json
import os
import logging

@click.command()
@click.option('--repos', help="Comma-separated list of Git repository URLs.")
@click.option('--config-file', default="workspace-config.json", help="Path to JSON config file containing 'workspace' and 'repos'.")
@click.option('--files', required=True, help="Comma-separated list of file paths to edit.")
@click.option('--prompt', required=True, help="Prompt instructions for the LLM.")
@click.option('--branch-name', required=True, help="Branch name to create for the updates.")
@click.option('--pr-title', required=True, help="Title for the pull request.")
@click.option('--pr-body', required=True, help="Body description for the pull request.")
@click.option('--dry-run', is_flag=True, default=False, help="Run steps without pushing or creating PR.")
def main(repos, config_file, files, prompt, branch_name, pr_title, pr_body, dry_run):
    """
    CLI entry point for the Multi-Repo LLM Code Update Tool.
    """
    # Determine the repository list: either from --config-file or from --repos
    if config_file:
        # Read the JSON configuration file.
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            raise click.BadParameter(f"Failed to read config file: {e}")
        workspace = config.get("workspace")
        repo_names = config.get("repos")
        if not workspace or not repo_names:
            raise click.BadParameter("Config file must contain both 'workspace' and 'repos' keys.")
        # Build full repository paths.
        repo_list = [os.path.join(workspace, repo_name) for repo_name in repo_names]
    elif repos:
        repo_list = [r.strip() for r in repos.split(',')]
    else:
        raise click.BadParameter("Either --repos or --config-file must be provided.")
    
    logging.debug(f"Using repositories from config file: {repo_list}")

    file_list = [f.strip() for f in files.split(',')]

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

if __name__ == "__main__":
    main()
