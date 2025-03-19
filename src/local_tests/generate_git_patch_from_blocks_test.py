import sys
import logging
from pathlib import Path
import textwrap

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.tools.search_replace.search_replace_apply import generate_git_patch_from_search_replace
from src.rag.rag import DEFAULT_PLUGIN_TOOLS_REPO_PATH

logger = logging.getLogger(__name__)


def main() -> None:
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Example search/replace blocks
    blocks = textwrap.dedent("""
    src/data.ts
    ```
    <<<<<<< SEARCH
    export const metadata = {
        id: "my-plugin",
        name: "My Plugin",
        version: "1.0.0"
    };
    =======
    export const metadata = {
        id: "my-plugin",
        name: "My Plugin",
        version: "1.1.0"  // Updated version
    };
    >>>>>>> REPLACE
    ```
    """)

    patch = generate_git_patch_from_search_replace(DEFAULT_PLUGIN_TOOLS_REPO_PATH, blocks)
    logger.info(patch)


if __name__ == "__main__":
    main()
