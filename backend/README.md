---
title: EU Ireland Public Services AI Advisor
emoji: 🏛️
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# Ireland Public Services AI Advisor — Backend

FastAPI backend for the Ireland Public Services AI Advisor. Provides a RAG (Retrieval-Augmented Generation) API over 1,640 official Irish government documents from Citizens Information, Revenue, DSP, RTB, WRC, and HSE.

**Frontend:** https://irish-public-services-ai-advisor.vercel.app  
**API docs:** https://srikarcod3r-eu-ireland-advisor.hf.space/docs  
**Health:** https://srikarcod3r-eu-ireland-advisor.hf.space/v1/health

## Stack

- FastAPI + SSE streaming
- BM25 (Postgres tsvector) + dense vector search (pgvector HNSW) fused with RRF
- Cross-encoder reranker (BAAI/bge-reranker-base)
- Llama 3.3 70B via NVIDIA NIM
- Supabase (Postgres + pgvector)
- Redis (Upstash) for query cache and rate limiting
