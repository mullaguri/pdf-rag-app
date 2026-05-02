# ── Base image ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── System dependencies (needed for faiss-cpu, pypdf, sentence-transformers) 
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ────────────────────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ──────────────────────────────────────────────
# Copy requirements first (Docker layer caching — reinstall only if changed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application code ────────────────────────────────────────────────────
COPY . .

# ── Create volume mount point for FAISS index persistence ───────────────────
RUN mkdir -p /app/vectorstore/faiss_index

# ── Expose FastAPI port ──────────────────────────────────────────────────────
EXPOSE 8000

# ── Start the app ────────────────────────────────────────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]