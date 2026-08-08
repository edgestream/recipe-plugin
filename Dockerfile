# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    RECIPE_MCP_HOST=0.0.0.0 \
    RECIPE_MCP_PORT=8001

WORKDIR /app

RUN addgroup --system recipe && adduser --system --ingroup recipe recipe

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir . && chown -R recipe:recipe /app

USER recipe

EXPOSE 8001

CMD ["recipe-mcp"]
