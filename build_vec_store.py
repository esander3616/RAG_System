import os
import chromadb
from chromadb.utils import embedding_functions

DOCS_DIR = "docs"
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "policies"

def chunk_text(text: str) -> list[str]:
    """Splits a markdown doc into paragraph-level chunks. Each policy
    document here is written with one topic per paragraph, so this keeps
    each chunk semantically self-contained without any fixed-size logic."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs

def build():
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # collection didn't exist yet, nothing to delete

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.create_collection(
        name=COLLECTION_NAME, embedding_function=embedding_fn
    )

    total_chunks = 0
    for filename in sorted(os.listdir(DOCS_DIR)):
        if not filename.endswith((".md", ".txt")):
            continue
        with open(os.path.join(DOCS_DIR, filename)) as f:
            text = f.read()

        chunks = chunk_text(text)
        collection.add(
            documents=chunks,
            ids=[f"{filename}::{i}" for i in range(len(chunks))],
            metadatas=[{"source": filename} for _ in chunks],
        )
        print(f"Ingested {len(chunks):>2} chunks from {filename}")
        total_chunks += len(chunks)

    print(f"\nTotal chunks: {total_chunks}")
    print(f"Vector store ready at {CHROMA_PATH}")

if __name__ == "__main__":
    build()