import os
import sys
import time

import rag

DEFAULT_DOCS_PATH = os.path.join("..", "..", "plugin-tools", "docusaurus", "docs")


def main(docs_path: str) -> None:
    rag.vectordb_memory.clear()

    print("Loading documents from", docs_path)
    markdown_documents = rag.get_documents(docs_path)
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
    folder = DEFAULT_DOCS_PATH
    if len(sys.argv) >= 2:
        folder = sys.argv[1]
    main(folder)
