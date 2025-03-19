from dataclasses import dataclass
import time
from typing import Dict, Iterable, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.gemini import GeminiModel
from rich import print as rprint
from langchain_community.vectorstores import FAISS
from src.rag import rag
import logging


class RelatedDocumentationChunk(BaseModel):
    """A documentation chunk that is semantically similar to a Git diff."""

    file_name: str = Field(
        description="Name of the file in the documentation git repository where the documentation chunk is located."
    )
    chunk_content: str = Field(description="The content of the original documentation chunk.")
    distance: float = Field(
        description="The distance between the provided git diff and the documentation chunk. 0 is the exact match and higher means further apart.",
    )
    diff: str = Field(description="The git diff that was originally modified and affected this documentation chunk.")


class Changes(BaseModel):
    """A documentation chunk that should be updated for a given code change."""

    original_documentation_chunk: RelatedDocumentationChunk = Field(
        description="The original snippet of content that has to be updated. "
        "This can be used to search for the exact location in the documentation file."
    )
    changes_description: str = Field(
        description="A short description of what has to be changed in order to make the documentation up-to-date."
    )


class PRFileChange(BaseModel):
    file_path: str = Field(description="The path to the source code file that was changed.")
    patch: str = Field(description="The git diff hunk that represents the changes made in the file.")


@dataclass
class Deps:
    vectordb: FAISS


agent = Agent(
    # "google-gla:gemini-2.0-pro-exp-02-05",
    # "google-gla:gemini-2.0-flash",
    # "anthropic:claude-3-5-sonnet-latest",
    "openai:gpt-4o-2024-08-06",
    # GeminiModel("gemini-2.0-pro-exp-02-05"),
    # OpenAIModel("o1"),
    # AnthropicModel("claude-3-5-sonnet-latest"),
    deps_type=Deps,
    system_prompt=[
        "You are specialized in finding documentation sections that should be updated for a given code change, provided in the form of a git diff."
        "Given a git diff hunk for a pull request, determine the documentation chunks that should be updated when the provided code changes are applied."
        "Use the `find_relevant_documentation` tool to get documentation sections that are similar to the provided git diffs using a vector search."
        "The tool accepts a list of diffs, where each element is one file in the original source code."
        "Before calling `find_relevant_documentation`, you must split the full git diff hunk (from text format) into multiple diffs, one for each file."
        "Notice  it is perfectly possible that the changes in the provided git diff hunk are not related to any documentation."
    ],
    result_type=List[Changes],
    retries=5,
)  # , instrument=True)


def question(diff_hunk: str) -> str:
    return f"Find the documentation chunks that should be updated when the provided code changes are applied:\n```diff\n{diff_hunk}\n```"


logger = logging.getLogger(__name__)


@agent.tool(retries=5)
def find_relevant_documentation(
    context: RunContext[Deps], diffs: Iterable[PRFileChange]
) -> Dict[str, List[RelatedDocumentationChunk]]:
    """Retrieve documentation text chunks that should be updated after applying the provided git diffs.

    Args:
      context: The call context.
      diff: A list of git diff hunks that represent the changes made in the code.
    Returns:
        A dictionary with the file names as keys and a list of related documentation chunks as values.
        The list is sorted by the distance between the provided git diff and the documentation chunk, which
        means the most relevant chunks are at the beginning of the list.
    """
    ret: Dict[str, List[RelatedDocumentationChunk]] = {}
    for diff in diffs:
        search_results = context.deps.vectordb.similarity_search_with_score(diff.patch, k=5)

        if not search_results:
            logger.info(f"No related documents found for diff {diff.file_path}")
            continue

        chunks: List[RelatedDocumentationChunk] = []

        for doc, score in search_results:
            chunks.append(
                RelatedDocumentationChunk(
                    chunk_content=doc.page_content,
                    file_name=doc.metadata["file_name"],
                    distance=float(score),
                    diff=diff.patch,
                )
            )
        ret[diff.file_path] = chunks

    for k, v in ret.items():
        ret[k] = sorted(v, key=lambda x: x.distance)

    logger.info(f"Found {len(ret)} related documentation chunks")
    return ret


def deps() -> Deps:
    if rag.vectordb is None:
        raise ValueError("Vectorstore not initialized. Please run generate_embeddings.py first.")
    return Deps(vectordb=rag.vectordb)


def run_agent(diffs: List[PRFileChange]) -> None:
    st = time.monotonic()
    agent_result = agent.run_sync(question("\n".join([diff.patch for diff in diffs])), deps=deps())
    et = time.monotonic()
    rprint(agent_result)
    logger.info(f"agent took {et - st} seconds")
