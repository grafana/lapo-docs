import os
import sys
import time
import logging
from typing import List, Dict
import rag
from langchain_community.vectorstores import FAISS
import shutil

# Configure once at program start
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def main(docs_path: str) -> None:

    repo_path = find_git_root(docs_path)
    if repo_path is None:
        raise ValueError(f"Could not find git repo at {docs_path}")

    logger.info(f"Loading documents from {docs_path} in repo {repo_path}")
    markdown_documents = get_documents(repo_path, docs_path)

    # Convert documents to format expected by FAISS
    texts: List[str] = []
    metadatas: List[Dict] = []

    logger.info(f"Processing {len(markdown_documents)} documents...")
    for k in markdown_documents:
        logger.info(f"Processing {k}")
        texts.append(markdown_documents[k])
        metadatas.append({"file_name": k})

    logger.info("Generating embeddings and storing in FAISS...")
    st = time.monotonic()

    # Create new FAISS instance with documents
    vectorstore = FAISS.from_texts(texts=texts, embedding=rag.embeddings, metadatas=metadatas)

    # delete old vectorstore
    if os.path.exists(rag.VECTORDB_DATA_PATH):
        # delete dir
        logger.info(f"Deleting old vectorstore at {rag.VECTORDB_DATA_PATH}")
        shutil.rmtree(rag.VECTORDB_DATA_PATH)

    # Save to disk
    os.makedirs(rag.VECTORDB_DATA_PATH, exist_ok=True)
    vectorstore.save_local(rag.VECTORDB_DATA_PATH)

    et = time.monotonic()
    logger.info(f"Done. Took {et - st:.2f} seconds")
    return None


def find_git_root(directory):
    while True:
        if os.path.exists(os.path.join(directory, ".git")):
            return directory
        parent = os.path.dirname(directory)
        if parent == directory:
            return None
        directory = parent


def get_documents(repo_path: str, docs_path: str) -> rag.Documents:
    if not os.path.isdir(repo_path):
        raise ValueError(f"Path {repo_path} does not exist")
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        raise ValueError(f"Path {repo_path} is not a git repository")
    working_path = os.path.join(repo_path, docs_path)
    if not os.path.isdir(working_path):
        raise ValueError(
            f"Path {working_path} does not contain docusaurus docs, make sure the folder points to the root of the plugin-tools repository."
        )
    documents = rag.Documents()
    for root, _, files in os.walk(working_path):
        for file in files:
            if not file.endswith(".md"):
                continue
            fn = os.path.join(root, file)
            with open(fn, "r") as f:
                documents[fn] = f.read()
    return documents


if __name__ == "__main__":
    docs_folder = sys.argv[1]
    main(docs_folder)
