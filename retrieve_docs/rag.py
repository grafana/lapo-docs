import os
from typing import List, OrderedDict

DOCS_PATH = os.path.join("..", "..", "plugin-tools", "docusaurus", "docs")
CHROMADB_DATA_PATH = os.path.join(".data", "chromadb")
COLLECTIONS_NAME = "documents"


class Documents:
    def __init__(self) -> None:
        self._docs: OrderedDict[str, str] = OrderedDict()

    def __setitem__(self, key: str, docs: str) -> None:
        if key in self._docs:
            raise ValueError(f"Document with key {key} already exists")
        self._docs[key] = docs

    def __getitem__(self, key: str) -> str:
        return self._docs[key]

    def sorted_documents(self) -> List[str]:
        return list(self._docs.values())

    def sorted_keys(self) -> List[str]:
        return list(self._docs.keys())


def get_documents(path: str) -> Documents:
    documents = Documents()
    for root, _, files in os.walk(path):
        for file in files:
            if not file.endswith(".md"):
                continue
            fn = os.path.join(root, file)
            rel_fn = os.path.relpath(fn, path)
            with open(fn, "r") as f:
                documents[rel_fn] = f.read()
    return documents
