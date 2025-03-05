import docs_search_agent
import gitpr_agent
from rich import print as rprint
from pydantic_ai.usage import Usage


def lapo() -> None:
    q = "return changes for https://github.com/grafana/grafana-plugin-examples/pull/482"
    gitpr_result = gitpr_agent.pr_agent.run_sync(q)
    rprint("git pr agent result", gitpr_result.data)

    q = docs_search_agent.question(gitpr_result.data)
    docs_search_result = docs_search_agent.agent.run_sync(
        q, deps=docs_search_agent.deps()
    )
    rprint("docs search agent result", docs_search_result.data)


if __name__ == "__main__":
    lapo()
