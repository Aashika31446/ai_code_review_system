FROM python:3.11-slim
WORKDIR /app
# Install system deps (for psycopg2)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*
# Install ruff and bandit globally
RUN pip install ruff bandit
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy backend app
COPY . .
# Copy analyzer and AI engine (they're siblings)
COPY ../code-analyzer /code-analyzer
COPY ../ai-engine /ai-engine
ENV PYTHONPATH=/app:/code-analyzer:/ai-engine
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
