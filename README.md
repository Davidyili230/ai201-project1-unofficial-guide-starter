# The Unofficial Guide — Project 1

---

## Domain

Student reviews of Computer Science professors at Hunter College (CUNY). This knowledge is valuable because students choosing between professors have limited options: official course descriptions say nothing about teaching style, exam difficulty, or workload, and course evaluations are internal and never published. Review aggregators like RateMyProfessors exist, but students typically check one source and miss dissenting reviews or outdated ratings. By collecting and indexing reviews for 9 different professors across a range of ratings — plus one official course syllabus for ground-truth workload data — the system can answer specific, comparative questions ("Is Professor X's grading fair?", "How much time does this course take?") that no single official channel can answer.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | RateMyProfessors — Raffi Khatchadourian | Student reviews | `documents/01_khatchadourian_rmp.txt` |
| 2 | RateMyProfessors — Susan Epstein | Student reviews | `documents/02_susan_epstein_rmp.txt` |
| 3 | RateMyProfessors — Eric Schweitzer | Student reviews | `documents/03_schweitzer_rmp.txt` |
| 4 | RateMyProfessors — Jeff Epstein | Student reviews | `documents/04_jeff_epstein_rmp.txt` |
| 5 | RateMyProfessors — Katherine St. John | Student reviews | `documents/05_st_john_rmp.txt` |
| 6 | RateMyProfessors — Raj Korpan | Student reviews | `documents/06_korpan_rmp.txt` |
| 7 | RateMyProfessors — Mahdi Makki | Student reviews | `documents/07_makki_rmp.txt` |
| 8 | RateMyProfessors — Khant Ko Naing | Student reviews | `documents/08_ko_naing_rmp.txt` |
| 9 | RateMyProfessors — Tong Yi | Student reviews | `documents/09_tong_yi_rmp.txt` |
| 10 | CSCI 13500 Syllabus (Tong Yi, Spring 2021) | Official course document | `documents/10_csci135_syllabus.txt` |

The corpus spans high-rated (Makki 5.0, Korpan 4.0, Khatchadourian 4.2), mixed (Ko Naing 3.8, Jeff Epstein 3.7, Schweitzer 2.6), and low-rated (Susan Epstein 2.1, Tong Yi 2.2, St. John 2.3) professors so the system can answer comparative and specific questions. The official syllabus adds a ground-truth document for workload and policy questions.

---

## Chunking Strategy

**Chunk size:** ~300 characters target (roughly 75 tokens), using boundary-aware packing — whole review lines or whole paragraphs are packed together up to the limit, never splitting mid-word or mid-opinion.

**Overlap:** 0 characters. The original plan called for 50-character overlap to avoid splitting opinions across boundaries. After switching to boundary-aware packing (which guarantees opinions are never cut mid-thought), overlap became counterproductive: a 50-char character overlap would either re-duplicate complete reviews across adjacent chunks or re-introduce mid-word fragments at the seam. Overlap is set to 0.

**Why these choices fit your documents:** Reviews are short opinion units — typically 1–3 sentences capturing a distinct observation ("Hard grader but fair," "Lectures unclear due to accent"). A 300-char chunk captures one complete review or a discrete observation. Smaller chunks (< 200 chars) lose context; larger chunks (> 600 chars) mix multiple review aspects, reducing retrieval precision on targeted questions.

**Preprocessing before chunking:** The `SOURCE:/PROFESSOR:/DEPARTMENT:/URL:/OVERALL RATING:` header block that appeared at the top of every file is boilerplate, not reviewable content. It was parsed into chunk metadata (`source`, `professor`, `doc_type`) and stripped from chunk bodies. To preserve attribution inside each chunk, every chunk is prefixed with `Professor <name>, RateMyProfessors — <rating>.` so that a chunk like "Her accent is hard to understand" is not stripped of context when retrieved in isolation.

**Final chunk count:** 42 chunks across 10 documents (average ~224 characters, range 118–316; 0 empty chunks).

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (384-dimensional vectors, cosine distance space, stored in a persistent ChromaDB collection).

**Production tradeoff reflection:** `all-MiniLM-L6-v2` is fast, lightweight, and performs well on general semantic similarity, which is sufficient for a domain as linguistically simple as student reviews. Its main weakness here is that it has no awareness that "Epstein" is a surname shared by two unrelated professors (Susan Epstein and Jeff Epstein) — queries about one retrieve chunks from the other because the embedding space clusters reviews with shared last-name tokens. In production with no cost constraint, I would evaluate `all-mpnet-base-v2` (768-dim), which captures finer-grained semantic distinctions, and consider a re-ranking layer (e.g., a cross-encoder) to apply name-exact-match filtering on top of semantic similarity. For a multilingual student body, a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` would also be worth benchmarking. The latency/accuracy tradeoff favors the current model for a small (~8 KB) corpus, but breaks down for larger, more ambiguous corpora.

---

## Grounded Generation

**System prompt grounding instruction:**

The system prompt enforces grounding with four numbered rules given to the LLM before any user query:

```
You are a student advisor assistant for Hunter College Computer Science courses.
You answer questions ONLY using the provided document excerpts.

STRICT RULES:
1. Answer ONLY from the provided context. Do not use any outside knowledge.
2. If the context does not contain enough information to answer the question,
   respond with exactly: "I don't have enough information in my sources to answer that question."
3. Do not guess, infer, or supplement with general knowledge.
4. Be specific and reference which professor or document your answer comes from.
```

Rule 2 specifies the exact decline phrase, which enables automated testing: both out-of-scope queries ("What is the capital of France?" and "Who invented the internet?") returned that exact string in testing.

Context is formatted as a numbered excerpt block:

```
[1] Source: 09_tong_yi_rmp.txt | Professor: Tong Yi
Professor Tong Yi, RateMyProfessors — 2.2/5. Her accent is really hard to understand...

[2] Source: 10_csci135_syllabus.txt | Professor: Tong Yi
...
```

The numbered format with explicit `Source:` and `Professor:` labels helps the LLM cite correctly and reinforces that the context is a bounded list, not general knowledge.

**How source attribution is surfaced in the response:**

Source attribution is programmatic — never LLM-generated. After the model returns its answer, `ask()` iterates the retrieved chunks in order, reads the `source` field from each chunk's ChromaDB metadata, deduplicates, and returns the list. The LLM is never asked to name its sources; it only synthesizes an answer. This eliminates hallucinated citations.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about the clarity of Professor Tong Yi's lectures in CSCI 13500? | Negative: accent hard to understand, "pretty useless," difficulty mismatch between lectures and assignments | Accent is hard to understand, lectures "pretty useless," frustrating for an intro course — correct core content. Syllabus also retrieved (minor noise). | Partially relevant (syllabus pulled in alongside reviews) | Accurate |
| 2 | How much time per week does CSCI 13500 (Software Analysis & Design 1) require? | ~15–20 hrs/week: syllabus says 10–15 hrs at computer in addition to class time | Correctly cites "10–15 hours a week at a computer" plus class time, totaling ~15–20 hrs weekly | Partially relevant (Schweitzer and Korpan chunks retrieved despite being unrelated professors) | Accurate |
| 3 | How responsive is Professor Mahdi Makki to student questions? | Very positive: "answers any question you have," "answered all my questions," approachable | Correctly captures both quotes with dates; characterizes him as very responsive and approachable | Partially relevant (Schweitzer chunk retrieved, unused by LLM) | Accurate |
| 4 | What do students say about the clarity of Professor Susan Epstein's grading rubrics? | Negative: "lots of homework without clear rubric," "really picky on how you do stuff," 2.1/5 | Only surfaces "Lots of homework without clear rubric" — misses "really picky" and other details. Jeff Epstein chunks took slots in the context window. | Partially relevant (Jeff Epstein reviews retrieved due to shared surname) | Partially accurate |
| 5 | Does Professor Mahdi Makki's course connect to real-world / industry CS work? | Yes: "a lot of industry insights," useful for interviews, "hugely beneficial in my job search" | Correctly cites "industry insights that were hugely beneficial in my job search" from 07_makki_rmp.txt | Partially relevant (syllabus pulled in) | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:**  
"What do students say about the clarity of Professor Susan Epstein's grading rubrics?"

**What the system returned:**  
The answer cited only one data point — "Lots of homework without clear rubric" — and omitted the additional criticism ("really picky on how you do stuff," vague feedback on assignments) that appears in Susan Epstein's actual reviews. The programmatic sources list included `04_jeff_epstein_rmp.txt` and `05_st_john_rmp.txt`, confirming that 2 of the 6 retrieved chunks came from entirely different professors.

**Root cause (tied to a specific pipeline stage):**  
The failure occurs at the **retrieval stage**, caused by a name-collision in embedding space. The query "Susan Epstein's grading rubrics" contains the token "Epstein," and `all-MiniLM-L6-v2` encodes last-name tokens as part of the semantic representation without any understanding that it is a person identifier shared by two different professors. As a result, Jeff Epstein's reviews — which also contain the string "Epstein" alongside grading-related language ("fair grader," "rubric," "assignment") — are ranked semantically close to the query. When Jeff Epstein chunks fill 2 of the 6 context slots, the LLM has less Susan Epstein material to synthesize, and the answer becomes thinner and less accurate. The LLM correctly ignores the Jeff Epstein chunks in its answer, so the problem is not generation-level — it is that irrelevant chunks displaced relevant ones at retrieval.

**What you would change to fix it:**  
Two targeted fixes: (1) **Query expansion with disambiguation context** — prefix the query with the professor's full name and course ("Susan Epstein CSCI 150 Hunter College, grading rubrics") to add distinguishing tokens that push the query vector away from Jeff Epstein's embedding cluster; (2) **Post-retrieval metadata filtering** — add an exact-match filter on the `professor` metadata field in ChromaDB so that a query about Susan Epstein can optionally restrict results to `professor == "Susan Epstein"` before the top-k selection, hard-excluding false-positive name matches.

---

## Spec Reflection

**One way the spec helped you during implementation:**  
The Anticipated Challenges section — specifically Challenge #2 ("Loss of source credibility and attribution") — directly shaped the per-chunk context prefix design in `ingest.py`. By writing down the risk before coding, I recognized early that a standalone chunk like "Her accent is really hard to understand" is semantically meaningless without the professor's name. The spec locked in the requirement that every chunk must carry its attribution, which led to the `Professor <name>, RateMyProfessors — <rating>.` prefix that now precedes every chunk body. Without that section, the issue likely would have surfaced only during retrieval testing, after the embedding step was already done.

**One way your implementation diverged from the spec, and why:**  
The spec specified 50-character chunk overlap to prevent opinion fragmentation across boundaries. During implementation, after switching from blind character-window slicing to boundary-aware packing (which packs whole review lines up to the ~300-char target), the overlap became both redundant and harmful: with boundary packing, no opinion is ever split at a boundary, so overlap adds no protection. Worse, a 50-char character overlap on boundary-packed chunks re-duplicated complete reviews (the same opinion retrieved twice, inflating its apparent consensus) or re-introduced mid-word fragments at the seam where the carry-over portion didn't align with the next unit boundary. The spec was updated to reflect overlap = 0 along with an explanation of the tradeoff.

---

## AI Usage

**Instance 1 — Ingestion and chunking (`ingest.py`)**

- *What I gave the AI:* The Documents table, Chunking Strategy section, and pipeline diagram from `planning.md`, plus the requirement that header boilerplate should not be embedded as content.
- *What it produced:* A `chunk_text()` function using a fixed 300/50 character sliding window — cutting the text at exactly 300 characters regardless of word or sentence boundaries, then carrying the last 50 characters into the next chunk.
- *What I changed or overrode:* Two overrides. First, the blind character slice produced fragments like `"KE AGAIN: 82% | DIFFICULTY..."` — I directed Claude to switch to boundary-aware packing (accumulate whole review lines or syllabus paragraphs up to the ~300-char target, never mid-word). Second, after the boundary-packing rewrite made overlap structurally unnecessary (no opinion is ever split), I had Claude set overlap to 0 and document the rationale in `planning.md`.

**Instance 2 — Generation and grounding (`generate.py`)**

- *What I gave the AI:* The Retrieval Approach section, Evaluation Plan, pipeline diagram, and the already-working `retrieve.py` as context. I specified that source attribution must be programmatic (not LLM-generated) and that out-of-scope queries must return a fixed, testable decline phrase.
- *What it produced:* A working `ask()` function and system prompt with four numbered grounding rules, the numbered context block format (`[N] Source: ... | Professor: ...\n<text>`), and the fixed decline phrase in Rule 2.
- *What I changed or overrode:* The initial draft had the LLM produce source citations inside the answer text (e.g., "According to source 3..."). I overrode this to move attribution entirely out of the LLM's output: `ask()` now extracts `source` fields from chunk metadata after the call, deduplicates them, and returns them as a separate list. This eliminates any risk of the LLM hallucinating a file name it saw in the context prefix.
