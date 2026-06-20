# Full Build Log — Ireland Public Services AI Advisor

A running record of every decision, bug, and lesson from building a production-grade RAG chatbot for Irish public services from scratch.

---

## What We Set Out To Do

Build a production-grade RAG chatbot for Irish public services and learn the engineering behind every decision as we went — from the first SQL query to a GDPR-compliant live deployment at zero hosting cost.

---

## v0.1 — Core RAG Pipeline

### Infrastructure

```
Docker Compose
├── Postgres 16 + pgvector   ← stores documents, chunks, 384-dim vectors
└── Redis 7                  ← ready for caching and sessions
```

One command to start: `make db-up`

### Database Schema

Two tables designed for RAG:

**documents** — one row per government page
- `id, source, url, title, content_hash`
- `content_hash` makes ingestion idempotent — rerun it, only changed pages re-embed

**chunks** — one row per passage
- `content` — the text
- `content_tsv` — Postgres TSVECTOR (generated, stored) for BM25 search
- `embedding vector(384)` — pgvector column for dense search
- GIN index on `content_tsv` for fast full-text search

### Ingestion Pipeline

```
Citizens Information page
  ↓
[Chunker]     512-word chunks, 50-word overlap
  ↓
[Embedder]    BAAI/bge-small-en-v1.5 — 134MB, CPU
  ↓
[DB Writer]   batch insert chunks + embeddings
```

Cloudflare blocked direct crawling, so we built 15 hand-crafted fixture documents covering what a new arrival in Ireland needs: Stamp 1G, Critical Skills Permit, IRP, PPSN, Medical Card, USC, Income Tax, Jobseeker's Benefit, Child Benefit, Tenants' Rights, Bank Accounts, Minimum Wage.

### RAG Pipeline

```
User question
  ↓
[BM25 search]              [Dense search]
Postgres tsvector           pgvector cosine similarity
top 20 keyword results      top 20 semantic results
  ↓                         ↓
         [RRF Fusion]
         score = 1/(60+rank_bm25) + 1/(60+rank_dense)
         documents in both lists get boosted
         ↓
         [Llama 3.1 8B via NVIDIA API]
         system prompt forces [n] citations
         streams tokens one-by-one
         ↓
         [SSE → Next.js chat UI]
         tokens render as they arrive, citations at the end
```

### API

`POST /v1/chat/messages` — returns Server-Sent Events:
- `event: meta` — retrieved chunk count
- `event: token` — one token at a time (~100–200 per response)
- `event: citations` — 5 source passages with title, URL, snippet
- `event: done` — stream complete

### Frontend

Next.js 14 + Tailwind CSS:
- Messages stream token-by-token with cursor animation
- Citation chips appear below each answer with clickable source links
- Auto-scrolls as tokens arrive

### Bugs Fixed

| Bug | Root Cause | Fix |
|---|---|---|
| Cloudflare 403 | Bot detection on Citizens Information | Built fixture data instead of crawling |
| Migration failed | SQLAlchemy can't map vector type natively | Rewrote as raw SQL with `op.execute()` |
| asyncpg syntax error | `$1::vector` — asyncpg replaces `:param` with `$1`, breaking `::` cast | Inlined vector as numeric literal (fixed in v0.6 with proper parameterization) |
| Concurrent session crash | `asyncio.gather` on two queries on same SQLAlchemy session | Ran BM25 and dense search sequentially |
| NVIDIA 70B timeout | Free-tier cold start ~36s | Switched to 8B for dev |
| IndexError at stream end | NVIDIA sends final chunk with `choices=[]` | Added `if not chunk.choices: continue` guard |

---

## v0.2 — Eval Harness

You can't improve a RAG system without measuring it first. Any change might quietly break retrieval.

### Gold Q&A Pairs

30 pairs: 2 per document. Each has:
- The question
- The expected source URL(s)
- Key facts that should appear in the answer

### Retrieval Eval

`retrieval_eval.py`:
- Embeds each question, runs the full retrieval pipeline
- Measures **Recall@5** (did the right document appear in the top 5?)
- Measures **Mean Reciprocal Rank** (how high was the right document?)
- **Results: 100% Recall@5, avg rank 1.0**

### Answer Eval (LLM-as-judge)

`answer_eval.py`:
- Runs the full pipeline (retrieval + generation) for each question
- Asks the LLM to score faithfulness: "Does this answer only use information from the context?"
- **Results: 0.93/1.0 faithfulness**

### CI Gates

GitHub Actions (`eval.yml`):
- Retrieval eval runs on every PR — blocks merge if Recall@5 drops below threshold
- Answer eval runs on push to main

---

## v0.3 — Better Retrieval

### Hierarchical Chunking

The core insight: small chunks for retrieval precision, large chunks for LLM context.

- **Child chunks**: 128 words — precise match targets for BM25 and vector search
- **Parent chunks**: 512 words — the broader passage sent to the LLM for answer generation
- Result: retrieval finds the exact sentence, but the LLM sees the full paragraph

### HNSW Index

Switched from exact search to approximate nearest-neighbour (HNSW) via pgvector. Cuts vector search latency significantly as the knowledge base scales.

### Cross-Encoder Reranker

Added `BAAI/bge-reranker-base` after RRF fusion. Unlike embeddings (which compare vectors), a cross-encoder reads the query and passage together — much more accurate.

Pipeline: BM25 (top 20) + Dense (top 20) → RRF → Reranker → top 5 → LLM.

### Revenue.ie Added

Second source integrated. Knowledge base: 20 documents.

---

## v0.4 — Live Deployment (Free Stack)

Every component running in production at $0/month:

| Component | Provider | Spec |
|---|---|---|
| Backend | Hugging Face Spaces | Docker, 2 vCPU, 16 GB RAM |
| Frontend | Vercel | Next.js, Edge CDN |
| Database | Supabase | Postgres 16 + pgvector, EU West |
| Cache | Upstash | Serverless Redis, EU West |

Cold-start challenge: HF Spaces sleeps after ~15 min inactivity. Solution: frontend pings `/v1/health` on page load so the backend is warm by the time the user types.

---

## v0.5 — Expanded Knowledge Base

### Scale: 20 → 1,640 Documents

Built a proper multi-source web crawler with:
- Per-site URL filters (domain allowlists, path filters)
- Sitemap support for discovery
- Brotli-safe HTTP headers
- Idempotent: content hash comparison skips unchanged pages

Sources added: Gov.ie/DSP, RTB, WRC, HSE, expanded Revenue.ie.
Total: 16,326 vector chunks in Supabase.

### LLM Upgrade

Switched from Llama 3.1 8B → Llama 3.3 70B. Much better answer quality, especially for complex multi-step questions.

### Privacy Notice

Terms and privacy notice added inline to the UI — users are informed that queries are processed by NVIDIA's API before they type their first message.

---

## v0.6 — Production Hardening

Everything that makes the difference between a demo and something you'd actually give to someone to use.

### 16 Issues Fixed

Starting from an honest analysis of the project: gaps in correctness, UX, security, legal compliance, and test coverage.

#### Correctness

**React key anti-pattern** — messages were keyed by array index (`key={i}`). When React reconciles a list keyed by index, reordering or deletion causes it to reuse the wrong component state. Fixed by assigning each message a stable `crypto.randomUUID()` at creation.

**ISD source misrepresentation** — the UI listed "Irish Immigration (ISD)" as a source. The crawler had never indexed irishimmigration.ie. Fixed: UI now shows the six sources that are actually indexed (CI, Revenue, DSP, RTB, WRC, HSE).

**SQL injection in dense_search** — the embedding vector was interpolated directly into the SQL string as an f-string. An embedding is model-generated floating-point data, not user input, so the actual exploit risk was low — but the pattern was wrong. Fixed by using `CAST(:vec AS vector)` with a SQLAlchemy bound parameter.

#### UX

**Raw markdown in chat** — LLM responses containing `**bold**`, `- bullets`, and `[links]` rendered as literal characters. Added `react-markdown` + `@tailwindcss/typography` so the output renders correctly.

**No way to copy an answer** — added a copy-to-clipboard button on every completed assistant message (SVG icon, 2s checkmark confirmation).

**No shareable links** — added a share button that copies `/chat?q=<encoded-question>` to the clipboard so users can link to specific questions.

**No source freshness** — users had no way to know if the cited content was from last week or last year. Fixed by surfacing `crawled_at` through the retrieval pipeline (both BM25 and dense search queries) and displaying it as "Jun 2025" on each citation chip.

**No way to start over** — added a "New conversation" button that resets client state and issues a new `conversation_id` to clear the server session.

#### Security & Reliability

**No rate limiting** — the chat endpoint had no protection against quota exhaustion. One malicious or runaway client could burn the NVIDIA free-tier allocation for everyone. Added `slowapi` — 10 requests/minute per IP, HTTP 429 with `Retry-After` on breach.

**No query caching** — every question triggered a full embedding + dual DB search + reranker pass, even for identical queries. Added Redis cache (6-hour TTL, keyed by SHA-256 of the normalised query). Cache misses fall through transparently; hits return instantly.

#### Legal Compliance

**No standalone privacy notice** — the inline disclaimer didn't meet GDPR Article 13 requirements, which mandate a structured notice identifying the controller, legal basis, processors, transfer mechanisms, retention period, and all eight data subject rights. Built `/privacy` as a proper route with: controller identity, legal basis (Art. 6(1)(b) for service delivery; Art. 46(2)(c) SCCs + EU-US DPF for NVIDIA transfer), processor table (NVIDIA, Vercel, Hugging Face, Supabase, Upstash), retention policy, all eight data subject rights, and controller contact.

#### Features

**Multi-turn conversation** — each chat generates a UUID that acts as a session key. The backend stores up to 3 prior exchanges (30-min TTL, in-memory) and passes them as history to the LLM. Follow-up questions like "what about for EU citizens?" now work correctly.

**Feedback loop** — thumbs up/down buttons on each answer. The question is SHA-256 hashed client-side before submission — the raw query never reaches the feedback endpoint. The backend stores `question_hash + rating + timestamp`. This is the foundation for identifying which topics the system struggles with.

#### Tests

**No unit tests** — the project had a gold eval suite but no unit tests for the core library code. Added 28 tests:
- `test_chunker.py` (11): child ≤128 words, parent ≤512 words, parent contains child, sequential indices, min-length guard, `token_count` accuracy, custom sizes
- `test_retrieval.py` (9): empty inputs, single-source, final_k cap, shared-doc boosting, descending score order, metadata propagation
- `test_pipeline.py` (8): SHA-256 determinism, 64-char hex output, whitespace sensitivity, provided-hash priority

#### CI

**No automated re-crawl** — content aged silently. Added `recrawl.yml`: cron every Sunday 02:00 UTC, connecting to production Supabase via secrets. Also triggerable manually with optional `--source` and `--max-pages` overrides via `workflow_dispatch`.

---

## What We Learned

### RAG Engineering
- BM25 wins on exact terminology (tax codes, scheme names); dense search wins on paraphrased questions
- Hierarchical chunking (small for retrieval, large for generation) is the right default
- Cross-encoder reranking meaningfully improves answer quality — worth the latency
- RRF is a strong baseline for fusion with no tuning required

### Database
- pgvector HNSW index needed explicit tuning (`m=16, ef_construction=64`) to behave well at scale
- tsvector GIN index is essential — without it, BM25 scans the full table
- Alembic needs a sync connection even in an async app

### Production
- Cold starts are a real product problem, not just a latency number — solved with a health-check ping on page load
- Rate limiting is essential before any public deploy — even on a personal project
- SHA-256 keying for cache and feedback lets you store derived data without storing PII

### Legal
- GDPR Article 13 requires more than a one-line disclaimer — it needs a structured notice with processor table, transfer mechanisms, retention periods, and all eight data subject rights
- Third-country transfers (NVIDIA US, Vercel US, HF US) each need a mechanism: SCCs and/or the EU-US DPF

### Frontend
- `key={index}` on a list is one of the most common React bugs and hardest to notice in testing
- SSE is the right transport for token streaming — simpler than WebSockets, stateless, resumable

---

## Stack Summary

| Concern | Choice | Reason |
|---|---|---|
| LLM | NVIDIA NIM (Llama 3.3 70B) | Free, high quality |
| Fallback LLM | Anthropic (Claude) | Config switch, no code change |
| Vector DB | Supabase (pgvector) | Free EU West tier, stays in EEA |
| Cache | Upstash Redis | Free EU West tier, serverless |
| Frontend hosting | Vercel | Free, instant deploy |
| Backend hosting | Hugging Face Spaces | Free, Docker, 16 GB RAM for ML models |
| Embeddings | BAAI/bge-small-en-v1.5 | 134 MB, CPU-only, strong for English |
| Reranker | BAAI/bge-reranker-base | ~1.1 GB, CPU, cross-encoder |
| Rate limiting | slowapi | Integrates natively with FastAPI |
| Migrations | Alembic | Industry standard for SQLAlchemy |

**Total cost: $0/month.** Every component is on a free tier.
