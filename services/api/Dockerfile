FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pyproject.toml alembic.ini ./
COPY src ./src
COPY ml_training ./ml_training
COPY alembic ./alembic
COPY scripts/entrypoint.sh ./scripts/entrypoint.sh
RUN pip install --no-cache-dir --no-deps . \
 && useradd --system --uid 10001 lunaris && chmod +x scripts/entrypoint.sh
USER lunaris
EXPOSE 8000
ENTRYPOINT ["./scripts/entrypoint.sh"]
