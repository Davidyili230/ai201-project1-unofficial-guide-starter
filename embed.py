"""
Milestone 4 — Embedding and vector store population.

Stages:
  1. Load    — read chunks.json produced by ingest.py
  2. Embed   — encode all chunk texts with all-MiniLM-L6-v2 (384-dim, local, no API key)
  3. Store   — upsert into a persistent ChromaDB collection with source metadata

Run:  python3 embed.py
"""

import json
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).parent
CHUNKS_FILE = ROOT / "chunks.json"
CHROMA_DIR = ROOT / "chroma_db"

COLLECTION_NAME = "professor_reviews"
EMBED_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 64   # embed in batches to avoid OOM on large corpora


def load_chunks(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_collection(chunks, model):
    """Embed all chunks and upsert into a persistent ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Delete and recreate so re-runs are idempotent.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        # cosine distance: intuitive for semantic similarity (lower = more similar)
        metadata={"hnsw:space": "cosine"},
    )

    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [
        {
            "source": c["source"],
            "professor": c.get("professor") or "",
            "doc_type": c.get("doc_type") or "",
        }
        for c in chunks
    ]

    print(f"Embedding {len(texts)} chunks with '{EMBED_MODEL}' …")
    # Encode in batches; show_progress_bar gives a tqdm bar if tqdm is installed.
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    # ChromaDB add() accepts lists, not numpy arrays directly.
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
    )
    return collection


def main():
    chunks = load_chunks(CHUNKS_FILE)
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE}")

    model = SentenceTransformer(EMBED_MODEL)

    collection = build_collection(chunks, model)

    print(f"\nStored {collection.count()} vectors in ChromaDB -> {CHROMA_DIR}")
    print(f"Collection: '{COLLECTION_NAME}'  |  Distance space: cosine")
    print("Run retrieve.py to test retrieval.")


if __name__ == "__main__":
    main()
