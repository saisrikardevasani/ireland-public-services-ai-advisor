# Ireland Public Services AI Advisor

A production-grade RAG (Retrieval-Augmented Generation) chatbot that answers questions about Irish public services — tax, benefits, housing, employment, tenancy, and workplace rights — with **cited, grounded answers** linked directly to official government sources.

Built from scratch as a real engineering project. Every answer cites its source so you can verify it yourself.

---

## Try It Live

> **Chat UI:** https://irish-public-services-ai-advisor.vercel.app
>
> **Backend API docs:** https://srikarcod3r-eu-ireland-advisor.hf.space/docs

**Cold start note:** The backend runs on Hugging Face Spaces free tier, which sleeps after ~15 minutes of inactivity. The chat page pings it automatically on load, so by the time you type your first question it's usually warm. If it isn't, an amber banner appears (~30s wakeup). Subsequent messages are instant.

Health check: https://srikarcod3r-eu-ireland-advisor.hf.space/v1/health — should return `{"status":"ok","database":"connected"}`.

---

## What It Does

Ask something like *"How do I apply for a medical card?"* or *"What's the minimum wage in Ireland?"* and the system:

1. Converts your question into a 384-dimensional embedding vector
2. Runs **hybrid retrieval** — BM25 keyword search + dense vector search — across 1,640 official government documents
3. Merges both result lists using **Reciprocal Rank Fusion (RRF)**
4. Re-ranks with a **cross-encoder** (reads query + passage together — far more accurate than cosine similarity alone)
5. Streams a grounded answer token-by-token from **Llama 3.3 70B** via NVIDIA's free API
6. Returns citation chips — every claim links to the exact government page it came from

The model is explicitly instructed not to answer from general knowledge. If it's not in the retrieved documents, it says so.

---

## Architecture

```
User question
     │
     ▼
[Embedder] — BAAI/bge-small-en-v1.5 (384-dim, runs inside the container)
     │
     ├─────────────────────────────────┐
     ▼                                 ▼
[BM25 Search]                   [Dense Search]
Postgres tsvector               pgvector + HNSW index
top 20 by term frequency        top 20 by cosine similarity
     │                                 │
     └──────────────┬──────────────────┘
                    ▼
             [RRF Fusion]
             score = Σ 1/(60 + rank)
             top 20 merged candidates
                    │
                    ▼
      [Cross-Encoder Reranker]
      BAAI/bge-reranker-base
      reads (query + passage) together
      picks top 5 — uses parent chunk for wider context
                    │
                    ▼
       [Llama 3.3 70B via NVIDIA NIM]
       streams answer with [n] citation markers
                    │
                    ▼
      [Server-Sent Events → Next.js UI]
```

**Caching:** Repeated questions hit a Redis cache (6-hour TTL, SHA-256 keyed) and skip the database entirely.

**Multi-turn:** Sessions maintain up to 3 prior exchanges (30-minute TTL) keyed by a UUID generated per conversation — history is passed to the LLM so follow-up questions work naturally.

---

## Tech Stack

| Layer | Technology | Cost |
|---|---|---|
| **Frontend** | Next.js 16 + Tailwind CSS + react-markdown | Free (Vercel) |
| **Backend** | FastAPI + Python 3.11 | Free (Hugging Face Spaces) |
| **Database** | PostgreSQL 16 + pgvector | Free (Supabase, EU West) |
| **Vector index** | HNSW via pgvector | — |
| **Full-text search** | Postgres tsvector + GIN index | — |
| **Cache** | Redis (serverless) | Free (Upstash, EU West) |
| **Rate limiting** | slowapi (10 req/min per IP) | — |
| **Embeddings** | BAAI/bge-small-en-v1.5 | Free (runs in container) |
| **Reranker** | BAAI/bge-reranker-base | Free (runs in container) |
| **LLM** | Llama 3.3 70B via NVIDIA NIM | Free tier |
| **Migrations** | Alembic | — |

**Total hosting cost: $0/month.**

---

## What's Covered

The knowledge base has **1,640 documents** across six official Irish government sources (16,326 vector chunks):

| Source | Coverage |
|---|---|
| **Citizens Information** | Immigration, tax, welfare, healthcare, housing, employment |
| **Revenue.ie** | PAYE, VAT, CGT, income tax, credits, tax returns |
| **Gov.ie / DSP** | Department of Social Protection — all benefits and schemes |
| **RTB** | Residential Tenancies Board — landlord/tenant rights, disputes |
| **WRC** | Workplace Relations Commission — employment rights, complaints |
| **HSE** | Health Service Executive — healthcare entitlements, services |

All content is crawled from official government websites and re-indexed automatically every Sunday (GitHub Actions cron).

---

## Versions

### v0.1 — Working RAG pipeline
Core pipeline: FastAPI backend, hybrid BM25 + dense retrieval, RRF fusion, streaming Next.js UI. 15 Citizens Information documents. NVIDIA free API for the LLM.

### v0.2 — Eval harness
30 gold Q&A pairs (2 per document). Automated retrieval eval measuring Recall@5 and Mean Reciprocal Rank. LLM-as-judge faithfulness scoring. GitHub Actions CI — retrieval eval on every PR, answer eval on push to main.

**Results:** 100% Recall@5 · Avg rank 1.0 · Faithfulness 0.93/1.0

### v0.3 — Better retrieval
Hierarchical chunking: child chunks (128 words) for retrieval precision, parent chunks (512 words) sent to the LLM for wider context. HNSW vector index for faster ANN search. Cross-encoder reranker added after RRF. Revenue.ie added as a second source.

### v0.4 — Deployed (free stack)
Everything live at zero cost: backend on Hugging Face Spaces (Docker, 2 vCPU / 16 GB RAM), frontend on Vercel, database on Supabase, cache on Upstash.

### v0.5 — Expanded knowledge base
- Knowledge base scaled from 20 → **1,640 documents** across six sources
- 16,326 vector chunks indexed in Supabase
- Multi-source web crawler with per-site URL filters, sitemap support, brotli-safe headers
- LLM upgraded from Llama 3.1 8B → Llama 3.3 70B
- Terms & Privacy notice in the UI

### v0.6 — Production hardening (current)

**Frontend**
- Markdown rendering: LLM output now renders bold, bullets, links correctly via `react-markdown` + `@tailwindcss/typography`
- Copy button on every completed assistant message
- Shareable link button — copies `/chat?q=...` URL to clipboard
- Source freshness dates on every citation chip (crawled date from the database)
- Multi-turn: "New conversation" button resets both client state and server session
- Feedback: thumbs up/down on answers — question is SHA-256 hashed client-side before submission (no raw query text stored)
- React key anti-pattern fixed: messages now use stable `crypto.randomUUID()` IDs instead of array index
- Standalone `/privacy` page — full GDPR Article 13 notice with controller identity, legal basis, transfer mechanisms, processor table, and all eight data subject rights

**Backend**
- Rate limiting: slowapi — 10 requests/minute per IP on the chat endpoint
- Input validation: 2,000-character max on chat requests
- Redis query cache: identical questions skip the database and embedding pipeline (6-hour TTL, SHA-256 keyed, no PII)
- SQL injection fix: dense search vector now passed as a bound parameter (`CAST(:vec AS vector)`) instead of f-string interpolation
- Source freshness: `crawled_at` timestamp surfaced through retrieval pipeline to the frontend
- Multi-turn conversation: in-memory session store (30-min TTL, max 3 prior exchanges) keyed by UUID
- Feedback endpoint: `POST /v1/feedback` stores `question_hash + rating` only — no raw queries
- Alembic migration 003: `feedback` table

**CI / Quality**
- Weekly re-crawl: GitHub Actions cron every Sunday 02:00 UTC, also manually triggerable with `--source` and `--max-pages` overrides
- 28 unit tests across chunker (11), RRF fusion (9), and pipeline hash logic (8) — all passing

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py           # POST /v1/chat/messages — SSE streaming, rate-limited
│   │   │   ├── feedback.py       # POST /v1/feedback — stores hash+rating, no PII
│   │   │   └── health.py         # GET /v1/health + root redirect to /docs
│   │   ├── ingestion/
│   │   │   ├── chunker.py        # Hierarchical chunking (child 128w + parent 512w)
│   │   │   ├── pipeline.py       # Ingest orchestrator — idempotent, hash-deduped
│   │   │   ├── sources.py        # Per-source crawl config (URL filters, sitemaps)
│   │   │   └── web_crawler.py    # Multi-source async crawler
│   │   ├── models/
│   │   │   └── schema.py         # SQLAlchemy ORM: Document, Chunk, Feedback tables
│   │   ├── pipeline/
│   │   │   ├── generator.py      # LLM answer generation (NVIDIA or Anthropic) + history
│   │   │   ├── reranker.py       # Cross-encoder reranking
│   │   │   └── retrieval.py      # BM25 + dense + RRF + crawled_at timestamp
│   │   ├── cache.py              # Redis query cache (6h TTL, SHA-256 key, no PII)
│   │   ├── session.py            # In-memory conversation sessions (30min TTL, max 3 turns)
│   │   ├── config.py             # All config via pydantic-settings + .env
│   │   ├── database.py           # Async SQLAlchemy engine and session
│   │   └── main.py               # FastAPI app, CORS, rate limiter, routers
│   ├── eval/
│   │   ├── gold_qa.json          # 30 gold Q&A pairs with expected URLs and key facts
│   │   ├── retrieval_eval.py     # Recall@5, MRR, average rank
│   │   └── answer_eval.py        # LLM-as-judge faithfulness scoring
│   ├── fixtures/
│   │   ├── citizens_information.json
│   │   ├── revenue_ie.json
│   │   ├── revenue_ie_expanded.json
│   │   ├── dsp.json
│   │   ├── hse.json
│   │   ├── rtb.json
│   │   └── wrc.json
│   ├── migrations/
│   │   └── versions/
│   │       ├── 001_initial.py
│   │       ├── 002_hierarchical_chunks.py
│   │       └── 003_feedback_table.py
│   ├── scripts/
│   │   ├── seed.py               # Load fixtures into the database
│   │   └── ingest.py             # Live web crawler (multi-source)
│   ├── tests/
│   │   └── unit/
│   │       ├── test_chunker.py   # 11 tests: child size, parent window, overlap, min-length
│   │       ├── test_retrieval.py # 9 tests: RRF fusion, score ordering, metadata
│   │       └── test_pipeline.py  # 8 tests: hash deduplication logic
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx          # Landing page with example questions and source list
│       │   ├── chat/page.tsx     # Chat UI — streaming, multi-turn, feedback, share
│       │   └── privacy/page.tsx  # GDPR Article 13 Privacy Notice
│       ├── components/
│       │   ├── ChatMessage.tsx   # Bubbles + markdown + copy + share + feedback + citations
│       │   └── ChatInput.tsx     # Text input + send button
│       ├── lib/api.ts            # SSE streaming client (passes conversation_id)
│       └── types/index.ts        # Message, Citation interfaces (with id, crawled_at)
├── .github/
│   └── workflows/
│       ├── eval.yml              # CI: retrieval eval on PR, answer eval on main push
│       └── recrawl.yml           # Weekly re-crawl every Sunday 02:00 UTC
├── docker-compose.yml            # Local dev: Postgres + Redis in Docker
├── Makefile                      # Shortcuts for all common dev commands
└── .env.example                  # Template — copy to backend/.env and fill in keys
```

---

## Running Locally

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 18+
- A free NVIDIA API key — [build.nvidia.com](https://build.nvidia.com)

### 1. Clone and configure

```bash
git clone https://github.com/saisrikardevasani/ireland-public-services-ai-advisor.git
cd ireland-public-services-ai-advisor

cp .env.example backend/.env
# Open backend/.env and paste your NVIDIA_API_KEY
```

### 2. Start the database

```bash
make db-up
```

Starts Postgres 16 (with pgvector) and Redis in Docker.

### 3. Run migrations

```bash
make migrate
```

### 4. Seed the database

```bash
make seed
```

Loads all fixture documents. First run downloads the 134 MB embedding model (~30s). Subsequent runs are instant (idempotent — only changed pages re-embed).

### 5. Start the backend

```bash
make backend
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 6. Start the frontend

```bash
make frontend
# UI at http://localhost:3000
```

---

## API Reference

### `POST /v1/chat/messages`

Rate-limited to 10 requests/minute per IP. Streams a grounded answer as Server-Sent Events.

**Request:**
```json
{
  "message": "How do I apply for a medical card?",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

`conversation_id` is optional. If provided, the last 3 turns of that session are included as history so follow-up questions work. Generate one with `crypto.randomUUID()` on the client.

**Response stream:**
```
event: meta
data: {"retrieved_count": 5}

event: token
data: {"text": "To apply"}

event: token
data: {"text": " for a medical card..."}

event: citations
data: {"citations": [{"n": 1, "title": "Medical Card", "url": "https://...", "snippet": "...", "crawled_at": "2025-06-14"}]}

event: done
data: {"message": "Stream complete"}
```

---

### `POST /v1/feedback`

Stores a thumbs up/down rating. No raw query text is stored — the client hashes the question with SHA-256 before sending.

**Request:**
```json
{
  "question_hash": "a3f2c1...",
  "rating": 1
}
```

`rating` must be `1` (helpful) or `-1` (not helpful). Returns HTTP 204 on success.

---

### `GET /v1/health`

```json
{"status": "ok", "database": "connected"}
```

---

## Configuration

Copy `.env.example` to `backend/.env`. Never commit `backend/.env`.

### Database

| Variable | Example | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/db` | Runtime (async). Must use `asyncpg` driver prefix. |
| `DATABASE_SYNC_URL` | `postgresql://user:pass@host:5432/db` | Alembic migrations only (sync). Same host, no `+asyncpg`. |
| `REDIS_URL` | `redis://localhost:6379` | Use `rediss://` (double-s) for TLS (Upstash). |

### LLM

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `nvidia` | `nvidia` for NVIDIA NIM (free), `anthropic` for Claude. |
| `NVIDIA_API_KEY` | — | Required when `LLM_PROVIDER=nvidia`. Free at [build.nvidia.com](https://build.nvidia.com). |
| `NVIDIA_MODEL` | `meta/llama-3.3-70b-instruct` | Best quality on the free tier. |
| `ANTHROPIC_API_KEY` | — | Required when `LLM_PROVIDER=anthropic`. |

### Embeddings & Reranking

| Variable | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | 134 MB, 384-dim, CPU. Downloads automatically on first run. |
| `EMBEDDING_DIM` | `384` | Must match the model. Change both together or pgvector rejects inserts. |
| `RERANKER_MODEL` | `BAAI/bge-reranker-base` | Cross-encoder, ~1.1 GB, CPU. |
| `RERANKER_ENABLED` | `true` | Set `false` to skip reranking (useful if RAM-constrained). |

### Retrieval tuning

| Variable | Default | Description |
|---|---|---|
| `BM25_TOP_K` | `20` | Candidates from BM25 before RRF. |
| `DENSE_TOP_K` | `20` | Candidates from vector search before RRF. |
| `FINAL_TOP_K` | `5` | Chunks sent to the LLM after reranking. |

Pipeline: BM25 (top 20) + Dense (top 20) → RRF merge → Reranker → top 5 → LLM.

### App

| Variable | Default | Description |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins. Set to your frontend URL in production. |
| `DEBUG` | `false` | Verbose logging. Don't set in production. |

---

## Eval Results (v0.3)

Run against 30 gold Q&A pairs covering all 20 documents.

| Metric | Score |
|---|---|
| Recall@5 | **100%** — right document in top 5 for every question |
| Average rank | **1.0** — right document ranked #1 on average |
| Faithfulness | **0.93 / 1.0** — answers grounded in retrieved context |

---

## Unit Tests

28 tests, all passing. Run with:

```bash
cd backend
.venv/bin/python -m pytest tests/unit/ -v
```

| File | Tests | What's covered |
|---|---|---|
| `test_chunker.py` | 11 | Child size ≤128 words, parent ≤512 words, parent contains child, sequential indices, min-length guard, token count accuracy |
| `test_retrieval.py` | 9 | RRF empty inputs, single-source, final_k cap, shared-doc boosting, score ordering, metadata propagation |
| `test_pipeline.py` | 8 | SHA-256 hash determinism, 64-char hex output, whitespace sensitivity, provided-hash vs computed-hash logic |

---

## Privacy & Legal

**Not legal or professional advice.** All answers are informational summaries of publicly available official guidance. Nothing here constitutes legal, tax, or financial advice. Always verify with the relevant authority or consult a qualified professional.

**How queries are processed.** Questions are transmitted to NVIDIA's AI inference API (Llama 3.3 70B, US-based) to generate a response. This service does not log, store, or retain raw user queries. Feedback ratings are stored as SHA-256 hashes only — no query text. See the full [Privacy Notice](https://irish-public-services-ai-advisor.vercel.app/privacy) (GDPR Art. 13 compliant).

**Do not include personal information** in queries — no PPS numbers, addresses, passport numbers, or financial details.

**Official sources:**
- [citizensinformation.ie](https://www.citizensinformation.ie)
- [revenue.ie](https://www.revenue.ie)
- [gov.ie / DSP](https://www.gov.ie/en/organisation/department-of-social-protection/)
- [rtb.ie](https://www.rtb.ie)
- [workplacerelations.ie](https://www.workplacerelations.ie)
- [hse.ie](https://www.hse.ie)

Knowledge base last crawled June 2026. Government policy changes — always verify with the official source.

---

## License

[Apache 2.0](LICENSE)

---

## Contributing

Issues and PRs welcome. To add more documents to the knowledge base, add them to `backend/fixtures/` in the same JSON format as existing files and run `make seed`.
