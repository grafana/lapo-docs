#!/usr/bin/env python3
import argparse
from src.lapo import lapo
import os
import requests
import uuid
import base64


def parse_args():
    parser = argparse.ArgumentParser(description="LAPO - Language Agent for Plugin Operations")
    parser.add_argument(
        "--docs-path",
        required=True,
        help="Path to the documentation. Relative to the root of the plugin-tools repository",
    )
    parser.add_argument("--docs-repo", required=True, help="GitHub repository link in the format owner/repo")
    parser.add_argument("--source-change-pr", required=True, help="Full URL of the source change PR")
    return parser.parse_args()


def open_dummy_pr(docs_repo: str) -> str:
    """
    Opens a dummy PR in the specified repository using GitHub's REST API.

    Args:
        docs_repo (str): GitHub repository in the format owner/repo

    Returns:
        str: URL of the created PR

    Raises:
        ValueError: If GITHUB_TOKEN is not set or if docs_repo format is invalid
    """
    token = os.getenv("GITHUB_TOKEN")
    if token is None or token == "":
        raise ValueError("GITHUB_TOKEN environment variable not set")

    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

    # Get the default branch's SHA
    base_url = f"https://api.github.com/repos/{docs_repo}"
    response = requests.get(f"{base_url}/git/refs/heads/main", headers=headers)
    response.raise_for_status()
    base_sha = response.json()["object"]["sha"]

    # Create a new branch
    new_branch = f"dummy-pr-{uuid.uuid4().hex[:8]}"
    branch_data = {"ref": f"refs/heads/{new_branch}", "sha": base_sha}
    response = requests.post(f"{base_url}/git/refs", headers=headers, json=branch_data)
    response.raise_for_status()

    # Create a dummy file
    file_content = "This is a test PR created by LAPO"
    file_data = {
        "message": "test: Add dummy file",
        "content": base64.b64encode(file_content.encode()).decode(),
        "branch": new_branch,
    }
    response = requests.put(f"{base_url}/contents/dummy-{uuid.uuid4().hex[:8]}.txt", headers=headers, json=file_data)
    response.raise_for_status()

    # Create the PR
    pr_data = {
        "title": "test: Dummy PR created by LAPO",
        "body": "This is a test PR to verify the repository access.",
        "head": new_branch,
        "base": "main",
    }
    response = requests.post(f"{base_url}/pulls", headers=headers, json=pr_data)
    response.raise_for_status()

    print(f"Dummy PR created: {response.json()['html_url']}")
    return response.json()["html_url"]


if __name__ == "__main__":
    args = parse_args()

    print("LAPO - LLM Agent Patcher of Docs")
    print(f"Docs Path: {args.docs_path}")
    print(f"Docs Repo: {args.docs_repo}")
    print(f"Source Change PR: {args.source_change_pr}")

    if args.docs_repo.startswith("http"):
        raise ValueError("Docs repo must be in the format owner/repo")

    if not args.source_change_pr.startswith("https://github.com/"):
        raise ValueError("Source change PR must be in the format https://github.com/owner/repo/pull/123")

    open_dummy_pr(args.docs_repo)
    # lapo(docs_repo=args.docs_repo, docs_path=args.docs_path, source_change_pr=args.source_change_pr)
