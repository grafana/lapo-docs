import inspect
import os
import subprocess
import tempfile
import requests
import re
import logging
from src.functions.git_pr import clone_or_update_github_repo

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
logger = logging.getLogger(__name__)


def create_pr_from_patch(
    repo_path: str | None = None,
    repo_url: str | None = None,
    branch_name: str | None = None,
    reasoning: str | None = None,
    title: str | None = None,
    patch: str | None = None,
    triggered_by: str | None = None,
):

    logger.info(f"repo_path: {repo_path}")
    logger.info(f"repo_url: {repo_url}")
    logger.info(f"branch_name: {branch_name}")
    logger.info(f"reasoning: {reasoning}")
    logger.info(f"title: {title}")
    logger.info(f"patch: {patch}")
    logger.info(f"triggered_by: {triggered_by}")

    if repo_url is None or patch is None or reasoning is None:
        raise ValueError("repoUrl, patch and description must be provided")

    # Extract owner and repo name from repo URL
    # Format: https://github.com/owner/repo.git or git@github.com:owner/repo.git
    owner_repo_match = re.search(r"github\.com[/:]([\w-]+)/([\w-]+)(\.git)?", repo_url)
    if not owner_repo_match:
        raise ValueError(f"Could not extract owner and repo from URL: {repo_url}")

    owner = owner_repo_match.group(1)
    repo = owner_repo_match.group(2)

    if repo_path is not None or repo_path == "":
        # check repoPath exists
        if not os.path.exists(repo_path):
            raise ValueError("repoPath does not exist")
        # check repoPath is a git repo
        if not os.path.exists(os.path.join(repo_path, ".git")):
            raise ValueError("repoPath is not a git repo")
    else:
        try:
            repo_path = clone_or_update_github_repo(repo_url)
        except Exception as e:
            raise ValueError(f"Failed to clone repo {repo_url}: {e}")

    if branch_name is None or branch_name == "":
        random_name = os.urandom(16).hex()
        branch_name = f"lapo-docs-{random_name}"

    if triggered_by is None or triggered_by == "":
        triggered_by = "No information provided"

    # store patch in a temporal file
    with tempfile.NamedTemporaryFile("w") as f:
        f.write(patch)
        f.flush()
        logger.info(f"patch {f.name}")
        try:
            logger.info(f"repo_path {repo_path}")
            # first checkout to main and pull
            result = subprocess.run(["git", "checkout", "main"], cwd=repo_path, check=True)
            logger.info(f"checkout {result}")
            result = subprocess.run(["git", "pull", "origin", "main"], cwd=repo_path, check=True)
            logger.info(f"pull {result}")

            result = subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_path, check=True)
            logger.info(f"checkout {result}")
            result = subprocess.run(["git", "apply", "--check", f.name], cwd=repo_path, capture_output=True, check=True)
            logger.info(f"patch valid {result}")

            # Actually apply the patch after validation
            result = subprocess.run(["git", "apply", f.name], cwd=repo_path, capture_output=True, check=True)
            logger.info(f"patch applied {result}")

            result = subprocess.run(
                ["git", "commit", "-a", "-m", reasoning], cwd=repo_path, capture_output=True, check=True
            )
            logger.info(f"commit {result}")
            result = subprocess.run(
                ["git", "push", "-f", "origin", branch_name], cwd=repo_path, capture_output=True, check=True
            )

            logger.info(f"push {result}")

        except subprocess.CalledProcessError as e:
            logger.error(f"error with patch {e.stderr if hasattr(e, 'stderr') else str(e)}")
            # write patch into a more permanent file
            with open(f"/tmp/{branch_name}.patch", "w") as f:
                f.write(patch)
            logger.error(f"patch written to /tmp/{branch_name}.patch")
            raise ValueError("error validating patch: " + str(e.stderr))
        except Exception as e:
            logger.error(f"Error creating PR: {str(e)}")
            raise ValueError(f"Error creating PR: {str(e)}")

    # Create the pull request
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    pr_title = "LapoDocs: "
    if title is not None:
        pr_title += title
    else:
        pr_title += "Update docs from changes in related code"

    description = inspect.cleandoc(f"""

        This is an automated pull request created by the [LapoDocs](https://github.com/grafana/llm-auto-update-docs) tool.

        ## Reasoning for the changes:

        {reasoning}

        ## PR that triggered these changes:

        {triggered_by}
""")

    pr_data = {"title": pr_title, "body": description, "head": branch_name, "base": "main"}
    logger.debug(pr_data)

    response = requests.post(f"https://api.github.com/repos/{owner}/{repo}/pulls", headers=headers, json=pr_data)

    if response.status_code != 201:
        raise ValueError(f"Failed to create PR: {response.status_code} - {response.text}")

    pr_info = response.json()

    # Add labels to the PR
    pr_number = pr_info["number"]
    labels_data = {"labels": ["lapo-docs", "type-docs", "no-changelog"]}
    label_response = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/labels", headers=headers, json=labels_data
    )

    if label_response.status_code != 200:
        logger.warning(f"Failed to add labels to PR: {label_response.status_code} - {label_response.text}")

    logger.info(f"PR created: {pr_info['html_url']}")

    return {"status": "success", "branch": branch_name, "pr_url": pr_info["html_url"]}
