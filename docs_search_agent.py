from dataclasses import dataclass
import json
import time
from typing import List
import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from rich import print as rprint
from vectordb import Memory
import os

from gitpr_analyzer_agent import CodeChange
import rag

# set CUDA_VISIBLE_DEVICES=1 in env
os.environ["CUDA_VISIBLE_DEVICES"] = "1"


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


@dataclass
class Deps:
    vectordb_memory: Memory


agent = Agent(
    # "google-gla:gemini-2.0-flash",
    "openai:o1",
    # "openai:gpt-4o",
    deps_type=Deps,
    system_prompt=[
        "You are specialized in finding documentation sections that should be updated for a given code change, provided in the form of a git diff.",
        "Use the `retrieve` tool to get documentation sections that are similar to the provided git diffs using a vector search. The results are sorted from most similar to least similar.",
        # "After retrieving the documents, for each result, return the original snippet of content AS-IS (with no changes), the name of the markdown documentation file where that snippet of content is from and short description of what has to be changed in order to make the documentation up-to-date.",
    ],
    result_type=List[Changes],
)  # , instrument=True)


def question(diffs: List[CodeChange]) -> str:
    j = json.dumps([x.model_dump(include={"diff_hunk"}) for x in diffs])
    return f"Retrieve the documentation chunks that should be updated when the provided code changes are applied:\n```json\n{j}\n```"


@agent.tool
def retrieve(
    context: RunContext[Deps], diff: CodeChange
) -> List[RelatedDocumentationChunk]:
    """Retrieve documentation text chunks that are related to the provided git diff.

    Args:
      context: The call context.
      diff: A list of git diff sections inside a file. The results are sorted from most similar to least similar.
    """
    db_results = context.deps.vectordb_memory.search(diff.diff_hunk, unique=True)
    if not db_results:
        raise ValueError("No related documents found")

    ret: List[RelatedDocumentationChunk] = []
    rprint("vector db results", db_results)
    for chunk in db_results:
        ret.append(
            RelatedDocumentationChunk(
                chunk_content=chunk["chunk"],
                file_name=chunk["metadata"]["file_name"],
                distance=float(chunk["distance"]),
                diff=diff.diff_hunk,
            )
        )
    ret = sorted(ret, key=lambda x: x.distance)
    rprint("final result for llm", ret)
    return ret


def deps() -> Deps:
    return Deps(vectordb_memory=rag.vectordb_memory)


def run_agent(diffs: List[CodeChange]) -> None:
    q = question(diffs)
    logfire.info(f"Asking question to agent: {q}")
    st = time.monotonic()
    agent_result = agent.run_sync(q, deps=deps())
    et = time.monotonic()
    rprint(agent_result)
    logfire.info("Done. Took {took} seconds", took="{:.2f}".format(et - st))
