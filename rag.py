import os
from typing import Iterator, OrderedDict
from vectordb import Memory

# use CUDA
os.environ["CUDA_VISIBLE_DEVICES"] = "1"

DEFAULT_PLUGIN_TOOLS_REPO_PATH = os.path.join("..", "..", "plugin-tools")
VECTORDB_DATA_PATH = os.path.join(".data", "vectordb")
vectordb_memory = Memory(memory_file=VECTORDB_DATA_PATH, embeddings="fast")


class Documents:
    def __init__(self) -> None:
        self._docs: OrderedDict[str, str] = OrderedDict()

    def __setitem__(self, key: str, docs: str) -> None:
        if key in self._docs:
            raise ValueError(f"Document with key {key} already exists")
        self._docs[key] = docs

    def __getitem__(self, key: str) -> str:
        return self._docs[key]

    def __contains__(self, key) -> bool:
        return key in self._docs

    def __len__(self) -> int:
        return len(self._docs)

    def __iter__(self) -> Iterator[str]:
        return iter(self._docs)


def get_documents(path: str) -> Documents:
    if not os.path.isdir(path):
        raise ValueError(f"Path {path} does not exist")
    if not os.path.isdir(os.path.join(path, ".git")):
        raise ValueError(f"Path {path} is not a git repository")
    docusaurus_root = os.path.join(path, "docusaurus", "docs")
    if not os.path.isdir(docusaurus_root):
        raise ValueError(
            f"Path {path} does not contain docusaurus docs, make sure the folder points to the root of the plugin-tools repository."
        )
    documents = Documents()
    for root, _, files in os.walk(docusaurus_root):
        for file in files:
            if not file.endswith(".md"):
                continue
            fn = os.path.join(root, file)
            rel_fn = os.path.relpath(fn, path)
            with open(fn, "r") as f:
                documents[rel_fn] = f.read()
    return documents
