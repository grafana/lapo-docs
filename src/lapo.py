import json
import re
import logging
from rich import print as rprint
from src.functions import git_pr
from src.agents import docs_search_agent
from src.agents import generate_patch_agent
from src.rag.rag import DEFAULT_PLUGIN_TOOLS_REPO_PATH
from src.tools.search_replace.search_replace_apply import generate_git_patch_from_search_replace
from src.functions import create_pr_from_patch

# Configure once at program start
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


def lapo() -> None:
    pr_link = "https://github.com/grafana/grafana-plugin-examples/pull/482"
    logger.info(f"Processing PR: {pr_link}")

    pr_diff_hunk = git_pr.get_pr_diff_hunk(pr_link)
    logger.info("Got PR diff hunk")

    logger.info("Running docs search agent")
    docs_search_response = docs_search_agent.agent.run_sync(
        docs_search_agent.question(pr_diff_hunk), deps=docs_search_agent.deps()
    )
    logger.info(f"Got docs search response with docs: {len(docs_search_response.data)}")

    logger.info("Running generate patch agent")
    patch_agent_response = generate_patch_agent.generate_patch_agent.run_sync(
        json.dumps([x.model_dump() for x in docs_search_response.data]),
        deps=generate_patch_agent.Deps(docs_repo_path=DEFAULT_PLUGIN_TOOLS_REPO_PATH),

    )
    logger.info("Got patch agent response")

    patch = patch_agent_response.data.patch_diff

    # remove all whitespaces and new lines, if === 0 early exit 0
    clean_patch = re.sub(r'\s+', '', patch)
    if len(clean_patch) == 0:
        logger.info("No changes detected")
        exit(0)

    logger.info("generating git patch")
    git_patch = generate_git_patch_from_search_replace(DEFAULT_PLUGIN_TOOLS_REPO_PATH, patch)
    logger.info("Generated git patch")

    rprint(patch)
    rprint(git_patch)

    logger.info("Creating PR")
    pr_response = create_pr_from_patch.create_pr_from_patch(
        repo_url="https://github.com/grafana/plugin-tools/",
        reasoning=patch_agent_response.data.reasoning,
        title=patch_agent_response.data.title,
        patch=git_patch,
        triggered_by=pr_link,
    )

    logger.info("Created PR")
    rprint(pr_response)


if __name__ == "__main__":
    lapo()
