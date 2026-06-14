Full Recap — EU & Ireland Public Services AI Advisor

---

  What We Set Out To Do

  Build a production-grade RAG chatbot for Irish public services from scratch — and learn the engineering behind
  every decision as we went.

---

  Week 1 (v0.1) — Everything We Built

  The Infrastructure

  Docker Compose
  ├── Postgres 16 + pgvector extension   ← stores documents, chunks, 384-dim vectors
  └── Redis 7                            ← ready for rate limiting / sessions

  Spun up with one command: make db-up

---

  The Database Schema

  Two tables, designed for RAG:

  documents — one row per Citizens Information page

- id, source, url, title, content_hash
- content_hash makes ingestion idempotent — rerun it, only changed pages get re-embedded

  chunks — one row per 512-word passage

- content — the text
- content_tsv — a Postgres TSVECTOR column (generated, stored) for BM25 search
- embedding vector(384) — the pgvector column for dense search
- GIN index on content_tsv — makes full-text search fast

---

  The Ingestion Pipeline

  Citizens Information page
    ↓
    [Chunker]         512-word chunks, 50-word overlap
    ↓
    [Embedder]        BAAI/bge-small-en-v1.5 — 134MB, runs locally on CPU
    ↓
    [DB Writer]       batch insert chunks + embeddings

  Because crawling the live site was blocked by Cloudflare, we built 15 hand-crafted fixture documents covering
  every topic a new arrival in Ireland would need: Stamp 1G, Critical Skills Permit, IRP, PPSN, Medical Card,
  USC, Income Tax, Jobseeker's Benefit, Child Benefit, Tenants' Rights, Bank Accounts, Minimum Wage.

  Seed with: make seed

---

  The RAG Pipeline

  User question: "When can I switch from Stamp 2 to Stamp 1G?"
           ↓
  [Embed query]   →   384-dim float vector
    ↓
  [BM25 search]                    [Dense search]
  Postgres tsvector + ts_rank_cd   pgvector cosine similarity (<=>)
  top 20 by keyword relevance      top 20 by semantic similarity
    ↓                               ↓
    [RRF Fusion]
    score = 1/(60+rank_bm25) + 1/(60+rank_dense)
    top 5 chunks — documents in both lists get boosted
    ↓
    [Llama 3.1 8B via NVIDIA API]
    System prompt forces citation of every claim with [n]
    Streams tokens one-by-one
    ↓
    [SSE → Next.js chat UI]
    Tokens render as they arrive, citations appear at the end

---

  The API

  POST /v1/chat/messages — returns a Server-Sent Events stream:

  event: meta       ← how many chunks were retrieved
  event: token      ← one token at a time (×100-200 per response)
  event: citations  ← 5 source passages with title, URL, snippet
  event: done       ← stream is finished

---

  The Frontend

  Next.js 14 + Tailwind CSS chat interface:

- Messages stream in token-by-token (cursor animation while generating)
- Citation chips appear below each answer with clickable source links
- Auto-scrolls as tokens arrive

---

  Bugs We Debugged Together

  ┌───────────────────┬──────────────────────────────────────────────┬──────────────────────────────────────┐
  │        Bug        │                  Root Cause                  │                 Fix                  │
  ├───────────────────┼──────────────────────────────────────────────┼──────────────────────────────────────┤
  │ Cloudflare 403    │ Bot detection on Citizens Information        │ Built fixture data instead of        │
  │                   │                                              │ crawling                             │
  ├───────────────────┼──────────────────────────────────────────────┼──────────────────────────────────────┤
  │ Migration failed  │ SQLAlchemy can't map vector type natively    │ Rewrote migration as raw SQL with    │
  │                   │                                              │ op.execute()                         │
  ├───────────────────┼──────────────────────────────────────────────┼──────────────────────────────────────┤
  │ asyncpg syntax    │ $1::vector — asyncpg replaces :param with $1 │ Inlined the vector as a numeric      │
  │ error             │  which breaks the :: cast                    │ literal in an f-string               │
  ├───────────────────┼──────────────────────────────────────────────┼──────────────────────────────────────┤
  │ Concurrent        │ asyncio.gather ran two queries on the same   │ Ran BM25 and dense search            │
  │ session crash     │ SQLAlchemy session                           │ sequentially                         │
  ├───────────────────┼──────────────────────────────────────────────┼──────────────────────────────────────┤
  │ NVIDIA 70B        │ Free tier cold-start is ~36 seconds          │ Switched to 8B model (70ms) for dev  │
  │ timeout           │                                              │                                      │
  ├───────────────────┼──────────────────────────────────────────────┼──────────────────────────────────────┤
  │ IndexError at     │ NVIDIA sends a final chunk with choices = [] │ Added if not chunk.choices: continue │
  │ stream end        │                                              │  guard                               │
  └───────────────────┴──────────────────────────────────────────────┴──────────────────────────────────────┘

---

  What We Published to GitHub

  https://github.com/saisrikardevasani/eu-ireland-public-services-ai-advisor

- README.md — architecture diagram, quick start, API reference, roadmap
- LICENSE — Apache 2.0 (free to use, fork, build on)
- SECURITY.md — vulnerability reporting, SQL injection prevention, secret management
- .env.example — template with placeholder values, safe to commit
- .gitignore — blocks .env, .venv, node_modules, model cache binaries

  Real API key was confirmed clean before every commit.

---

  Concepts You Learned

- RAG — why grounding LLMs in retrieved documents prevents hallucination
- BM25 vs dense search — when keywords win, when semantics win, why you want both
- RRF — how to fuse ranked lists without tuning weights
- pgvector — storing and searching vectors inside Postgres
- tsvector / GIN index — how Postgres does full-text search
- SSE — why it beats WebSockets for one-way LLM streaming
- asyncpg quirks — why ::cast syntax conflicts with positional parameters
- pydantic-settings — type-safe config from .env
- Alembic — database migrations, why you use sync connections even in an async app

---

  What's Next — Week 2

  Eval harness — this is what separates a demo from a real system:

1. Write 30 gold Q&A pairs (question + ideal answer + which document should be retrieved)
2. Run retrieval on all 30 questions, measure recall@5 (did the right chunk land in the top 5?)
3. Run the full pipeline, measure faithfulness with RAGAS (did the answer only use retrieved context?)
4. Set CI gates — if recall drops below 80% or faithfulness below 0.7, the PR is blocked

  Without this, you can't safely improve the system — any change might quietly break retrieval and you'd never
  know.
