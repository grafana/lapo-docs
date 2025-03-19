import subprocess
import os
import hashlib
import re
from github import Github, Auth

DIFF_CONTEXT_SIZE = 32
MAIN_BRANCH = "main"


def get_pr_diff_hunk(pr_url: str) -> str:
    """Get PR changes from GitHub API"""
    match = re.search(r"github.com/(.+)/(.+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError("Invalid PR URL")

    owner, repo_name, pr_number = match.groups()
    tok = os.getenv("GITHUB_TOKEN")
    if tok is None:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    g = Github(auth=Auth.Token(tok))
    repo = g.get_repo(f"{owner}/{repo_name}")
    pull = repo.get_pull(int(pr_number))

    clone_path = clone_or_update_github_repo(repo.clone_url, pull.head.ref)
    result = subprocess.run(
        ["git", "-C", clone_path, "diff", f"-U{DIFF_CONTEXT_SIZE}", f"{MAIN_BRANCH}..."],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        check=True,
    )
    # curious name but apparently that's how it's called
    hunk = result.stdout.decode()
    return hunk


def clone_or_update_github_repo(
    github_url: str, branch: str, base_path: str | None = None
) -> str:
    """
    Clones a GitHub repository in a specific branch to a deterministic path or updates it if exists.

    Args:
        github_url (str): The GitHub repository URL
        branch (str): The branch name to clone
        base_path (str): Base directory for cloning. Defaults to system temp directory

    Returns:
        str: Path to the directory containing the cloned repository

    Raises:
        subprocess.CalledProcessError: If the git command fails
    """
    # Create a deterministic directory name based on the repo URL and branch
    repo_hash = hashlib.sha256(f"{github_url}:{branch}".encode()).hexdigest()[:16]

    # Use provided base_path or system temp directory
    if base_path is None:
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
                    # "--depth=1",
                    "--branch",
                    branch,
                    github_url,
                    repo_path,
                ],
                stderr=subprocess.STDOUT,
                check=True,
            )
        else:
            # If repository exists, fetch and reset to origin/branch
            subprocess.run(
                ["git", "-C", repo_path, "fetch", "origin", branch],
                stderr=subprocess.STDOUT,
                check=True,
            )

            subprocess.run(
                ["git", "-C", repo_path, "reset", "--hard", f"origin/{branch}"],
                stderr=subprocess.STDOUT,
                check=True,
            )

            # Clean any untracked files
            subprocess.run(
                ["git", "-C", repo_path, "clean", "-fd"],
                stderr=subprocess.STDOUT,
                check=True,
            )

            subprocess.run(
                ["git", "-C", repo_path, "fetch", "origin", f"{MAIN_BRANCH}"],
                stderr=subprocess.STDOUT,
                check=True,
            )

        return repo_path

    except subprocess.CalledProcessError as e:
        # Clean up the directory if clone fails and it was a new clone
        if os.path.exists(repo_path) and not os.listdir(repo_path):
            import shutil

            shutil.rmtree(repo_path)
        raise e
