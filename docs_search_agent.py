from dataclasses import dataclass
import json
import time
from typing import List, TypedDict
import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from rich import print as rprint
from vectordb import Memory
import os

import rag
import testdata
# set CUDA_VISIBLE_DEVICES=1 in env
os.environ["CUDA_VISIBLE_DEVICES"] = "1"


logfire.configure(send_to_logfire=False)


class Diff(TypedDict):
    """A diff section inside a file."""

    """Name of the file in the git repository where the diff is located."""
    file_name: str

    """The content of the git diff."""
    diff: str


class RelatedDocumentationChunk(BaseModel):
    """A documentation chunk that is semantically similar to a Git diff."""

    file_name: str = Field(
        description="Name of the file in the documentation git repository where the documentation chunk is located."
    )
    chunk_content: str = Field(description="The content of the documentation chunk.")
    distance: float = Field(
        description="The distance between the provided git diff and the documentation chunk. 0 is the exact match and higher means further apart.",
    )
    diff: str = Field(
         description="The git diff that was originally modified and affected this documentation chunk."
    )


class Changes(BaseModel):
    """A documentation chunk that should be updated for a given code change."""

    original_documentation_chunks: RelatedDocumentationChunk = Field(
        description="The original snippet of content that has to be updated. "
        + "This can be used to search for the exact location in the documentation file."
    )
    changes_description: str = Field(
        description="A short description of what has to be changed in order to make the documentation up-to-date."
    )


@dataclass
class Deps:
    vectordb_memory: Memory


docs_rag_agent = Agent(
    # "google-gla:gemini-2.0-flash",
    "openai:o1",
    # "openai:gpt-4o",
    deps_type=Deps,
    system_prompt=[
        "You are specialized in finding documentation sections that should be updated for a given code change, provided in the form of a git diff.",
        "Use the `retrieve` tool to get documentation sections that are similar to the provided git diffs using a vector search. The results are sorted from most similar to least similar.",
        "After retrieving the documents, for each result, return the original snippet of content AS-IS (with no changes), the name of the markdown documentation file where that snippet of content is from and short description of what has to be changed in order to make the documentation up-to-date.",
    ],
    result_type=List[Changes],
)  # , instrument=True)


def question(diffs: List[Diff]) -> str:
    return f"Retrieve the related documentation chunks that are related to the provided git diffs: ```\n{json.dumps(diffs)}\n```"


@docs_rag_agent.tool
def retrieve(context: RunContext[Deps], diff: Diff) -> List[RelatedDocumentationChunk]:
    """Retrieve documentation text chunks that are related to the provided git diff.

    Args:
      context: The call context.
      diff: A list of git diff sections inside a file. The results are sorted from most similar to least similar.
    """
    db_results = context.deps.vectordb_memory.search(diff["diff"], unique=True)
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
                diff=diff["diff"],
            )
        )
    ret = sorted(ret, key=lambda x: x.distance)
    rprint("final result for llm", ret)
    return ret


def run_agent(diffs: List[Diff]) -> None:
    deps = Deps(vectordb_memory=rag.vectordb_memory)
    q = question(diffs)
    logfire.info(f"Asking question to agent: {q}")
    st = time.monotonic()
    agent_result = docs_rag_agent.run_sync(q, deps=deps)
    et = time.monotonic()
    rprint(agent_result)
    logfire.info("Done. Took {took} seconds", took="{:.2f}".format(et - st))


def main() -> None:
    run_agent(testdata.DUMMY_GIT_DIFFS)


if __name__ == "__main__":
    main()
