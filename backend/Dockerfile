FROM python:3.12-slim

WORKDIR /app

# Build context is the repo root (see docker-compose.yml). Contract ABIs
# ship inside the backend package as backend/sentinel/reputation/contract_abis.json,
# so no contracts/.build copy is needed at runtime.
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY backend/sentinel ./sentinel
COPY backend/alembic.ini ./

EXPOSE 8000
CMD ["uvicorn", "sentinel.main:app", "--host", "0.0.0.0", "--port", "8000"]
