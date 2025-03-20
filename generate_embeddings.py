import os
import sys
import time

import rag


def main(plugin_tools_repo_path: str) -> None:
    rag.vectordb_memory.clear()

    print("Loading documents from", plugin_tools_repo_path)
    markdown_documents = rag.get_documents(plugin_tools_repo_path)
    print(f"Adding {len(markdown_documents)} documents to collection.")
    st = time.monotonic()
    for k in markdown_documents:
        print(k)
        rag.vectordb_memory.save(
            texts=markdown_documents[k],
            metadata={"file_name": k},
        )
    et = time.monotonic()
    print(f"Done. Took {et - st:.2f} seconds")
    return None


if __name__ == "__main__":
    folder = rag.DEFAULT_PLUGIN_TOOLS_REPO_PATH
    if len(sys.argv) >= 2:
        folder = sys.argv[1]
    main(folder)
