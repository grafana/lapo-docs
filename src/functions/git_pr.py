import subprocess
import os
import hashlib
import requests
import re
from github import Github, Auth
import logging

logger = logging.getLogger(__name__)

DIFF_CONTEXT_SIZE = 32
MAIN_BRANCH = "main"


def get_pr_diff_hunk(pr_url: str) -> str:
    """Get PR changes directly from GitHub PR patch URL"""
    match = re.search(r"github.com/(.+)/(.+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError("Invalid PR URL")

    owner, repo_name, pr_number = match.groups()

    # Construct the patch URL
    patch_url = f"https://github.com/{owner}/{repo_name}/pull/{pr_number}.patch"

    # Use requests to fetch the patch
    token = os.getenv("GITHUB_TOKEN")
    if token is None or token == "":
        raise ValueError("GITHUB_TOKEN environment variable not set")

    headers = {"Authorization": f"token {token}"}

    logger.info(f"Fetching PR patch from {patch_url}")
    response = requests.get(patch_url, headers=headers)
    response.raise_for_status()

    # The patch content contains the diff with sufficient context
    hunk = response.text

    return hunk


def clone_or_update_github_repo(
    github_url: str, branches: list[str] = [MAIN_BRANCH]
) -> str:
    """
    Clones a GitHub repository in a specific branch to a deterministic path or updates it if exists.

    Args:
        github_url (str): The GitHub repository URL
        branch list[str]: List of branches to clone

    Returns:
        str: Path to the directory containing the cloned repository

    Raises:
        subprocess.CalledProcessError: If the git command fails
    """
    # Create a deterministic directory name based on the repo URL and branch
    repo_hash = hashlib.sha256(f"{github_url}".encode()).hexdigest()[:16]

    github_token = os.getenv("GITHUB_TOKEN")
    if github_token is None:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    auth_github_url = get_authenticated_github_url(github_url)

    # Use provided base_path or system temp directory
    base_path = os.path.join(os.path.expanduser("~"), ".cache", "github_repos")

    # Create the base directory if it doesn't exist
    os.makedirs(base_path, exist_ok=True)

    repo_path = os.path.join(base_path, repo_hash)

    try:
        if not os.path.exists(repo_path):
            # Clone the repository if it doesn't exist
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth=50",  # can't use depth=1 because we need the branches
                    "--branch",
                    MAIN_BRANCH,
                    auth_github_url,
                    repo_path,
                ],
                stderr=subprocess.STDOUT,
                check=True,
            )

        # Clean any untracked files
        subprocess.run(
            ["git", "-C", repo_path, "clean", "-fd"],
            stderr=subprocess.STDOUT,
            check=True,
        )

        # For each branch you want to fetch
        for branch in branches:
            logger.info(f"Fetching branch {branch}")
            # Set up remote tracking for the branch
            subprocess.run(
                ["git", "-C", repo_path, "remote", "set-branches", "--add", "origin", branch],
                stderr=subprocess.STDOUT,
                check=True,
            )

            # Fetch the specific branch with depth=1
            subprocess.run(
                ["git", "-C", repo_path, "fetch", "--depth=50", "origin", branch],
                stderr=subprocess.STDOUT,
                check=True,
            )
            logger.info(f"Successfully fetched branch {branch}")

        # finally checkout to branch
        logger.info(f"Checking out branch {branches[0]}")
        subprocess.run(
            ["git", "-C", repo_path, "checkout", branches[0]],
            stderr=subprocess.STDOUT,
            check=True,
        )
        logger.info(f"Successfully checked out branch {branches[0]}")

        return repo_path

    except subprocess.CalledProcessError as e:
        # Clean up the directory if clone fails and it was a new clone
        if os.path.exists(repo_path) and not os.listdir(repo_path):
            import shutil

            shutil.rmtree(repo_path)
        raise e


def get_authenticated_github_url(url):
    # Extract the repository path from the URL
    match = re.match(r'https://github.com/(.+?)(?:\.git)?$', url)
    if not match:
        raise ValueError(f"Invalid GitHub URL: {url}")

    repo_path = match.group(1)

    # Get the GitHub token from environment variable
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    # Construct the authenticated URL
    return f"https://x-access-token:{github_token}@github.com/{repo_path}.git"
