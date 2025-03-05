import time
from chromadb import PersistentClient

import rag


def main() -> None:
    chromadb_client = PersistentClient(path=rag.CHROMADB_DATA_PATH)

    if rag.COLLECTIONS_NAME in chromadb_client.list_collections():
        chromadb_client.delete_collection(rag.COLLECTIONS_NAME)
    collection = chromadb_client.create_collection(rag.COLLECTIONS_NAME)

    markdown_documents = rag.get_documents(rag.DOCS_PATH)
    ids = markdown_documents.sorted_keys()
    print(f"Adding {len(ids)} documents to collection:{'\n'.join(ids)}")
    st = time.monotonic()
    collection.add(
        documents=markdown_documents.sorted_documents(),
        ids=ids,
    )
    et = time.monotonic()
    print(f"Done. Took {et - st:.2f} seconds")
    return None


if __name__ == "__main__":
    main()
