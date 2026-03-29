# Stage 1: Base image with Python requirements
FROM python:3.14-slim-trixie AS base


# Add image labels for metadata
LABEL org.opencontainers.image.title="Mealie Recipe Translator"
LABEL org.opencontainers.image.description="Translates Mealie recipes using LLMs and converts imperial units to metric"
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

# Stage 2: Runtime image (the only published image)
FROM base AS runtime

RUN --mount=type=cache,target=/root/.cache/pip \
  pip install .

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from mealie_translate.config import get_settings; s=get_settings(); assert s.mealie_base_url and s.mealie_api_token and s.openai_api_key, 'Missing required config'" || exit 1

CMD ["/usr/local/bin/docker-entrypoint.sh"]

# Stage 3: Testing image for CI (never published)
FROM runtime AS testing

COPY --chown=app:app . ./
RUN --mount=type=cache,target=/root/.cache/pip \
  pip install .[dev]

RUN python -m pytest tests/ -m "not integration" -q

# Default to runtime stage
FROM runtime
