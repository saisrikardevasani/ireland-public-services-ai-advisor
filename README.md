---
title: EU Ireland Public Services AI Advisor
emoji: 🏛️
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# Ireland Public Services AI Advisor

A production RAG chatbot for Irish public services. Ask about tax, immigration, benefits, housing, employment, or healthcare. Get an answer grounded in and cited from official government pages.

**Live:** https://irish-public-services-ai-advisor.vercel.app  
**API docs:** https://srikarcod3r-eu-ireland-advisor.hf.space/docs

The backend runs on Hugging Face Spaces free tier and sleeps after ~15 minutes of inactivity. The chat page pings `/health` on load, so it's usually warm by the time you type. If it isn't, an amber banner appears and it wakes in ~30s.

Health check: https://srikarcod3r-eu-ireland-advisor.hf.space/v1/health → `{"status":"ok","database":"connected"}`


## How the pipeline works

When you send a question, this is the actual sequence:

1. Your question is embedded into a 384-dimensional vector using BAAI/bge-small-en-v1.5. This runs in-container on CPU with no external embedding API.
2. Two searches run in parallel against 1,640 official Irish government documents: BM25 over Postgres `tsvector` (keyword match) and dense search over a `pgvector` HNSW index (cosine similarity). Each returns the top 20 candidates.
3. Both result lists get merged with Reciprocal Rank Fusion: `score = Σ 1/(60 + rank)`. Documents appearing in both lists accumulate score from each, effectively boosting them. No hyperparameters to tune.
4. A cross-encoder reranker (BAAI/bge-reranker-base) reads each `(query, passage)` pair jointly and picks the top 5. This matters because bi-encoder vector similarity can't model the interaction between query and passage; the cross-encoder can.
5. Llama 3.3 70B via NVIDIA's free NIM API streams a grounded answer token-by-token. The system prompt explicitly instructs it to answer only from the retrieved passages. If the answer isn't in the documents, it says so.
6. Citation chips are returned alongside the stream, each linking to the exact government page with the crawl date so you know how fresh the source is.

Repeated questions hit Redis first (SHA-256 keyed, 6-hour TTL). Same question twice costs one cache lookup: no database, no embedding, no NVIDIA call.

Multi-turn sessions keep the last 3 exchanges in memory (30-min TTL, UUID per browser tab).

```
question
   │
   ▼
[bge-small-en-v1.5]  →  384-dim embedding
   │
   ├──────────────────────────────────┐
   ▼                                  ▼
[BM25 / Postgres tsvector]    [pgvector HNSW index]
  top 20, keyword match          top 20, cosine sim
   │                                  │
   └───────────────┬──────────────────┘
                   ▼
              [RRF fusion]
              score = Σ 1/(60 + rank)
              top 20 merged
                   │
                   ▼
       [bge-reranker-base]
       cross-encoder: reads (query, chunk) jointly
       top 5 parent chunks selected
                   │
                   ▼
        [Llama 3.3 70B / NVIDIA NIM]
        streams answer + [n] citation markers
                   │
                   ▼
         [SSE → Next.js frontend]
```


## Chunking strategy

Each document produces two chunk sizes. The small chunk (128 words) is what gets searched. Smaller chunks mean more precise BM25 and vector matching. When a chunk makes it through to the reranker, the full parent chunk (512 words) is what gets sent to the LLM, giving it enough surrounding context to answer properly.

This avoids the classic tradeoff between retrieval precision (wants small chunks) and answer context (wants large chunks). You get both.


## The knowledge base

1,640 official documents, 16,326 vector chunks, six Irish government sources:

| Source | Coverage |
|---|---|
| Citizens Information | Immigration, tax, welfare, healthcare, housing, employment |
| Revenue.ie | PAYE, VAT, CGT, income tax, credits, returns |
| Gov.ie / DSP | All social protection benefits and schemes |
| RTB | Landlord/tenant rights and disputes |
| WRC | Employment rights and complaints |
| HSE | Healthcare entitlements and services |

Re-crawled every Sunday at 02:00 UTC via GitHub Actions. The pipeline deduplicates by content hash, so only changed pages re-embed. Manual trigger available with `--source` and `--max-pages` flags.


## Versions

**v0.1:** Core pipeline. FastAPI backend, hybrid BM25 + dense retrieval, RRF fusion, streaming Next.js frontend. 15 Citizens Information documents. NVIDIA free API for LLM.

**v0.2:** Eval harness. 30 gold Q&A pairs (2 per document), automated Recall@5 and MRR scoring, LLM-as-judge faithfulness eval, GitHub Actions CI. Every PR gates on retrieval metrics. Results: 100% Recall@5, avg rank 1.0, faithfulness 0.93/1.0.

**v0.3:** Better retrieval. Hierarchical chunking (128-word child for search, 512-word parent for context). HNSW vector index. Cross-encoder reranker added after RRF fusion. Revenue.ie added as a second source.

**v0.4:** Deployed. Full free stack: Hugging Face Spaces (Docker, 2 vCPU, 16 GB RAM), Vercel, Supabase EU West, Upstash EU West. Total cost: $0/month.

**v0.5:** Scale. Knowledge base went from 20 → 1,640 documents across six sources. 16,326 chunks indexed. Multi-source async crawler with per-site URL filters and sitemap support. LLM upgraded from Llama 3.1 8B → Llama 3.3 70B. The quality difference is significant.

**v0.6:** Production hardening. This is the pass where everything that "works in development" got made into something you'd hand to a real user.

The frontend was showing raw `**asterisks**` instead of rendered markdown, fixed with `react-markdown` and `@tailwindcss/typography`. Added a copy button, shareable links (copies `/chat?q=...` to clipboard), source freshness dates on citation chips, a proper "New conversation" button, and thumbs up/down feedback (the question is SHA-256 hashed client-side before submission so the raw text never reaches the feedback endpoint). Built a full GDPR Article 13 privacy notice at `/privacy`.

On the backend: the dense vector search was building its query with f-string interpolation. That's a SQL injection pattern. Fixed to use a bound parameter (`CAST(:vec AS vector)`). Daily rate limiting added on top of the per-minute burst cap: 20 requests/day per IP stored in Redis, so it survives backend restarts and protects the NVIDIA quota. Redis query cache added (6-hour TTL). The `crawled_at` timestamp surfaced through the retrieval pipeline to the frontend.

Supabase sent a CRITICAL security alert: all four tables were publicly accessible via PostgREST because Row Level Security wasn't enabled. Enabled RLS on `alembic_version`, `documents`, `chunks`, and `feedback`. Moved pg_trgm from the public schema to extensions while we were at it.

28 unit tests added across the chunker, RRF fusion, and pipeline hash logic.


## Stack

| Layer | Technology | Cost |
|---|---|---|
| Frontend | Next.js 16, Tailwind CSS, react-markdown | Free (Vercel) |
| Backend | FastAPI, Python 3.11 | Free (Hugging Face Spaces) |
| Database | PostgreSQL 16, pgvector | Free (Supabase EU West) |
| Cache + rate limits | Redis serverless | Free (Upstash EU West) |
| Embeddings | BAAI/bge-small-en-v1.5 (384-dim, CPU) | Free (in-container) |
| Reranker | BAAI/bge-reranker-base (cross-encoder, CPU) | Free (in-container) |
| LLM | Llama 3.3 70B via NVIDIA NIM | Free tier |
| Migrations | Alembic | — |

$0/month total.


## Running locally

You need Docker Desktop, Python 3.11+, Node.js 18+, and a free NVIDIA API key from [build.nvidia.com](https://build.nvidia.com).

```bash
git clone https://github.com/saisrikardevasani/ireland-public-services-ai-advisor.git
cd ireland-public-services-ai-advisor
cp .env.example backend/.env
# open backend/.env and paste your NVIDIA_API_KEY
```

Start Postgres 16 (with pgvector) and Redis in Docker:
```bash
make db-up
```

Run migrations, then seed:
```bash
make migrate
make seed
```

First seed downloads the 134 MB embedding model (~30s). Subsequent runs are fast; the pipeline deduplicates by content hash so only changed pages re-embed.

Start the backend on http://localhost:8000:
```bash
make backend
# interactive docs at http://localhost:8000/docs
```

Start the frontend on http://localhost:3000:
```bash
make frontend
```


## API

### POST /v1/chat/messages

Rate-limited to 10 requests/minute and 20 requests/day per IP. Returns a Server-Sent Events stream.

```json
{
  "message": "How do I apply for a medical card?",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

`conversation_id` is optional. Provide one (generate with `crypto.randomUUID()`) to get multi-turn context; the last 3 exchanges from that session are included as history. Omit it for stateless requests.

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

### POST /v1/feedback

```json
{"question_hash": "a3f2c1...", "rating": 1}
```

`rating` is `1` (helpful) or `-1` (not helpful). The question is hashed with SHA-256 on the client before submission. No raw query text is stored anywhere. Returns 204.

### GET /v1/health

```json
{"status": "ok", "database": "connected"}
```


## Configuration

Copy `.env.example` to `backend/.env`. Never commit `backend/.env`.

**Database**

| Variable | Example | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/db` | Runtime async queries. Must use `asyncpg` driver prefix. |
| `DATABASE_SYNC_URL` | `postgresql://user:pass@host:5432/db` | Alembic migrations only. Same host, no `+asyncpg`. |
| `REDIS_URL` | `redis://localhost:6379` | Use `rediss://` (double-s) for Upstash TLS. |

**LLM**

| Variable | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `nvidia` | `nvidia` (free tier) or `anthropic` |
| `NVIDIA_API_KEY` | — | Required when provider is nvidia. Free at build.nvidia.com. |
| `NVIDIA_MODEL` | `meta/llama-3.3-70b-instruct` | Best quality on the free tier |
| `ANTHROPIC_API_KEY` | — | Required when provider is anthropic |

**Embeddings and reranking**

| Variable | Default | Notes |
|---|---|---|
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | 134 MB, 384-dim, CPU. Downloads automatically on first run. |
| `EMBEDDING_DIM` | `384` | Must match the model. Changing this means rebuilding the HNSW index. |
| `RERANKER_MODEL` | `BAAI/bge-reranker-base` | ~1.1 GB, CPU. |
| `RERANKER_ENABLED` | `true` | Set `false` if RAM-constrained (retrieval quality degrades). |

**Retrieval tuning**

| Variable | Default | Notes |
|---|---|---|
| `BM25_TOP_K` | `20` | Candidates from keyword search before RRF |
| `DENSE_TOP_K` | `20` | Candidates from vector search before RRF |
| `FINAL_TOP_K` | `5` | Chunks sent to LLM after reranking |

Full pipeline: BM25 (20) + Dense (20) → RRF merge → cross-encoder → top 5 → LLM.

**App**

| Variable | Default | Notes |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated. Set to your Vercel URL in production. |
| `DEBUG` | `false` | Verbose logging. Don't enable in production. |


## Eval results

Run against 30 gold Q&A pairs covering all seed documents (v0.2 eval harness):

| Metric | Score | What it means |
|---|---|---|
| Recall@5 | 100% | Right document appeared in the top 5 for every single question |
| Average rank | 1.0 | Right document ranked #1 on average, not buried at #3 or #5 |
| Faithfulness | 0.93/1.0 | LLM-as-judge scored answers as grounded in retrieved context |

Run it yourself:
```bash
cd backend && .venv/bin/python eval/retrieval_eval.py
```


## Tests

28 unit tests, all passing:

```bash
cd backend && .venv/bin/python -m pytest tests/unit/ -v
```

| File | Tests | What's covered |
|---|---|---|
| test_chunker.py | 11 | Child ≤128 words, parent ≤512 words, parent contains child text, sequential indices, min-length guard |
| test_retrieval.py | 9 | RRF with empty inputs, single-source lists, final_k cap, shared-doc score boosting, metadata propagation |
| test_pipeline.py | 8 | SHA-256 hash determinism, 64-char hex output, whitespace sensitivity, provided-hash vs computed-hash paths |


## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py           # POST /v1/chat/messages: SSE streaming, rate-limited
│   │   │   ├── feedback.py       # POST /v1/feedback: stores hash+rating, no raw text
│   │   │   └── health.py         # GET /v1/health
│   │   ├── ingestion/
│   │   │   ├── chunker.py        # Hierarchical chunking (128-word child, 512-word parent)
│   │   │   ├── pipeline.py       # Ingest orchestrator: idempotent, content-hash deduped
│   │   │   ├── sources.py        # Per-source crawl config (URL filters, sitemaps)
│   │   │   └── web_crawler.py    # Multi-source async crawler
│   │   ├── models/
│   │   │   └── schema.py         # SQLAlchemy ORM: Document, Chunk, Feedback tables
│   │   ├── pipeline/
│   │   │   ├── generator.py      # LLM generation + conversation history
│   │   │   ├── reranker.py       # Cross-encoder reranking
│   │   │   └── retrieval.py      # BM25 + dense + RRF + crawled_at timestamp
│   │   ├── cache.py              # Redis cache (6h TTL, SHA-256 key, no PII)
│   │   ├── session.py            # In-memory sessions (30min TTL, max 3 turns)
│   │   ├── config.py             # pydantic-settings + .env
│   │   ├── database.py           # Async SQLAlchemy engine
│   │   └── main.py               # FastAPI app, CORS, rate limiting, routers
│   ├── eval/
│   │   ├── gold_qa.json          # 30 gold Q&A pairs with expected URLs and key facts
│   │   ├── retrieval_eval.py     # Recall@5, MRR, average rank
│   │   └── answer_eval.py        # LLM-as-judge faithfulness scoring
│   ├── fixtures/                  # Seed data (JSON, one file per source)
│   ├── migrations/versions/       # Alembic migrations 001–005
│   ├── scripts/
│   │   ├── seed.py               # Load fixtures into the database
│   │   └── ingest.py             # Live multi-source web crawler
│   └── tests/unit/               # 28 unit tests
├── frontend/src/
│   ├── app/
│   │   ├── page.tsx              # Landing page
│   │   ├── chat/page.tsx         # Chat UI: streaming, multi-turn, feedback, share
│   │   └── privacy/page.tsx      # GDPR Article 13 Privacy Notice
│   ├── components/
│   │   ├── ChatMessage.tsx       # Bubbles, markdown rendering, copy, share, feedback, citations
│   │   └── ChatInput.tsx         # Text input + send button
│   ├── lib/api.ts                # SSE streaming client (passes conversation_id)
│   └── types/index.ts            # Message, Citation interfaces
├── .github/workflows/
│   ├── eval.yml                  # CI: retrieval eval on PR, answer eval on main
│   └── recrawl.yml               # Weekly re-crawl, Sundays 02:00 UTC
├── docker-compose.yml            # Local dev: Postgres + Redis
├── Makefile                      # Common dev commands
└── .env.example                  # Template: copy to backend/.env
```


## Privacy

Nothing here is legal advice. All answers are informational summaries of publicly available official guidance. Always verify with the relevant authority or consult a qualified professional before acting on anything.

User questions are transmitted to NVIDIA's inference API to generate responses. This service doesn't store raw question text anywhere. Feedback ratings are stored as SHA-256 hashes only; the original question text can't be recovered from them. Full [Privacy Notice](https://irish-public-services-ai-advisor.vercel.app/privacy) (GDPR Art. 13).

Don't include personal information in questions. No PPS numbers, addresses, financial details, or health information.

Official sources: [citizensinformation.ie](https://www.citizensinformation.ie) · [revenue.ie](https://www.revenue.ie) · [gov.ie/DSP](https://www.gov.ie/en/organisation/department-of-social-protection/) · [rtb.ie](https://www.rtb.ie) · [workplacerelations.ie](https://www.workplacerelations.ie) · [hse.ie](https://www.hse.ie)


## Contributing

Issues and PRs welcome. To add documents to the knowledge base, add them to `backend/fixtures/` in the same JSON format as existing files and run `make seed`. The pipeline deduplicates by content hash so running it multiple times is safe.


## License

[Apache 2.0](LICENSE)
