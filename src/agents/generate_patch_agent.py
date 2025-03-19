from posix import wait
from dataclasses import dataclass
from typing import TypedDict
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.anthropic import AnthropicModel
import os
import textwrap
from src.tools.search_replace.search_replace_validator import validate_patch as validate_patch_impl
import logging

logger = logging.getLogger(__name__)


class PullRequestContent(BaseModel):
    reasoning: str = Field(
        description="The reason behind the pull request changes",
    )
    patch_diff: str = Field(
        description="The patch diff for the pull request",
    )
    title: str = Field(
        description="The title of the pull request",
    )


class DocumentContent(TypedDict):
    file_path: str
    content: str
    exists: bool


@dataclass
class Deps:
    docs_repo_path: str


generate_patch_prompt = textwrap.dedent(
    """
    You are an expert system generating search/replace blocks for documentation based on code changes.
    You will analyze the presented list of POSSIBLE affected documents by a code change (diff)
    think carefully if the code change (diff) affects the document related  content
    you can use the full document content to better decide if the code change (diff) affects the document

    If the code changes affect the document in a way that it requires changes then you will generate a search/replace block
    to update the document.

    you must only change the content of the document that is affected by the code change (diff)
    use the `get_document` tool to get the full content of a document.
    use the `validate_patch` tool to validate the generated patch. it should return OK if the patch is valid

    Describe each change with a *SEARCH/REPLACE block* per the examples below.

    Example search/replace block:
    documents/usehooks.md
    ```markdown
    <<<<<<< SEARCH
        this is very important because the function `useHooks` is used in a lot of places
    =======
        this is very important because the function `useHooksLegacy` is used in a lot of places
    >>>>>>> REPLACE
    ```

    # *SEARCH/REPLACE block* Rules:

    Every *SEARCH/REPLACE block* must use this format:
    1. The *FULL* file path alone on a line, verbatim. No bold asterisks, no quotes around it, no escaping of characters, etc.
    2. The opening fence and code language, eg: ```
    3. The start of search block: <<<<<<< SEARCH
    4. A contiguous chunk of lines to search for in the existing source code
    5. The dividing line: =======
    6. The lines to replace into the source code
    7. The end of the replace block: >>>>>>> REPLACE
    8. The closing fence: ```

    Use the *FULL* file path, as shown to you by the user.

    Every *SEARCH* section must *EXACTLY MATCH* the existing file content, character for character, including all comments, docstrings, etc.
    If the file contains code or other data wrapped/escaped in json/xml/quotes or other containers, you need to propose edits to the literal contents of the file, including the container markup.

    *SEARCH/REPLACE* blocks will *only* replace the first match occurrence.
    Including multiple unique *SEARCH/REPLACE* blocks if needed.
    Include enough lines in each SEARCH section to uniquely match each set of lines that need to change.

    Keep *SEARCH/REPLACE* blocks concise.
    Break large *SEARCH/REPLACE* blocks into a series of smaller blocks that each change a small portion of the file.
    Include just the changing lines, and a few surrounding lines if needed for uniqueness.
    Do not include long runs of unchanging lines in *SEARCH/REPLACE* blocks.

    Only create *SEARCH/REPLACE* blocks for files passed to you.
    """
)


generate_patch_agent = Agent(
    AnthropicModel("claude-3-5-sonnet-latest"),
    # GeminiModel('gemini-2.0-flash'),  # gemini sucks at generating patches
    retries=3,
    deps_type=Deps,
    system_prompt=generate_patch_prompt,
    result_type=PullRequestContent,
)


@generate_patch_agent.tool(retries=5)
async def get_document(ctx: RunContext[Deps], file_name: str) -> DocumentContent:
    logger.info(f"get_document {file_name}")
    file_path = os.path.join(ctx.deps.docs_repo_path, file_name)
    if not os.path.exists(file_path):
        return {"file_path": file_name, "content": "", "exists": False}
    with open(file_path, "r") as f:
        return {"file_path": file_name, "content": f.read(), "exists": True}


@generate_patch_agent.result_validator
async def validate_patch(result: PullRequestContent) -> PullRequestContent:
    logger.info("validating patch")
    try:
        is_ok = validate_patch_impl(result.patch_diff)
        if is_ok == "OK":
            logger.info("Patch is valid")
            return result
        raise ModelRetry("Patch is invalid")
    except Exception as e:
        logger.error(f"validate_patch exception: {e}")
        raise ModelRetry(str(e))
