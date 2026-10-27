# The notes API as an image: pinned base, hash-pinned dependencies, a non-root user, a health check, graceful shutdown by gunicorn.
FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .

RUN useradd --system --uid 10001 --no-create-home app
USER app

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD ["notes-api-health"]
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "30", "--graceful-timeout", "20", "notes_evidence.interfaces.wsgi:app"]
