# Stage 1: Base image with Python requirements
FROM python:3.14-slim-trixie AS base


# Add image labels for metadata
LABEL org.opencontainers.image.title="Mealie Recipe Translator"
LABEL org.opencontainers.image.description="A Python application that translates Mealie recipes using OpenAI's ChatGPT API"
LABEL org.opencontainers.image.vendor="Oliver Lipkau"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.url="https://github.com/lipkau/mealie_translate"
LABEL org.opencontainers.image.source="https://github.com/lipkau/mealie_translate"
LABEL org.opencontainers.image.documentation="https://github.com/lipkau/mealie_translate#readme"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONPATH=/app \
  PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
  --no-install-recommends \
  build-essential \
  curl \
  cron \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
  && mkdir -p /app \
  && chown -R app:app /app

WORKDIR /app

# Copy entry script first
COPY scripts/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy project files for dependency installation
COPY --chown=app:app pyproject.toml ./
COPY --chown=app:app mealie_translate/ ./mealie_translate/
COPY --chown=app:app main.py ./

# Stage 2: Development image with dev dependencies
FROM base AS development

# Switch to app user
USER app
ENV PATH=$PATH:/home/app/.local/bin

# Install development dependencies with pip cache for faster rebuilds
RUN --mount=type=cache,target=/home/app/.cache/pip,uid=1000,gid=1000 \
  pip install -e .[dev]

# Copy remaining files (like tests, docs, etc.)
COPY --chown=app:app . ./

# Stay as app user for development (no cron needed)
# USER root - not needed for development

# Expose port for development server (if you add one later)
# EXPOSE 8000

# Development command - for dev, just run once by default
CMD ["python", "main.py"]

# Stage 3: Production image (lightweight)
FROM base AS production

# Install production dependencies with pip cache for faster rebuilds
RUN --mount=type=cache,target=/root/.cache/pip \
  pip install .

# Health check verifies configuration is valid (required env vars are set)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from mealie_translate.config import get_settings; s=get_settings(); assert s.mealie_base_url and s.mealie_api_token and s.openai_api_key, 'Missing required config'" || exit 1

# Production command - use our entry script for cron scheduling
CMD ["/usr/local/bin/docker-entrypoint.sh"]

# Stage 4: Testing image for CI/CD
FROM development AS testing

# Switch to app user to match development environment
USER app

# Run tests directly
RUN python -m pytest tests/ -m "not integration" -q

# Default to production stage
FROM production
