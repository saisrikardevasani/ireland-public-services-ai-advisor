FROM python:3.11-slim

WORKDIR /app

# Install system deps for psycopg2 and sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Pre-download both models into the image so first-request latency is just CPU inference,
# not a 280MB download. Models are cached in /root/.cache/huggingface.
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('BAAI/bge-small-en-v1.5'); CrossEncoder('BAAI/bge-reranker-base')"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
