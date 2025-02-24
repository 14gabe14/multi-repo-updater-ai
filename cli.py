# cli.py

import click
import yaml
import os
import shutil
import logging

def load_config(config_file):
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        raise click.BadParameter(f"Failed to read config file: {e}")

@click.group()
def cli():
    """Multi-Repo LLM Code Update Tool"""
    pass

def get_repo_path(repo_config, global_directory, sandbox_path=None):
    """
    Determine the local repository path based on configuration.
    If sandbox_path is provided, always use that (sandbox_path + repo name),
    ignoring any repository-specific directory setting.
    Otherwise, if the repo config has a 'directory' field:
      - If it's absolute and its basename doesn't match the repo name,
        assume the repo is located in a subfolder named after the repo.
      - Otherwise, join the global directory with the repo's name.
    """
    repo_name = repo_config.get("name")
    if sandbox_path:
        return os.path.join(sandbox_path, repo_name)
    else:
        if "directory" in repo_config:
            repo_path = repo_config["directory"]
            if os.path.isabs(repo_path):
                # Check if the provided directory's basename is the same as the repo name.
                if os.path.basename(os.path.normpath(repo_path)) != repo_name:
                    # Append the repo name to form the full path.
                    return os.path.join(repo_path, repo_name)
                else:
                    return repo_path
            else:
                return os.path.join(global_directory, repo_path)
        else:
            return os.path.join(global_directory, repo_name)

@cli.command("run")
@click.option('--subset', default="", help="Comma-separated list of repo names or tags to process (if empty, use all repos).")
@click.option('--repos', help="Override repo config with a comma-separated list of repository paths.")
@click.option('--config-file', default="workspace-config.yaml", help="Path to YAML config file containing global and repos info.")
@click.option('--files', required=True, help="Comma-separated list of file paths to edit relative to each repo.")
@click.option('--prompt', required=True, help="Prompt instructions for the LLM.")
@click.option('--branch-name', required=True, help="Branch name to create for the updates.")
@click.option('--pr-title', required=True, help="Title for the pull request.")
@click.option('--pr-body', required=True, help="Body description for the pull request.")
@click.option('--dry-run', is_flag=True, default=False, help="Run steps without pushing or creating PR.")
@click.option('--repo-path', default="", help="Override a specific repository path. (Optional)")
@click.option('--sandbox-path', default=None, help="Force all repositories to be treated as if they are in the specified sandbox directory.")
def run(subset, repos, config_file, files, prompt, branch_name, pr_title, pr_body, dry_run, repo_path, sandbox_path):
    """
    Run the multi-repo update workflow.
    """
    config = load_config(config_file)
    global_conf = config.get("global", {})
    workspace_dir = global_conf.get("directory")
    repo_configs = config.get("repos", [])

    if repo_path:
        repo_list = [repo_path]
    elif repos:
        repo_list = [r.strip() for r in repos.split(',')]
    else:
        # Build list of repository paths using get_repo_path and the sandbox override.
        full_repo_list = [get_repo_path(rc, workspace_dir, sandbox_path) for rc in repo_configs]
        if subset:
            subset_filter = [s.strip() for s in subset.split(',')]
            filtered_repos = []
            for rc in repo_configs:
                repo_name = rc.get("name")
                repo_tags = rc.get("tags", [])
                if repo_name in subset_filter or any(tag in subset_filter for tag in repo_tags):
                    filtered_repos.append(get_repo_path(rc, workspace_dir, sandbox_path))
            repo_list = filtered_repos
        else:
            repo_list = full_repo_list

    logging.debug(f"Using repositories: {repo_list}")
    logging.debug(f"Files to edit: {files}")

    from main import run_workflow
    run_workflow(
        repo_list=repo_list,
        file_list=[f.strip() for f in files.split(',')],
        llm_prompt=prompt,
        branch_name=branch_name,
        pr_title=pr_title,
        pr_body=pr_body,
        dry_run=dry_run
    )

@cli.command("undo")
@click.option('--subset', default="", help="Comma-separated list of repo names or tags to process (if empty, use all repos).")
@click.option('--repos', help="Override repo config with a comma-separated list of repository paths.")
@click.option('--config-file', default="workspace-config.yaml", help="Path to YAML config file containing global and repos info.")
@click.option('--branch-name', required=True, help="Name of the branch to delete (undo changes).")
@click.option('--restore-files', help="Comma-separated list of file paths to restore to HEAD (default branch).")
@click.option('--repo-path', default="", help="Override a specific repository path. (Optional)")
@click.option('--sandbox-path', default=None, help="Force all repositories to be treated as if they are in the specified sandbox directory.")
def undo(subset, repos, config_file, branch_name, restore_files, repo_path, sandbox_path):
    """
    Undo the changes made by the tool by deleting the created branch and optionally restoring files.
    """
    config = load_config(config_file)
    global_conf = config.get("global", {})
    workspace_dir = global_conf.get("directory")
    repo_configs = config.get("repos", [])

    if repo_path:
        repo_list = [repo_path]
    elif repos:
        repo_list = [r.strip() for r in repos.split(',')]
    else:
        full_repo_list = [get_repo_path(rc, workspace_dir, sandbox_path) for rc in repo_configs]
        if subset:
            subset_filter = [s.strip() for s in subset.split(',')]
            filtered_repos = []
            for rc in repo_configs:
                repo_name = rc.get("name")
                repo_tags = rc.get("tags", [])
                if repo_name in subset_filter or any(tag in subset_filter for tag in repo_tags):
                    filtered_repos.append(get_repo_path(rc, workspace_dir, sandbox_path))
            repo_list = filtered_repos
        else:
            repo_list = full_repo_list

    restore_list = None
    if restore_files:
        restore_list = [f.strip() for f in restore_files.split(',')]
    
    from main import undo_workflow
    undo_workflow(repo_list, branch_name, restore_list)

@cli.command("prepare")
@click.option('--config-file', default="workspace-config.yaml", help="Path to YAML config file containing global and repos info.")
@click.option('--target-path', required=True, help="Target directory where a copy of the workspace should be created.")
def prepare(config_file, target_path):
    """
    Prepare a new workspace by copying repositories from the global directory
    to a target directory. If a repository is not found locally, attempts to clone
    it using the URL specified in the configuration.
    """
    config = load_config(config_file)
    global_conf = config.get("global", {})
    workspace_dir = global_conf.get("directory")
    repo_configs = config.get("repos", [])

    os.makedirs(target_path, exist_ok=True)
    for rc in repo_configs:
        repo_name = rc.get("name")
        dest_path = os.path.join(target_path, repo_name)
        src_path = get_repo_path(rc, workspace_dir)  # Get path from config

        if os.path.exists(src_path):
            # Repository exists locally: copy it.
            try:
                if os.path.exists(dest_path):
                    click.echo(f"Repository {repo_name} already exists in target; skipping copy.")
                else:
                    shutil.copytree(src_path, dest_path)
                    click.echo(f"Copied {repo_name} from {src_path} to {dest_path}.")
            except Exception as e:
                click.echo(f"Failed to copy {repo_name}: {e}")
        else:
            # Repository not found locally, attempt to clone if URL is provided.
            if "url" in rc and rc["url"]:
                url = rc["url"]
                try:
                    from git import Repo
                    Repo.clone_from(url, dest_path)
                    click.echo(f"Cloned {repo_name} from {url} to {dest_path}.")
                except Exception as e:
                    click.echo(f"Failed to clone {repo_name} from {url}: {e}")
            else:
                click.echo(f"Source repository {repo_name} not found at {src_path} and no URL provided.")

if __name__ == "__main__":
    cli()
