import json
import docs_search_agent
import generate_patch_agent
import git_pr
from rich import print as rprint
from rag import DEFAULT_PLUGIN_TOOLS_REPO_PATH
from create_pr_from_patch import create_pr_from_patch


def lapo() -> None:
    pr_link = "https://github.com/grafana/grafana-plugin-examples/pull/482"

    pr_diff_hunk = git_pr.get_pr_diff_hunk(pr_link)
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
    patch = patch_agent_response.data.patch_diff

    pr_response = create_pr_from_patch(
        repo_url="https://github.com/grafana/plugin-tools/",
        reasoning=patch_agent_response.data.reasoning,
        title=patch_agent_response.data.title,
        patch=patch,
        triggered_by=pr_link,
    )

    rprint(pr_response)


if __name__ == "__main__":
    lapo()
