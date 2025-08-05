# Docker Guide

Complete guide for containerizing, deploying, and using the Mealie Recipe Translator with Docker.

## Quick Start

### Using Pre-built Images (Recommended)

```bash
# Pull the latest image from GitHub Container Registry
docker pull ghcr.io/lipkau/mealie_translate:latest

# Create environment configuration
cp .env.example .env
# Edit .env with your API keys

# Run with docker-compose (recommended)
make docker-run

# Or run directly
docker run --rm --env-file .env ghcr.io/lipkau/mealie_translate:latest
```

### Building Locally

```bash
# Setup environment (if not done already)
make setup-env
# Edit .env with your API keys

# Build and run with docker-compose
make docker-build
make docker-run

# Or run in development mode (with volume mounts)
make docker-dev
```

## Docker Commands Reference

| Command             | Description                                  |
| ------------------- | -------------------------------------------- |
| `make docker-build` | Build Docker image locally                   |
| `make docker-run`   | Run production container with docker-compose |
| `make docker-dev`   | Run development container with volume mounts |
| `make docker-logs`  | Follow container logs                        |
| `make docker-test`  | Run tests in Docker container                |
| `make docker-clean` | Clean up Docker images and containers        |

## Available Images

The project automatically publishes Docker images to GitHub Container Registry (GHCR):

- **Registry**: `ghcr.io`
- **Repository**: `lipkau/mealie_translate`
- **Base URL**: `ghcr.io/lipkau/mealie_translate`

### Image Tags

| Tag      | Description                             | When Updated             |
| -------- | --------------------------------------- | ------------------------ |
| `latest` | Latest stable release from main branch  | Every push to main       |
| `dev`    | Development build with dev dependencies | Every push to main       |
| `v1.0.0` | Specific version tags                   | When git tags are pushed |
| `main`   | Latest commit on main branch            | Every push to main       |

### Pulling Images

```bash
# Production image
docker pull ghcr.io/lipkau/mealie_translate:latest

# Development image
docker pull ghcr.io/lipkau/mealie_translate:dev

# Specific version
docker pull ghcr.io/lipkau/mealie_translate:v1.0.0
```

## Automated Scheduling with Cron

The Docker container includes automatic scheduling functionality using cron for periodic recipe translation without manual
intervention.

### Configuration

Configure the schedule using the `CRON_SCHEDULE` environment variable in your `.env` file:

```env
# Run every 6 hours (default)
CRON_SCHEDULE=0 */6 * * *

# Run daily at 2 AM
CRON_SCHEDULE=0 2 * * *

# Run every 30 minutes
CRON_SCHEDULE=*/30 * * * *

# Run twice daily (6 AM and 6 PM)
CRON_SCHEDULE=0 6,18 * * *
```

### Cron Format

The cron schedule follows the standard 5-field format:

```text
minute hour day month weekday
```

Examples:

- `0 */6 * * *` - Every 6 hours
- `0 9 * * *` - Daily at 9 AM
- `0 9 * * 1` - Weekly on Monday at 9 AM
- `*/30 * * * *` - Every 30 minutes

### Production vs Development

- **Production** (`make docker-run`): Uses cron scheduling with configurable intervals
- **Development** (`make docker-dev`): Runs once for testing

## Docker Architecture

### Multi-Stage Build

The Dockerfile uses a multi-stage build process:

1. **Base Stage**: Python 3.13 with system dependencies
2. **Development Stage**: Includes dev dependencies and testing tools
3. **Production Stage**: Lightweight image with only runtime dependencies
4. **Testing Stage**: Runs tests during build (optional)

### Images Sizes

- **Production**: ~200MB (optimized)
- **Development**: ~300MB (includes dev tools)

### Security Features

- Non-root user execution
- Multi-layer optimization
- Dependency vulnerability scanning
- Minimal attack surface

## Usage Patterns

### One-time Translation

```bash
# Run translation once
docker run --rm --env-file .env ghcr.io/lipkau/mealie_translate:latest
```

### Scheduled Production Deployment

```bash
# Run with automatic scheduling (recommended)
make docker-run

# Follow logs to monitor execution
make docker-logs
```

### Development and Testing

```bash
# Development environment with volume mounts
make docker-dev

# Run tests in container
make docker-test
```

## Monitoring and Logs

### Container Logs

```bash
# Follow live logs
docker-compose logs -f mealie-translator

# View recent logs
docker-compose logs --tail=100 mealie-translator

# Using make command
make docker-logs
```

### Application Logs

- **Container**: Logs are written to `/var/log/mealie-translator.log` inside the container
- **Docker**: All output is captured by Docker logging system
- **Health Check**: Container health is monitored to ensure the application is working

### Log Behavior

1. **Startup**: The container runs the translation job immediately when started
2. **Scheduling**: Cron then runs the job according to the configured schedule
3. **Logging**: All output is logged and can be viewed via Docker logs
4. **Rotation**: Log rotation is handled by the container runtime

## Environment Configuration

### Required Environment Variables

```env
# Mealie API Configuration
MEALIE_BASE_URL=https://your-mealie-instance.com
MEALIE_API_TOKEN=your_mealie_api_token

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# Optional: Cron Schedule
CRON_SCHEDULE=0 */6 * * *

# Optional: Logging
LOG_LEVEL=INFO
```

### Docker Compose Configuration

The project includes `docker-compose.yml` with:

- Environment file loading (`.env`)
- Volume mounts for development
- Health checks
- Restart policies
- Network configuration

### Custom Configuration

Create `docker-compose.override.yml` for environment-specific settings:

```yaml
version: '3.8'
services:
  mealie-translator:
    environment:
      - CRON_SCHEDULE=0 */2 * * *  # Every 2 hours
      - LOG_LEVEL=DEBUG
```

## Publishing and Deployment

### Automatic Publishing

Images are automatically published to GHCR when:

1. **Push to main branch**: Creates `latest` and `main` tags
2. **Git tags**: Creates versioned tags (e.g., `v1.0.0`, `1.0`, `latest`)

### Manual Publishing

```bash
# Create a release
git tag v1.0.0
git push origin v1.0.0

# Build and push locally (if needed)
docker build -t ghcr.io/lipkau/mealie_translate:custom .
docker push ghcr.io/lipkau/mealie_translate:custom
```

### CI/CD Integration

The GitHub Actions workflow (`.github/workflows/cd.yml`) handles:

- ✅ Multi-stage builds (dev + production)
- ✅ Automatic tagging strategy
- ✅ Security scanning with Trivy
- ✅ GHCR authentication and publishing
- ✅ Build caching for faster deployments

## Troubleshooting

### Common Issues

**Container won't start**:

```bash
# Check logs
docker-compose logs mealie-translator

# Verify environment
docker run --rm --env-file .env ghcr.io/lipkau/mealie_translate:latest --check-config
```

**Cron not running**:

```bash
# Check cron logs
docker exec -it $(docker-compose ps -q mealie-translator) cat /var/log/cron.log

# Verify schedule
docker exec -it $(docker-compose ps -q mealie-translator) crontab -l
```

**Permission issues**:

```bash
# Check user
docker exec -it $(docker-compose ps -q mealie-translator) whoami

# Check file permissions
docker exec -it $(docker-compose ps -q mealie-translator) ls -la /app
```

### Performance Optimization

- Use multi-stage builds to minimize image size
- Leverage Docker layer caching
- Use `.dockerignore` to exclude unnecessary files
- Consider using Alpine-based images for smaller footprint

## Advanced Configuration

### Custom Dockerfile

For specialized deployments, you can extend the base image:

```dockerfile
FROM ghcr.io/lipkau/mealie_translate:latest

# Add custom configuration
COPY custom-config.json /app/config/
ENV CUSTOM_CONFIG_PATH=/app/config/custom-config.json

# Custom entrypoint
COPY custom-entrypoint.sh /app/
ENTRYPOINT ["/app/custom-entrypoint.sh"]
```

### Health Checks

The container includes health checks:

```dockerfile
HEALTHCHECK --interval=1h --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1
```

### Resource Limits

Configure resource limits in production:

```yaml
services:
  mealie-translator:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

## Migration from Local Installation

If migrating from a local installation:

1. **Export configuration**: Copy your `.env` file
2. **Stop local service**: Ensure no conflicts with ports
3. **Start container**: Use `make docker-run`
4. **Verify**: Check logs and test translation

The container setup preserves all functionality from local installations while adding scheduling and deployment benefits.
