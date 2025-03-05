import time
from vectordb import Memory
from rich import print as rprint

import rag


def main() -> None:
    memory = Memory(memory_file=rag.VECTORDB_DATA_PATH)
    memory.clear()

    markdown_documents = rag.get_documents(rag.DOCS_PATH)
    print(f"Adding {len(markdown_documents)} documents to collection.")
    st = time.monotonic()
    for k in markdown_documents:
        print(k)
        memory.save(
            texts=markdown_documents[k],
            metadata={"file_name": k},
        )
    et = time.monotonic()
    print(f"Done. Took {et - st:.2f} seconds")
    return None


if __name__ == "__main__":
    main()
