#!/usr/bin/env python3
import argparse
from src.lapo import lapo


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

    lapo(docs_repo=args.docs_repo, docs_path=args.docs_path, source_change_pr=args.source_change_pr)
