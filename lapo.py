import json
import os
import sys
import docs_search_agent
import generate_patch_agent
import git_pr
from rich import print as rprint
from rag import DEFAULT_PLUGIN_TOOLS_REPO_PATH
from create_pr_from_patch import create_pr_from_patch


def lapo(pr_url: str) -> None:
    # Some sanity checks
    for ev in ("ANTHROPIC_API_KEY", "GITHUB_TOKEN"):
        if os.environ.get(ev) is None:
            raise ValueError(f"{ev} not set")

    # Ensure the vector db file exists
    docs_search_deps = docs_search_agent.deps()
    if not os.path.isfile(docs_search_deps.vectordb_memory.memory_file):
        raise ValueError("Vectordb memory file not found")

    # Ensure plugin-tools repo exists
    if not os.path.isdir(DEFAULT_PLUGIN_TOOLS_REPO_PATH):
        raise ValueError("plugin-tools repo not found")
    
    print("Running against PR", pr_url)
    pr_diff_hunk = git_pr.get_pr_diff_hunk(pr_url)
    rprint(pr_diff_hunk)

    docs_search_response = docs_search_agent.agent.run_sync(
        docs_search_agent.question(pr_diff_hunk), deps=docs_search_deps
    )
    rprint("docs search agent result", docs_search_response.data)

    patch_agent_response = generate_patch_agent.generate_pr_agent.run_sync(
        json.dumps([x.model_dump() for x in docs_search_response.data]),
        deps=generate_patch_agent.Deps(docs_repo_path=DEFAULT_PLUGIN_TOOLS_REPO_PATH),
    )
    rprint(patch_agent_response)

    rprint(patch_agent_response.data)
    patch = patch_agent_response.data.patch_diff

    pr_response = create_pr_from_patch(
        repo_url="https://github.com/grafana/plugin-tools/",
        reasoning=patch_agent_response.data.reasoning,
        title=patch_agent_response.data.title,
        patch=patch,
        triggered_by=pr_url,
    )

    rprint(pr_response)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python lapo.py <pr_url>")
        sys.exit(1)
    lapo(sys.argv[1])
