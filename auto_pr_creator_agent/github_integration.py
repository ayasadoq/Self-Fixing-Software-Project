import os
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from github import Github
from github.GithubException import GithubException

def get_github_client() -> Optional[Github]:
    """
    Initialize and return a GitHub client using the GITHUB_TOKEN environment variable.
    """
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("Warning: GITHUB_TOKEN environment variable not set. GitHub API features will be disabled.")
        return None
    return Github(github_token)

def get_repo_info() -> Tuple[Optional[str], Optional[str]]:
    """
    Extract repository owner and name from git remote URL.
    Returns (owner, repo_name) or (None, None) if not found.
    """
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()
        
        # Handle both HTTPS and SSH URLs
        if remote_url.startswith('https://'):
            # https://github.com/owner/repo.git
            parts = remote_url.rstrip('.git').split('/')
            return parts[-2], parts[-1]
        else:
            # git@github.com:owner/repo.git
            parts = remote_url.rstrip('.git').split(':')
            owner_repo = parts[1].split('/')
            return owner_repo[0], owner_repo[1]
    except subprocess.CalledProcessError:
        print("Warning: Could not get git remote URL. GitHub API features will be disabled.")
        return None, None

def get_file_owners(file_paths: List[str], github_client: Github, repo) -> Dict[str, List[str]]:
    """
    Get the owners of files based on git blame history.
    Returns a dictionary mapping file paths to lists of usernames.
    """
    file_owners = {}
    for file_path in file_paths:
        try:
            # Get the last 10 commits that modified this file
            commits = repo.get_commits(path=file_path, per_page=10)
            owners = set()
            for commit in commits:
                if commit.author:
                    owners.add(commit.author.login)
            file_owners[file_path] = list(owners)
        except GithubException as e:
            print(f"Warning: Could not get owners for {file_path}: {e}")
            file_owners[file_path] = []
    return file_owners

def create_pull_request(
    branch_name: str,
    changes_made: Dict[str, List[str]],
    commit_message: str
) -> Optional[Dict[str, Any]]:
    """
    Create a pull request using the GitHub API.
    Returns PR information or None if creation failed.
    """
    github_client = get_github_client()
    if not github_client:
        return None

    owner, repo_name = get_repo_info()
    if not owner or not repo_name:
        return None

    try:
        repo = github_client.get_repo(f"{owner}/{repo_name}")
        
        # Get the default branch
        default_branch = repo.default_branch

        # Get file owners for reviewer assignment
        file_owners = get_file_owners(list(changes_made.keys()), github_client, repo)
        
        # Collect all unique owners
        reviewers = set()
        for owners in file_owners.values():
            reviewers.update(owners)

        # Create PR title and description
        pr_title = "Automated Code Quality Fixes"
        pr_body = f"""## Automated Code Quality Improvements

This PR contains automated fixes for code quality issues detected by our self-fixing software system.

### Changes Made:
{commit_message}

### Files Modified:
{chr(10).join(f"- {os.path.basename(path)}" for path in changes_made.keys())}

### Fixes Applied:
{chr(10).join(f"- {change}" for changes in changes_made.values() for change in changes)}

This PR was automatically created by the Self-Fixing Software Project's Auto-PR Creator Agent.
"""

        # Create the pull request
        pr = repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=branch_name,
            base=default_branch
        )

        # Add reviewers if any were found
        if reviewers:
            pr.add_to_reviewers(list(reviewers))

        # Add labels
        pr.add_to_labels("automated", "code-quality", "enhancement")

        return {
            "status": "success",
            "message": "Pull request created successfully",
            "pr_url": pr.html_url,
            "pr_number": pr.number,
            "reviewers": list(reviewers)
        }

    except GithubException as e:
        print(f"Error creating pull request: {e}")
        return {
            "status": "error",
            "message": f"Failed to create pull request: {str(e)}"
        } 