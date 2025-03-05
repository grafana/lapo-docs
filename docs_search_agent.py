from dataclasses import dataclass
import json
import time
from typing import Dict, Iterable, List
import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from rich import print as rprint
from vectordb import Memory

import rag


logfire.configure(send_to_logfire=False)


class RelatedDocumentationChunk(BaseModel):
    """A documentation chunk that is semantically similar to a Git diff."""

    file_name: str = Field(
        description="Name of the file in the documentation git repository where the documentation chunk is located."
    )
    chunk_content: str = Field(
        description="The content of the original documentation chunk."
    )
    distance: float = Field(
        description="The distance between the provided git diff and the documentation chunk. 0 is the exact match and higher means further apart.",
    )
    diff: str = Field(
        description="The git diff that was originally modified and affected this documentation chunk."
    )


class Changes(BaseModel):
    """A documentation chunk that should be updated for a given code change."""

    original_documentation_chunk: RelatedDocumentationChunk = Field(
        description="The original snippet of content that has to be updated. "
        + "This can be used to search for the exact location in the documentation file."
    )
    changes_description: str = Field(
        description="A short description of what has to be changed in order to make the documentation up-to-date."
    )
    # ??????
    # updated_chunk_content: str = Field(
    #    description="The new content of the documentation chunk. "
    #    + "This is the updated version of the documentation, with the changes described in the `changes_description` field."
    # )


class PRFileChange(BaseModel):
    file_path: str = Field(
        description="The path to the source code file that was changed."
    )
    patch: str = Field(
        description="The git diff hunk that represents the changes made in the file."
    )


@dataclass
class Deps:
    vectordb_memory: Memory


agent = Agent(
    # "google-gla:gemini-2.0-flash",
    # "openai:o1",
    # GeminiModel("gemini-2.0-flash"),
    OpenAIModel("o1"),
    # AnthropicModel("claude-3-5-sonnet-latest"),
    deps_type=Deps,
    system_prompt=[
        "You are specialized in finding documentation sections that should be updated for a given code change, provided in the form of a git diff."
        "Given a git diff hunk for a pull request, determine the documentation chunks that should be updated when the provided code changes are applied."
        "Use the `find_relevant_documentation` tool to get documentation sections that are similar to the provided git diffs using a vector search."
        "The tool accepts a list of diffs, where each element is one file in the original source code."
        "Before calling `find_relevant_documentation`, you must split the full git diff hunk (from text format) into multiple diffs, one for each file."
        # "Split the provided git diff hunk (one for each file) and search for similar documentation chunks in the documentation repository using the `find_relevant_documentation` tool.",
        # "After retrieving the documents, for each result, return the original snippet of content AS-IS (with no changes), the name of the markdown documentation file where that snippet of content is from and short description of what has to be changed in order to make the documentation up-to-date.",
    ],
    result_type=List[Changes],
    retries=5,
)  # , instrument=True)


def question(diff_hunk: str) -> str:
    return f"Find the documentation chunks that should be updated when the provided code changes are applied:\n```diff\n{diff_hunk}\n```"


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
        db_results = context.deps.vectordb_memory.search(diff.patch, unique=True)
        if not db_results:
            print("No related documents found for diff", diff.file_path)
            continue
        rprint("vector db result for", diff, ":", db_results)
        chunks: List[RelatedDocumentationChunk] = []
        for chunk in db_results:
            chunks.append(
                RelatedDocumentationChunk(
                    chunk_content=chunk["chunk"],
                    file_name=chunk["metadata"]["file_name"],
                    distance=float(chunk["distance"]),
                    diff=diff.patch,
                )
            )
        ret[diff.file_path] = chunks
    for k, v in ret.items():
        ret[k] = sorted(v, key=lambda x: x.distance)
    rprint("final result for llm", ret)
    return ret


def deps() -> Deps:
    return Deps(vectordb_memory=rag.vectordb_memory)


def run_agent(diffs: List[PRFileChange]) -> None:
    q = question(diffs)
    logfire.info(f"Asking question to agent: {q}")
    st = time.monotonic()
    agent_result = agent.run_sync(q, deps=deps())
    et = time.monotonic()
    rprint(agent_result)
    logfire.info("Done. Took {took} seconds", took="{:.2f}".format(et - st))
