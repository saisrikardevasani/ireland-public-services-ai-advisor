.PHONY: help db-up db-down migrate ingest backend frontend eval-retrieval eval-answers eval

help:
	@echo "Dev commands:"
	@echo "  make db-up            Start Postgres + Redis in Docker"
	@echo "  make db-down          Stop and remove containers"
	@echo "  make migrate          Apply database migrations"
	@echo "  make seed             Load fixture documents (fast, no crawling)"
	@echo "  make ingest           Crawl Citizens Information live (slow)"
	@echo "  make backend          Start the FastAPI backend (hot reload)"
	@echo "  make frontend         Start the Next.js frontend (hot reload)"
	@echo ""
	@echo "Eval commands (Week 2):"
	@echo "  make eval-retrieval   Recall@5 across 30 gold questions (fast, no LLM)"
	@echo "  make eval-answers     Faithfulness eval via LLM-as-judge (calls NVIDIA API)"
	@echo "  make eval             Run both evals"

db-up:
	docker-compose up -d postgres redis
	@echo "Waiting for Postgres to be ready..."
	@until docker-compose exec postgres pg_isready -U advisor -d advisor; do sleep 1; done
	@echo "Postgres is ready."

db-down:
	docker-compose down

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && .venv/bin/python scripts/seed.py

# Seed the production Supabase database.
# Usage: DATABASE_URL="postgresql+asyncpg://..." DATABASE_SYNC_URL="postgresql://..." make seed-prod
seed-prod:
	cd backend && DATABASE_URL=$(DATABASE_URL) DATABASE_SYNC_URL=$(DATABASE_SYNC_URL) .venv/bin/python scripts/seed.py

# Live crawl — requires bot protection bypass or approved access
ingest:
	cd backend && .venv/bin/python scripts/ingest.py --max-pages 50

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

# ── Eval (Week 2) ─────────────────────────────────────────────────────────────

eval-retrieval:
	cd backend && .venv/bin/python eval/retrieval_eval.py --k 5 --fail-below 0.80

eval-answers:
	cd backend && .venv/bin/python eval/answer_eval.py --fail-below 0.70

eval: eval-retrieval eval-answers
