import json
import docs_search_agent
import generate_patch_agent
import git_pr
from rich import print as rprint

from rag import DEFAULT_PLUGIN_TOOLS_REPO_PATH


def lapo() -> None:
    pr_diff_hunk = git_pr.get_pr_diff_hunk(
        "https://github.com/grafana/grafana-plugin-examples/pull/482"
    )
    rprint(pr_diff_hunk)

    docs_search_response = docs_search_agent.agent.run_sync(
        docs_search_agent.question(pr_diff_hunk), deps=docs_search_agent.deps()
    )
    rprint("docs search agent result", docs_search_response.data)

    patch_agent_response = generate_patch_agent.generate_pr_agent.run_sync(
        json.dumps([x.model_dump() for x in docs_search_response.data]),
        deps=generate_patch_agent.Deps(docs_repo_path=DEFAULT_PLUGIN_TOOLS_REPO_PATH),
    )
    rprint(patch_agent_response)

    rprint(patch_agent_response.data)
    with open("test.patch", "w") as f:
        print("writing patch to test.patch")
        f.write(patch_agent_response.data.patch_diff)


if __name__ == "__main__":
    lapo()
