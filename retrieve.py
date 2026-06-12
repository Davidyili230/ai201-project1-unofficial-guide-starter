"""
Milestone 4 — Retrieval function and query evaluation.

Usage:
  python3 retrieve.py                 # run the 3 built-in test queries
  python3 retrieve.py "your question" # ad-hoc query

The retrieval function embed_query() + query_collection() can also be imported
by the Milestone 5 generation script:

    from retrieve import get_retriever
    retrieve = get_retriever()
    results = retrieve("What do students think about Professor X?")
"""

import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).parent
CHROMA_DIR = ROOT / "chroma_db"

COLLECTION_NAME = "professor_reviews"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 6   # planning.md Retrieval Approach: top-k = 6–8


# ---------------------------------------------------------------------------
# Core retrieval
# ---------------------------------------------------------------------------

def get_retriever(top_k=TOP_K):
    """Return a callable retrieve(query) -> list[dict] ready for Milestone 5."""
    model = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    def retrieve(query: str, k: int = top_k):
        embedding = model.encode([query], convert_to_numpy=True)
        results = collection.query(
            query_embeddings=embedding.tolist(),
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append({"text": doc, "metadata": meta, "distance": dist})
        return chunks

    return retrieve


# ---------------------------------------------------------------------------
# CLI / evaluation harness
# ---------------------------------------------------------------------------

# 3 of the 5 evaluation-plan queries (planning.md §Evaluation Plan)
TEST_QUERIES = [
    "What do students say about the clarity of Professor Tong Yi's lectures in CSCI 13500?",
    "How responsive is Professor Mahdi Makki to student questions?",
    "What do students say about the clarity of Professor Susan Epstein's grading rubrics?",
]


def run_evaluation(retrieve):
    queries = TEST_QUERIES
    if len(sys.argv) > 1:
        queries = [" ".join(sys.argv[1:])]

    for i, query in enumerate(queries, 1):
        print("\n" + "=" * 72)
        print(f"QUERY {i}: {query}")
        print("=" * 72)
        results = retrieve(query)
        for rank, r in enumerate(results, 1):
            dist = r["distance"]
            meta = r["metadata"]
            flag = "  <-- WEAK MATCH" if dist > 0.6 else ""
            print(f"\n  Rank {rank}  |  distance: {dist:.4f}{flag}")
            print(f"  Source:    {meta.get('source')}  ({meta.get('doc_type')})")
            print(f"  Professor: {meta.get('professor')}")
            print(f"  Text: {r['text']}")


def main():
    retrieve = get_retriever()
    run_evaluation(retrieve)


if __name__ == "__main__":
    main()
