# EU & Ireland Public Services AI Advisor

A production-grade RAG (Retrieval-Augmented Generation) chatbot that answers questions about Irish public services — immigration, tax, health, housing, and employment — with **cited, grounded answers** linked to official government sources.

> Built as a 4-week learning project: build a real product, learn the engineering behind it.

**Live demo:**
- Frontend: https://eu-and-ireland-public-services-ai-a.vercel.app
- Backend API: https://srikarcod3r-eu-ireland-advisor.hf.space/v1/health

---

## What It Does

Ask a question like *"When can I switch from Stamp 2 to Stamp 1G?"* and the system:

1. Embeds your question into a 384-dimensional vector
2. Runs **hybrid retrieval** — BM25 full-text search + dense cosine similarity — sequentially
3. Fuses results with **Reciprocal Rank Fusion (RRF)** to get 20 candidates
4. **Cross-encoder reranks** all 20 with BAAI/bge-reranker-base to find the best 5
5. Streams a grounded answer from **Llama 3.1** (via NVIDIA free API) token-by-token
6. Returns clickable citation chips linking every claim to its source

Every factual claim is cited. The model is instructed never to answer outside the retrieved context.

---

## Architecture (v0.3)

```
User question
     │
     ▼
[Query Embedder]  ←── BAAI/bge-small-en-v1.5 (384-dim)
     │
     ├──────────────────────────────────────┐
     ▼                                      ▼
[BM25 Search]                        [Dense Search]
Postgres tsvector + ts_rank_cd       pgvector cosine (HNSW)
top 20 candidates                    top 20 candidates
     │                                      │
     └──────────────┬───────────────────────┘
                    ▼
            [RRF Fusion]
            score = Σ 1/(60 + rank)
            pool of 20 candidates
                    │
                    ▼
       [Cross-Encoder Reranker]
       BAAI/bge-reranker-base
       reads (query, passage) pairs
       top 5 chunks — parent window
                    │
                    ▼
         [Llama 3.1 via NVIDIA API]
         Streams tokens with [n] citations
                    │
                    ▼
         [SSE stream → Next.js UI]
```

### Tech Stack

| Layer | Technology |
|---|---|
| **API** | FastAPI + Server-Sent Events (SSE) |
| **Database** | PostgreSQL 16 + pgvector (Supabase) |
| **Full-text search** | Postgres `tsvector` / `ts_rank_cd` |
| **Vector search** | pgvector cosine similarity + HNSW index |
| **Embeddings** | `BAAI/bge-small-en-v1.5` via sentence-transformers |
| **Reranker** | `BAAI/bge-reranker-base` cross-encoder |
| **LLM** | `meta/llama-3.1-8b-instruct` via NVIDIA NIM (free tier) |
| **Frontend** | Next.js 16 + Tailwind CSS |
| **Cache** | Upstash Redis (serverless) |
| **Backend hosting** | Hugging Face Spaces (free, Docker) |
| **Frontend hosting** | Vercel (free) |
| **Migrations** | Alembic |

---

## Versions

### v0.1 — Hybrid RAG pipeline
- FastAPI backend with BM25 + dense vector retrieval
- RRF fusion, streaming SSE endpoint
- Next.js chat UI with citation chips
- 15 Citizens Information seed documents

### v0.2 — Eval harness
- 30 gold Q&A pairs across all documents
- Retrieval eval: Recall@5, MRR, avg rank
- Answer eval: LLM-as-judge faithfulness scoring
- GitHub Actions CI: retrieval gates on every PR
- **Results: 100% Recall@5, avg rank 1.0, faithfulness 0.93**

### v0.3 — Hierarchical chunking + reranking
- Child chunks (128 words) embedded for precision; parent chunks (512 words) sent to LLM
- HNSW vector index for faster approximate nearest-neighbour search
- Cross-encoder reranker (BAAI/bge-reranker-base) after RRF fusion
- Revenue.ie added as second source (PAYE, CGT, Rent Tax Credit, Flat Rate Expenses)
- **20 documents, 63 chunks total**

### v0.4 — Free cloud deployment
- Backend: Hugging Face Spaces (Docker, 2 vCPU / 16 GB RAM, free)
- Frontend: Vercel (free)
- Database: Supabase PostgreSQL + pgvector (free tier)
- Cache: Upstash Redis serverless (free tier)
- **$0/month total hosting cost**

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py          # POST /v1/chat/messages — SSE streaming
│   │   │   └── health.py        # GET /v1/health
│   │   ├── ingestion/
│   │   │   ├── chunker.py       # Hierarchical chunking (child + parent windows)
│   │   │   ├── crawler.py       # Citizens Information web crawler
│   │   │   ├── embedder.py      # Sentence-transformer embedding
│   │   │   └── pipeline.py      # Ingest orchestrator (idempotent)
│   │   ├── models/
│   │   │   └── schema.py        # SQLAlchemy ORM: Document + Chunk
│   │   ├── pipeline/
│   │   │   ├── generator.py     # LLM answer generation (NVIDIA / Anthropic)
│   │   │   ├── reranker.py      # Cross-encoder reranking (BAAI/bge-reranker-base)
│   │   │   └── retrieval.py     # Hybrid BM25 + dense + RRF + rerank
│   │   ├── config.py            # pydantic-settings config from .env
│   │   ├── database.py          # Async SQLAlchemy engine + session
│   │   └── main.py              # FastAPI app factory
│   ├── eval/
│   │   ├── gold_qa.json         # 30 gold Q&A pairs
│   │   ├── retrieval_eval.py    # Recall@5, MRR, avg rank
│   │   └── answer_eval.py       # LLM-as-judge faithfulness
│   ├── fixtures/
│   │   ├── citizens_information.json   # 15 Citizens Information documents
│   │   └── revenue_ie.json             # 5 Revenue.ie documents
│   ├── migrations/              # Alembic migrations
│   ├── scripts/
│   │   ├── seed.py              # Load fixtures into database
│   │   └── ingest.py            # Live crawler
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx         # Landing page
│       │   └── chat/page.tsx    # Chat UI (streaming + citations)
│       ├── components/
│       │   ├── ChatMessage.tsx  # Message bubbles + citation chips
│       │   └── ChatInput.tsx    # Input box
│       └── lib/api.ts           # SSE client
├── .github/
│   └── workflows/
│       └── eval.yml             # CI: retrieval eval on PR, answer eval on main
├── docker-compose.yml           # Local dev: Postgres + Redis
├── fly.toml                     # Fly.io config (unused — moved to HF Spaces)
├── Makefile
└── .env.example
```

---

## Quick Start (Local)

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 18+
- A free NVIDIA API key from [build.nvidia.com](https://build.nvidia.com)

### 1. Clone and configure

```bash
git clone https://github.com/saisrikardevasani/eu-ireland-public-services-ai-advisor.git
cd eu-ireland-public-services-ai-advisor

cp .env.example backend/.env
# Edit backend/.env — add your NVIDIA_API_KEY
```

### 2. Start the database

```bash
make db-up
```

Starts Postgres 16 (with pgvector) and Redis 7 in Docker.

### 3. Run migrations

```bash
make migrate
```

### 4. Seed the database

```bash
make seed
```

Loads 20 documents (15 Citizens Information + 5 Revenue.ie). First run downloads the 134 MB embedding model.

### 5. Start backend + frontend

```bash
make backend   # http://localhost:8000
make frontend  # http://localhost:3000
```

---

## Available Commands

```bash
make db-up      # Start Postgres + Redis in Docker
make db-down    # Stop and remove containers
make migrate    # Apply database migrations
make seed       # Load fixture documents
make ingest     # Crawl Citizens Information live
make backend    # Start FastAPI backend (hot reload)
make frontend   # Start Next.js frontend (hot reload)
```

---

## API Reference

### `POST /v1/chat/messages`

Streams an answer via Server-Sent Events.

**Request:**
```json
{ "message": "How do I apply for a medical card?" }
```

**Response stream (SSE):**
```
event: meta
data: {"retrieved_count": 5}

event: token
data: {"text": "To apply for a medical card..."}

event: citations
data: {"citations": [{"n": 1, "title": "Medical Card", "url": "...", "snippet": "..."}]}

event: done
data: {"message": "Stream complete"}
```

### `GET /v1/health`

Returns `{"status": "ok", "database": "connected"}`.

---

## How Retrieval Works

**BM25** (Postgres `tsvector`): tokenises and stems the query, ranks by term frequency. Best for exact terms like "Stamp 1G" or "USC rate".

**Dense** (pgvector HNSW): embeds query and chunks into 384-dim vectors, ranks by cosine similarity. Best for semantic matches — "switching visa" finds "changing immigration permission".

**RRF Fusion**: merges the two ranked lists with `score = Σ 1/(60 + rank)`. Documents appearing in both lists get boosted. Parameter-free.

**Cross-encoder reranker**: reads each `(query, passage)` pair together — far more accurate than cosine similarity, which encodes query and passage independently. The top 5 after reranking are sent to the LLM as parent-window chunks.

**Hierarchical chunking**: child chunks (128 words) are used for retrieval precision; when found, their parent chunk (512 words) is sent to the LLM for wider context.

---

## Sources Covered

**Citizens Information (15 documents)**
- Stamp 1G (Third Level Graduate Programme)
- Critical Skills Employment Permit
- IRP registration
- PPSN
- Medical Card and GP Visit Card
- USC (Universal Social Charge)
- Income Tax calculation
- PAYE Tax Credit
- Minimum Wage
- Jobseeker's Benefit and Allowance
- Child Benefit
- Tenants' Rights
- Opening a Bank Account
- Employment Permits overview

**Revenue.ie (5 documents)**
- What is PAYE?
- Rent Tax Credit
- Capital Gains Tax (CGT)
- Who Must File a Tax Return
- Flat Rate Expenses

---

## Configuration

All config is via environment variables in `backend/.env`. See `.env.example`.

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `nvidia` | `nvidia` or `anthropic` |
| `NVIDIA_MODEL` | `meta/llama-3.1-8b-instruct` | Any NVIDIA NIM model |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | sentence-transformers model |
| `RERANKER_MODEL` | `BAAI/bge-reranker-base` | Cross-encoder model |
| `RERANKER_ENABLED` | `true` | Toggle reranking |
| `BM25_TOP_K` | `20` | BM25 candidates before RRF |
| `DENSE_TOP_K` | `20` | Dense candidates before RRF |
| `FINAL_TOP_K` | `5` | Chunks passed to LLM |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |

---

## Eval Results (v0.3)

| Metric | Score |
|---|---|
| Recall@5 | **100%** (30/30 questions) |
| Average rank | **1.0** |
| LLM faithfulness | **0.93 / 1.0** |

---

## Disclaimer

This tool provides **informational guidance only**. It is not a substitute for professional legal, tax, or immigration advice. Always verify with official sources:

- [citizensinformation.ie](https://www.citizensinformation.ie)
- [revenue.ie](https://www.revenue.ie)
- [irishimmigration.ie](https://www.irishimmigration.ie)

---

## License

[Apache 2.0](LICENSE) — see licence terms for permitted use, modification, and distribution.

---

## Contributing

Pull requests welcome. Open an issue first for significant changes.
