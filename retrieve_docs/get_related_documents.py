from dataclasses import dataclass
import json
from typing import List, TypedDict
from chromadb import Collection, PersistentClient, ClientAPI
import logfire
from pydantic_ai import Agent, RunContext
from rich import print as rprint

import rag
import testdata

# 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
logfire.configure(send_to_logfire="if-token-present")


class Diff(TypedDict):
    file_name: str
    diff: str


class RelatedDocumentSection(TypedDict):
    file_name: str
    content: str


class Changes(TypedDict):
    original_document: RelatedDocumentSection
    changes_description: str


@dataclass
class Deps:
    chromadb_client: ClientAPI
    chromadb_collection: Collection


docs_rag_agent = Agent(
    "google-gla:gemini-2.0-flash",
    # "openai:o1",
    # "openai:gpt-4o",
    deps_type=Deps,
    system_prompt=[
        "You are specialized in finding documentation sections that should be updated for a given code change, provided in the form of a git diff.",
        "Use the `retrieve` tool to get documentation sections that are similar to the provided git diffs using a vector search.",
        # "After retrieving the documents, for each result, return the original snippet of content that has to be updated AS-IS (with no changes), the name of the markdown documentation file where that snippet of content is from and short description of what has to be changed in order to make the documentation up-to-date.",
    ],
    result_type=List[Changes],
)  # , instrument=True)


@docs_rag_agent.tool
def retrieve(context: RunContext[Deps], diff: Diff) -> List[RelatedDocumentSection]:
    """Retrieve documentation sections that are related to the provided git diff.

    Args:
      context: The call context.
      diff: A list of git diff sections inside a file.
    """
    # TODO: exclude high distance results
    results = context.deps.chromadb_collection.query(query_texts=[diff["diff"]])
    if results["documents"] is None or not results["documents"]:
        raise ValueError("No related documents found")
    assert len(results["documents"]) == 1, "Only one result expected"

    ret: List[RelatedDocumentSection] = []
    for i, doc in enumerate(results["documents"][0]):
        ret.append({"content": doc, "file_name": results["ids"][0][i]})
    rprint(ret)
    return ret


def run_agent(diffs: List[Diff]) -> None:
    chromadb_client = PersistentClient(path=rag.CHROMADB_DATA_PATH)
    chromadb_collection = chromadb_client.get_collection(rag.COLLECTIONS_NAME)
    deps = Deps(
        chromadb_client=chromadb_client, chromadb_collection=chromadb_collection
    )

    question = f"Retrieve the related documentation sections that are related to the provided git diffs: ```\n{json.dumps(diffs)}\n```"
    logfire.info(f"Asking question to agent: {question}")
    agent_result = docs_rag_agent.run_sync(question, deps=deps)
    rprint(agent_result)


def main() -> None:
    run_agent(testdata.DUMMY_GIT_DIFFS)


if __name__ == "__main__":
    main()
