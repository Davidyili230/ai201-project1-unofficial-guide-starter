"""
Milestone 3 — Document ingestion and chunking pipeline.

Stages:
  1. Load   — read every .txt file in documents/ from disk, keep source filename.
  2. Clean  — decode HTML entities, strip any stray tags, normalize whitespace.
  3. Chunk  — boundary-aware ~300-char windows with ~50-char overlap (per planning.md),
              each prefixed with a short source-context line so the chunk is
              self-contained for retrieval (addresses attribution loss — see planning.md
              "Anticipated Challenges" #2).
  4. Output — write chunks.json (text + metadata) for the Milestone 4 embedding step.

Run:  python ingest.py
"""

import glob
import html
import json
import os
import random
import re
from pathlib import Path

ROOT = Path(__file__).parent
DOCS_DIR = ROOT / "documents"
OUTPUT_FILE = ROOT / "chunks.json"

# Chunking parameters — see planning.md "Chunking Strategy".
CHUNK_SIZE = 300       # target characters of review-body content per chunk
CHUNK_OVERLAP = 0      # see planning.md: boundary packing never splits an opinion,
                       # so the originally-planned 50-char overlap is redundant.

# Header lines that are metadata/boilerplate, not substantive content. They are
# extracted into chunk metadata (and a context prefix) and dropped from the body.
HEADER_LABELS = (
    "SOURCE:", "PROFESSOR:", "DEPARTMENT:", "URL:",
    "OVERALL RATING:", "STUDENT REVIEWS:", "COURSE:", "INSTRUCTOR:",
)


# --- Stage 1: Load -----------------------------------------------------------

def load_documents(docs_dir):
    """Read every .txt file into {source, raw}. Source = filename for attribution."""
    docs = []
    for path in sorted(glob.glob(str(docs_dir / "*.txt"))):
        raw = Path(path).read_text(encoding="utf-8")
        docs.append({"source": os.path.basename(path), "raw": raw})
    return docs


# --- Stage 2: Clean ----------------------------------------------------------

def clean_text(text):
    """Remove markup/boilerplate artifacts and normalize whitespace.

    These sources were collected by hand into plain text, so this is mostly a
    safeguard: it still runs so the pipeline survives a future source that was
    pasted from an HTML page (&amp;, <div>, &nbsp;, etc.).
    """
    text = html.unescape(text)               # &amp; -> &, &#39; -> '
    text = re.sub(r"<[^>]+>", " ", text)     # strip any HTML tags
    text = re.sub(r"[ \t]+", " ", text)      # collapse runs of spaces/tabs
    text = "\n".join(line.strip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)   # collapse 3+ blank lines to one
    return text.strip()


# --- Metadata extraction -----------------------------------------------------

def extract_metadata(source, text):
    """Pull professor/course/rating + a human-readable context label from the header.

    The context label is prepended to every chunk so each chunk is self-contained
    for retrieval (planning.md "Anticipated Challenges" #2 — attribution loss).
    """
    meta = {"source": source}

    prof = re.search(r"PROFESSOR:\s*(.+)", text)
    course = re.search(r"COURSE:\s*(.+)", text)
    instructor = re.search(r"INSTRUCTOR:\s*([^(\n]+)", text)
    rating = re.search(r"OVERALL RATING:\s*(.+)", text)

    if course:  # syllabus document
        instr = instructor.group(1).strip() if instructor else None
        meta["doc_type"] = "syllabus"
        meta["professor"] = instr
        meta["rating"] = None
        who = f", {instr}" if instr else ""
        meta["context"] = f"{course.group(1).strip()}{who} — official course syllabus"
    else:        # RateMyProfessors review document
        name = prof.group(1).strip() if prof else "Unknown"
        meta["doc_type"] = "review"
        meta["professor"] = name
        meta["rating"] = rating.group(1).strip() if rating else None
        summary = f" — {meta['rating']}" if meta["rating"] else ""
        meta["context"] = f"Professor {name}, RateMyProfessors{summary}"

    return meta


def extract_body(text, doc_type):
    """Return substantive content units, with header boilerplate removed.

    The two doc types have different structure, so they unitize differently:
      - reviews: one review per line (one unit per opinion; bullets stripped).
      - syllabus: prose is hard-wrapped mid-sentence, so units are whole
        paragraphs (split on blank lines, wrapped lines re-joined) to avoid
        tearing a sentence like "...on algorithm | development, and debugging."
    """
    if doc_type == "syllabus":
        units = []
        for para in re.split(r"\n\s*\n", text):
            para = " ".join(l.strip() for l in para.splitlines() if l.strip())
            if not para or para.startswith(HEADER_LABELS):
                continue
            units.append(para)
        return units

    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith(HEADER_LABELS):
            continue
        line = re.sub(r"^[-*]\s*", "", line)  # strip bullet markers
        lines.append(line)
    return lines


# --- Stage 3: Chunk ----------------------------------------------------------

def split_units(lines):
    """Break body lines into boundary units (one review/sentence per unit).

    Each line is a unit; a line longer than CHUNK_SIZE is further split on
    sentence boundaries so packing never has to cut mid-word.
    """
    units = []
    for line in lines:
        if len(line) <= CHUNK_SIZE:
            units.append(line)
        else:
            # Split overly long lines on sentence-ending punctuation.
            parts = re.split(r"(?<=[.!?])\s+", line)
            units.extend(p.strip() for p in parts if p.strip())
    return units


def chunk_document(text, meta):
    """Pack review/sentence units into ~CHUNK_SIZE windows on opinion boundaries.

    Every chunk is prefixed with the source context (professor + rating) so it
    stands alone in retrieval ("Her accent is hard to understand" is useless
    without the name). Header boilerplate is dropped before packing.
    """
    prefix = meta["context"] + ". "
    body_budget = max(1, CHUNK_SIZE - len(prefix))  # keep total near CHUNK_SIZE
    units = split_units(extract_body(text, meta["doc_type"]))

    bodies = []          # body text of each chunk (without prefix)
    current = []
    for unit in units:
        candidate = (" ".join(current + [unit])).strip()
        if current and len(candidate) > body_budget:
            bodies.append(" ".join(current).strip())
            # CHUNK_OVERLAP == 0: boundary packing already keeps opinions whole,
            # so we start fresh. (Carry trailing units here if overlap is wanted.)
            current = [unit]
        else:
            current.append(unit)
    if current:
        bodies.append(" ".join(current).strip())

    chunks = []
    for i, body in enumerate(bodies):
        text_with_ctx = prefix + body
        chunks.append({
            "id": f"{Path(meta['source']).stem}_c{i}",
            "text": text_with_ctx,
            "source": meta["source"],
            "professor": meta["professor"],
            "doc_type": meta["doc_type"],
            "char_count": len(text_with_ctx),
        })
    return chunks


# --- Pipeline ----------------------------------------------------------------

def build_chunks():
    docs = load_documents(DOCS_DIR)
    all_chunks = []
    cleaned_by_source = {}
    for doc in docs:
        cleaned = clean_text(doc["raw"])
        cleaned_by_source[doc["source"]] = cleaned
        meta = extract_metadata(doc["source"], cleaned)
        all_chunks.extend(chunk_document(cleaned, meta))
    return docs, cleaned_by_source, all_chunks


def main():
    docs, cleaned_by_source, chunks = build_chunks()

    print(f"Loaded {len(docs)} documents from {DOCS_DIR}")

    # --- Inspection 1: read one fully cleaned document ---
    sample_src = docs[0]["source"]
    print("\n" + "=" * 70)
    print(f"CLEANED DOCUMENT — {sample_src}")
    print("=" * 70)
    print(cleaned_by_source[sample_src])

    # --- Inspection 2: 5 representative chunks (one per several documents) ---
    print("\n" + "=" * 70)
    print("5 REPRESENTATIVE CHUNKS")
    print("=" * 70)
    step = max(1, len(chunks) // 5)
    for c in chunks[::step][:5]:
        print(f"\n[{c['id']}] ({c['char_count']} chars, source={c['source']})")
        print(c["text"])

    # --- Inspection 3: 5 random chunks (checkpoint) ---
    rng = random.Random(42)  # fixed seed for reproducible inspection
    print("\n" + "=" * 70)
    print("5 RANDOM CHUNKS (checkpoint)")
    print("=" * 70)
    for c in rng.sample(chunks, min(5, len(chunks))):
        print(f"\n[{c['id']}] ({c['char_count']} chars, source={c['source']})")
        print(c["text"])

    # --- Stats ---
    lengths = [c["char_count"] for c in chunks]
    empties = [c for c in chunks if len(c["text"].strip()) == 0]
    print("\n" + "=" * 70)
    print("STATS")
    print("=" * 70)
    print(f"Total chunks: {len(chunks)}")
    print(f"Chunk length — min {min(lengths)}, max {max(lengths)}, "
          f"avg {sum(lengths) / len(lengths):.0f} chars")
    print(f"Empty chunks: {len(empties)}")
    print(f"Chunks per document:")
    for doc in docs:
        n = sum(1 for c in chunks if c["source"] == doc["source"])
        print(f"  {doc['source']}: {n}")

    OUTPUT_FILE.write_text(json.dumps(chunks, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    print(f"\nWrote {len(chunks)} chunks -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
