import os
import subprocess
import tempfile
import requests
import re
from git_pr import clone_or_update_github_repo

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def create_pr_from_patch(
        repo_path: str,
        repo_url: str,
        branch_name: str,
        description: str,
        patch: str
):

    if repo_url is None or patch is None or description is None:
        raise ValueError("repoUrl, patch and description must be provided")

    # Extract owner and repo name from repo URL
    # Format: https://github.com/owner/repo.git or git@github.com:owner/repo.git
    owner_repo_match = re.search(r'github\.com[/:]([\w-]+)/([\w-]+)(\.git)?', repo_url)
    if not owner_repo_match:
        raise ValueError(f"Could not extract owner and repo from URL: {repo_url}")

    owner = owner_repo_match.group(1)
    repo = owner_repo_match.group(2)

    if repo_path is not None or repo_path != "":
        # check repoPath exists
        if not os.path.exists(repo_path):
            raise ValueError("repoPath does not exist")
        # check repoPath is a git repo
        if not os.path.exists(os.path.join(repo_path, ".git")):
            raise ValueError("repoPath is not a git repo")
    else:
        try:
            repo_path = clone_or_update_github_repo(repo_url, "main")
        except Exception as e:
            raise ValueError(f"Failed to clone repo {repo_url}: {e}")

    if branch_name is None or branch_name == "":
        random_name = os.urandom(16).hex()
        branch_name = f"lapo-docs-{random_name}"

    # store patch in a temporal file
    with tempfile.NamedTemporaryFile("w") as f:
        f.write(patch)
        f.flush()
        print("patch", f.name)
        try:
            result = subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_path, check=True)
            print("checkout", result)
            result = subprocess.run(["git", "apply", "--check", f.name],
                                    cwd=repo_path,
                                    capture_output=True,
                                    check=True)
            print("patch valid", result)

            # Actually apply the patch after validation
            result = subprocess.run(["git", "apply", f.name],
                                    cwd=repo_path,
                                    capture_output=True,
                                    check=True)
            print("patch applied", result)

            result = subprocess.run(["git", "commit", "-a", "-m", description],
                                    cwd=repo_path,
                                    capture_output=True,
                                    check=True)
            print("commit", result)
            result = subprocess.run(["git", "push", "-f", "origin", branch_name],
                                    cwd=repo_path,
                                    capture_output=True,
                                    check=True)

            print("push", result)

        except subprocess.CalledProcessError as e:
            print("error with patch", e.stderr if hasattr(e, 'stderr') else str(e))
            raise ValueError("error validating patch: " + str(e.stderr))
        except Exception as e:
            print("Error creating PR:", str(e))
            raise ValueError(f"Error creating PR: {str(e)}")

    # Create the pull request
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    pr_data = {
        "title": 'LapoDocs: Update docs from changes in related code',
        "body": description,
        "head": branch_name,
        "base": "main"
    }

    response = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers=headers,
        json=pr_data
    )

    if response.status_code != 201:
        raise ValueError(f"Failed to create PR: {response.status_code} - {response.text}")

    pr_info = response.json()
    print("PR created:", pr_info["html_url"])

    return {"status": "success", "branch": branch_name, "pr_url": pr_info["html_url"]}
