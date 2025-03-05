import docs_search_agent
import git_pr
from rich import print as rprint
from pydantic_ai.usage import Usage


def lapo() -> None:
    pr_diff_hunk = git_pr.get_pr_diff_hunk("https://github.com/grafana/grafana-plugin-examples/pull/482")
    rprint(pr_diff_hunk)
    q = docs_search_agent.question(pr_diff_hunk)
    print(q)
    docs_search_result = docs_search_agent.agent.run_sync(
        q, deps=docs_search_agent.deps()
    )
    rprint("docs search agent result", docs_search_result.data)


if __name__ == "__main__":
    lapo()
