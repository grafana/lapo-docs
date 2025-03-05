from dataclasses import dataclass
import json
import time
from typing import List, TypedDict
import logfire
from pydantic_ai import Agent, RunContext
from rich import print as rprint
from vectordb import Memory

import rag
import testdata

# 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
logfire.configure(send_to_logfire="if-token-present")


class Diff(TypedDict):
    file_name: str
    diff: str


class RelatedDocumentationChunk(TypedDict):
    file_name: str
    chunk_content: str


class Changes(TypedDict):
    original_documentation_chunks: RelatedDocumentationChunk
    changes_description: str


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
        "Use the `retrieve` tool to get documentation sections that are similar to the provided git diffs using a vector search.",
        # "After retrieving the documents, for each result, return the original snippet of content that has to be updated AS-IS (with no changes), the name of the markdown documentation file where that snippet of content is from and short description of what has to be changed in order to make the documentation up-to-date.",
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
      diff: A list of git diff sections inside a file.
    """
    # TODO: exclude low distance results
    db_results = context.deps.vectordb_memory.search(diff["diff"], unique=True)
    if not db_results:
        raise ValueError("No related documents found")

    ret: List[RelatedDocumentationChunk] = []
    rprint("vector db results", db_results)
    for chunk in db_results:
        ret.append(
            {
                "chunk_content": chunk["chunk"],
                "file_name": chunk["metadata"]["file_name"],
            }
        )
    rprint("final result for llm", ret)
    return ret


def run_agent(diffs: List[Diff]) -> None:
    vectordb_memory = Memory(memory_file=rag.VECTORDB_DATA_PATH)
    deps = Deps(vectordb_memory=vectordb_memory)
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
