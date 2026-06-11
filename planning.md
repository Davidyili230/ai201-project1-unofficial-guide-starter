# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
     Student reviews of CS professors at [university]. This knowledge is valuable because students often rely on only one or two sources when evaluating professors, but outdated reviews can provide misleading information. Multiple platforms offer anonymous reviews that encourage candid feedback. Official course evaluations are often not public, limited to end-of-semester snapshots, and lack the depth and currency of crowdsourced reviews. By aggregating the newest information across diverse sources, we create a more complete, real-time picture than any single channel provides.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | RateMyProfessors | CS dept professor reviews (ratings, comments) | https://www.ratemyprofessors.com |
| 2 | Reddit r/[university] | Student discussions about CS professors and courses | https://www.reddit.com/r/[university]/ |
| 3 | Reddit r/compsci | General CS education experiences and professor recommendations | https://www.reddit.com/r/compsci/ |
| 4 | Course Evaluations Archive | Official end-of-semester course feedback (if public) | Internal university records |
| 5 | Discord/Slack channels | Real-time student peer reviews and course recommendations | Campus communities |
| 6 | CS Department Review Portal | Department-specific professor feedback (if available) | Departmental intranet |
| 7 | Course forums (Piazza, Ed) | Student and TA comments about professor teaching style | Course-specific platforms |
| 8 | Alumni social groups | Post-graduation reflections on CS professors and their impact | Facebook groups, LinkedIn |
| 9 | GitHub discussions | Open-source course discussions and retrospectives | GitHub course repos |
| 10 | University course reviews | Aggregated reviews from multiple semesters | Campus-wide review platform |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
