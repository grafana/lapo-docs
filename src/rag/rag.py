import os
from typing import Iterator, OrderedDict
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# You'll need to set your Google API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable")

genai.configure(api_key=GEMINI_API_KEY)

DEFAULT_PLUGIN_TOOLS_REPO_PATH = os.path.join("..", "plugin-tools")
VECTORDB_DATA_PATH = os.path.join(".data", "faiss")

# Initialize Google embeddings
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GEMINI_API_KEY,
)

VECTORDB_DATA_PATH_PKL = os.path.join(VECTORDB_DATA_PATH, "index.pkl")
# Create FAISS instance if it exists, otherwise None
try:
    vectordb = FAISS.load_local(VECTORDB_DATA_PATH, embeddings, allow_dangerous_deserialization=True)
except:
    vectordb = None


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
