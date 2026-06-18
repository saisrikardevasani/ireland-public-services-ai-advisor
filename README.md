# Ireland Public Services AI Advisor

A RAG (Retrieval-Augmented Generation) chatbot that answers questions about Irish public services — immigration, tax, benefits, housing, and employment — with **cited, grounded answers** linked directly to official government sources.

Built as a real engineering project from scratch, not a tutorial. Every answer cites its source so you can verify it yourself.

---

## Try It Live

> **Frontend (chat UI):** https://irish-public-services-ai-advisor.vercel.app
>
> **Backend API:** https://srikarcod3r-eu-ireland-advisor.hf.space/docs

**A note on cold starts:** The backend runs on Hugging Face Spaces free tier, which sleeps after ~15 minutes of inactivity. The chat page pings the backend automatically when it loads, so by the time you type your question it's usually warm. If it isn't, an amber banner appears telling you it's waking up (~30s). Subsequent messages are instant.

If the chat doesn't respond at all, check whether the backend is alive:
https://srikarcod3r-eu-ireland-advisor.hf.space/v1/health

It should return `{"status":"ok","database":"connected"}`. If it does, the app is up.

---

## What It Does

Ask something like *"How do I apply for a medical card?"* or *"What's the minimum wage in Ireland?"* and the system:

1. Converts your question into a 384-dimensional embedding vector
2. Runs **hybrid retrieval** — BM25 keyword search and dense vector search — across 1,640 official government documents
3. Merges both result lists using **Reciprocal Rank Fusion (RRF)** to get the best 20 candidates
4. Re-ranks them with a **cross-encoder** (reads query + passage together — much more accurate than cosine similarity alone) to pick the top 5
5. Streams a grounded answer token-by-token from **Llama 3.3 70B** via the NVIDIA free API
6. Returns citation chips — every claim is linked to the exact government page it came from

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

---

## Tech Stack

| Layer | Technology | Cost |
|---|---|---|
| **Frontend** | Next.js 16 + Tailwind CSS | Free (Vercel) |
| **Backend** | FastAPI + Python 3.11 | Free (Hugging Face Spaces) |
| **Database** | PostgreSQL 16 + pgvector | Free (Supabase) |
| **Vector index** | HNSW via pgvector | — |
| **Full-text search** | Postgres tsvector | — |
| **Cache** | Redis (serverless) | Free (Upstash) |
| **Embeddings** | BAAI/bge-small-en-v1.5 | Free (runs locally in container) |
| **Reranker** | BAAI/bge-reranker-base | Free (runs locally in container) |
| **LLM** | Llama 3.3 70B via NVIDIA NIM | Free tier |
| **Migrations** | Alembic | — |

**Total hosting cost: $0/month.**

---

## What's Covered

The knowledge base has **1,640 documents** across six official Irish government sources (16,326 vector chunks in Supabase):

| Source | Coverage |
|---|---|
| **Citizens Information** | Immigration, tax, welfare, healthcare, housing, employment |
| **Revenue.ie** | PAYE, VAT, CGT, income tax, credits, tax returns |
| **Gov.ie / DSP** | Department of Social Protection — all benefits and schemes |
| **RTB** | Residential Tenancies Board — landlord/tenant rights, disputes |
| **WRC** | Workplace Relations Commission — employment rights, complaints |
| **ISD / Gov.ie** | Irish immigration (visa, IRP, employment permits) |

All content is crawled directly from official government websites and re-indexed periodically.

---

## Versions

### v0.1 — Working RAG pipeline
The core. FastAPI backend with hybrid BM25 + dense retrieval, RRF fusion, and a streaming Next.js UI. 15 Citizens Information documents. NVIDIA free API for the LLM.

### v0.2 — Eval harness
30 gold Q&A pairs (2 per document). Automated retrieval eval measuring Recall@5 and Mean Reciprocal Rank. LLM-as-judge faithfulness scoring. GitHub Actions CI — retrieval eval runs on every PR, answer eval runs on push to main.

**Results:** 100% Recall@5 · Avg rank 1.0 · Faithfulness 0.93/1.0

### v0.3 — Better retrieval
Hierarchical chunking: child chunks (128 words) used for retrieval precision, parent chunks (512 words) sent to the LLM for wider context. HNSW vector index for faster search. Cross-encoder reranker added after RRF fusion. Revenue.ie added as a second source — 20 documents total.

### v0.4 — Deployed (free stack)
Everything running live at zero cost:
- Backend on Hugging Face Spaces (Docker, 2 vCPU, 16 GB RAM — more than enough for the ML models)
- Frontend on Vercel
- Database on Supabase (PostgreSQL + pgvector)
- Cache on Upstash (serverless Redis)

### v0.5 — Expanded knowledge base + privacy notice
- Knowledge base scaled from 20 to **1,640 documents** across six sources (Citizens Information, Revenue, Gov.ie/DSP, RTB, WRC, ISD)
- 16,326 vector chunks indexed in Supabase
- Multi-source web crawler with per-site URL filters, sitemap support, and brotli-safe HTTP headers
- **Terms & Privacy notice added to the UI** — users are informed that queries are processed by NVIDIA's API (US-based, Llama 3.3 70B) before they send their first message
- LLM upgraded from Llama 3.1 8B to Llama 3.3 70B for better answer quality

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py           # POST /v1/chat/messages — SSE streaming endpoint
│   │   │   └── health.py         # GET /v1/health + root redirect to /docs
│   │   ├── ingestion/
│   │   │   ├── chunker.py        # Hierarchical chunking (child + parent windows)
│   │   │   ├── crawler.py        # Citizens Information web crawler
│   │   │   ├── embedder.py       # Sentence-transformer embedding
│   │   │   └── pipeline.py       # Ingest orchestrator — idempotent, safe to rerun
│   │   ├── models/
│   │   │   └── schema.py         # SQLAlchemy ORM: Document + Chunk tables
│   │   ├── pipeline/
│   │   │   ├── generator.py      # LLM answer generation (NVIDIA or Anthropic)
│   │   │   ├── reranker.py       # Cross-encoder reranking
│   │   │   └── retrieval.py      # BM25 + dense + RRF + rerank pipeline
│   │   ├── config.py             # All config via pydantic-settings + .env
│   │   ├── database.py           # Async SQLAlchemy engine and session
│   │   └── main.py               # FastAPI app + CORS
│   ├── eval/
│   │   ├── gold_qa.json          # 30 gold Q&A pairs with expected URLs and key facts
│   │   ├── retrieval_eval.py     # Recall@5, MRR, average rank
│   │   └── answer_eval.py        # LLM-as-judge faithfulness scoring
│   ├── fixtures/
│   │   ├── citizens_information.json   # 15 Citizens Information documents
│   │   └── revenue_ie.json             # 5 Revenue.ie documents
│   ├── migrations/               # Alembic migration files
│   ├── scripts/
│   │   ├── seed.py               # Load fixtures into the database
│   │   └── ingest.py             # Live web crawler (optional)
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx          # Landing page with example questions
│       │   └── chat/page.tsx     # Chat UI — streaming tokens + citation chips
│       ├── components/
│       │   ├── ChatMessage.tsx   # Message bubbles + citation links
│       │   └── ChatInput.tsx     # Text input + send button
│       └── lib/api.ts            # SSE streaming client
├── .github/
│   └── workflows/
│       └── eval.yml              # CI: retrieval eval on PR, answer eval on main push
├── docker-compose.yml            # Local dev: Postgres + Redis in Docker
├── Makefile                      # Shortcuts for common dev commands
└── .env.example                  # Template — copy to backend/.env and fill in keys
```

---

## Running Locally

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 18+
- A free NVIDIA API key — get one at [build.nvidia.com](https://build.nvidia.com)

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

Loads all 20 documents. First run downloads the 134 MB embedding model — takes about 30 seconds. Subsequent runs are instant (idempotent).

### 5. Start the backend

```bash
make backend
# API running at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### 6. Start the frontend

```bash
make frontend
# UI at http://localhost:3000
```

---

## API Reference

### `POST /v1/chat/messages`

Streams a grounded answer as Server-Sent Events.

**Request:**
```json
{ "message": "How do I apply for a medical card?" }
```

**Response stream:**
```
event: meta
data: {"retrieved_count": 5}

event: token
data: {"text": "To apply"}

event: token
data: {"text": " for a medical card..."}

event: citations
data: {"citations": [{"n": 1, "title": "Medical Card", "url": "https://...", "snippet": "..."}]}

event: done
data: {"message": "Stream complete"}
```

### `GET /v1/health`

```json
{"status": "ok", "database": "connected"}
```

---

## Configuration

Copy `.env.example` to `backend/.env` and fill in your values. Never commit `backend/.env` — it contains secrets.

### Database

| Variable | Example | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/db` | Used by FastAPI at runtime. Must use the `asyncpg` driver prefix. |
| `DATABASE_SYNC_URL` | `postgresql://user:pass@host:5432/db` | Used by Alembic for migrations only. Same host/credentials, no `+asyncpg`. |
| `REDIS_URL` | `redis://localhost:6379` | Use `rediss://` (double-s) for TLS connections like Upstash. |

Both database URLs are required. They point to the same database — the difference is just the driver prefix.

### LLM

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `nvidia` | `nvidia` to use NVIDIA NIM (free), or `anthropic` to use Claude. |
| `NVIDIA_API_KEY` | — | Required when `LLM_PROVIDER=nvidia`. Get a free key at [build.nvidia.com](https://build.nvidia.com). |
| `NVIDIA_MODEL` | `meta/llama-3.3-70b-instruct` | Best quality on the free tier. Higher latency on first request (~30s cold start). |
| `ANTHROPIC_API_KEY` | — | Required when `LLM_PROVIDER=anthropic`. Get a key at [console.anthropic.com](https://console.anthropic.com). |

### Embeddings & Reranking

| Variable | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | 134 MB, 384-dim, runs on CPU. Downloads automatically on first run. For better quality you can use `BAAI/bge-m3` (1024-dim) but update `EMBEDDING_DIM` too. |
| `EMBEDDING_DIM` | `384` | Must match the model above. If you change the model, change this too or pgvector will reject inserts. |
| `RERANKER_MODEL` | `BAAI/bge-reranker-base` | Cross-encoder that re-ranks candidates after RRF fusion. ~1.1 GB, runs on CPU. |
| `RERANKER_ENABLED` | `true` | Set to `false` to skip reranking and go straight from RRF to the LLM. Useful if you're low on RAM. |

### Retrieval tuning

| Variable | Default | Description |
|---|---|---|
| `BM25_TOP_K` | `20` | How many candidates BM25 returns before RRF fusion. |
| `DENSE_TOP_K` | `20` | How many candidates the vector search returns before RRF fusion. |
| `FINAL_TOP_K` | `5` | How many chunks (after reranking) are sent to the LLM as context. |

The pipeline is: BM25 (top 20) + Dense (top 20) → RRF merge → Reranker → top 5 to LLM.

### App

| Variable | Default | Description |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated list of origins allowed to call the API. In production, set this to your frontend URL. |
| `DEBUG` | `false` | Enables verbose logging. Don't set this in production. |

---

## Eval Results (v0.3)

Run against 30 gold Q&A pairs covering all 20 documents.

| Metric | Score |
|---|---|
| Recall@5 | **100%** — the right document appeared in the top 5 for every single question |
| Average rank | **1.0** — the right document was ranked #1 on average |
| Faithfulness | **0.93 / 1.0** — answers stayed grounded in the retrieved context |

---

## Terms & Privacy

**Not legal or professional advice.** All answers are informational summaries of publicly available official guidance. Nothing here constitutes legal, tax, immigration, or financial advice. Always verify with the relevant authority or consult a qualified professional before acting on any information.

**How queries are processed.** When a user sends a question, it is transmitted to NVIDIA's AI inference API (Llama 3.3 70B, US-based) to generate a response. This service does not log, store, or retain user queries. See [NVIDIA's privacy policy](https://www.nvidia.com/en-us/about-nvidia/privacy-policy/) for how they handle inference requests.

**Do not include personal information** in queries — no PPS numbers, addresses, passport numbers, or financial account details.

**Official sources:**
- [citizensinformation.ie](https://www.citizensinformation.ie)
- [revenue.ie](https://www.revenue.ie)
- [gov.ie](https://www.gov.ie)
- [irishimmigration.ie](https://www.irishimmigration.ie)
- [rtb.ie](https://www.rtb.ie)
- [workplacerelations.ie](https://www.workplacerelations.ie)

The knowledge base was last crawled in June 2026. Government policies change — always verify with the official source before acting on anything.

---

## License

[Apache 2.0](LICENSE)

---

## Contributing

Issues and PRs welcome. If you want to add more documents to the knowledge base, add them to `backend/fixtures/` in the same JSON format as the existing files and run `make seed`.
