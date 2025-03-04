import subprocess
from pydantic import BaseModel
from typing import List
import os
import hashlib
import re
from github import Github
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from rich import print as rprint


class CodeChange(BaseModel):
    file_path: str
    diff_hunk: str
    start_line: int
    end_line: int
    ten_lines_before_patch: List[str]
    ten_lines_after_patch: List[str]
    patch_diff: str


pr_agent = Agent(
    GeminiModel('gemini-2.0-flash'),
    deps_type=str,
    system_prompt=(
        'You are an expert at parsing git diffs and PRs (pull requests)',
        'Use the get_pr tool to get the PR changes and the file full contents',
        'return a list of code changes with the file path, diff hunk, start line, end line, and 10 lines before and 10 lines after the change'
    ),
    result_type=List[CodeChange],
)


@pr_agent.tool
async def get_pr(ctx: RunContext[str], pr_url: str) -> List[dict]:
    """Get PR changes from GitHub API"""
    match = re.search(r"github.com/(.+)/(.+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError("Invalid PR URL")

    owner, repo_name, pr_number = match.groups()
    g = Github(auth=os.getenv('GITHUB_TOKEN'))
    repo = g.get_repo(f"{owner}/{repo_name}")
    pull = repo.get_pull(int(pr_number))

    clone_path = clone_or_update_github_repo(repo.clone_url, pull.head.ref)

    diff = []
    for file in pull.get_files():
        file_path = os.path.join(clone_path, file.filename)
        try:
            with open(file_path, "r") as f:
                file_contents = f.read()
        except FileNotFoundError:
            file_contents = ""

        diff.append(
            {
                "file_path": file.filename,
                "patch": file.patch,
                "file_full_contents": file_contents
            }
        )

    return diff


def clone_or_update_github_repo(github_url: str, branch: str, base_path: str = None) -> str:
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
            subprocess.check_call([
                'git',
                'clone',
                '--depth=1',
                '--branch', branch,
                github_url,
                repo_path
            ], stderr=subprocess.STDOUT)
        else:
            # If repository exists, fetch and reset to origin/branch
            subprocess.check_call([
                'git',
                '-C', repo_path,
                'fetch',
                'origin',
                branch
            ], stderr=subprocess.STDOUT)

            subprocess.check_call([
                'git',
                '-C', repo_path,
                'reset',
                '--hard',
                f'origin/{branch}'
            ], stderr=subprocess.STDOUT)

            # Clean any untracked files
            subprocess.check_call([
                'git',
                '-C', repo_path,
                'clean',
                '-fd'
            ], stderr=subprocess.STDOUT)

        return repo_path

    except subprocess.CalledProcessError as e:
        # Clean up the directory if clone fails and it was a new clone
        if os.path.exists(repo_path) and not os.listdir(repo_path):
            import shutil
            shutil.rmtree(repo_path)
        raise e


if __name__ == "__main__":
    # changes = await analyze_pr("https://github.com/owner/repo/pull/123")
    result = pr_agent.run_sync("return changes for https://github.com/grafana/grafana-plugin-examples/pull/482")
    # pprint.PrettyPrinter(indent=4).pprint(result)
    rprint(result)
    pass
