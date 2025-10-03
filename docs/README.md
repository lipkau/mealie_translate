# Documentation Index

[![CI](https://github.com/lipkau/mealie_translate/actions/workflows/ci.yml/badge.svg)](https://github.com/lipkau/mealie_translate/actions/workflows/ci.yml)
[![CD](https://github.com/lipkau/mealie_translate/actions/workflows/cd.yml/badge.svg)](https://github.com/lipkau/mealie_translate/actions/workflows/cd.yml)
[![Security](https://github.com/lipkau/mealie_translate/actions/workflows/security.yml/badge.svg)](https://github.com/lipkau/mealie_translate/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This directory contains all project documentation for the Mealie Recipe Translator.

## Core Documentation

- **[Getting Started](../README.md)** - Main project README with setup and usage instructions
- **[Development Guide](DEVELOPMENT.md)** - Comprehensive developer guide including tools, optimizations, and all 35+
  Makefile commands
- **[Docker Guide](DOCKER.md)** - Complete Docker containerization, deployment, scheduling, and registry guide

## Architecture & Security

- **[CI/CD Architecture](CI_CD_ARCHITECTURE.md)** - Separated pipeline design and deployment workflow
- **[Docker Image Strategy](DOCKER_IMAGE_STRATEGY.md)** - Development vs production image build strategy and decision matrix
- **[Security Architecture](SECURITY_ARCHITECTURE.md)** - Multi-layered security scanning and tool migration history
- **[Artifacts Documentation](ARTIFACTS.md)** - CI/CD pipeline artifacts and retention policies

## Development Documentation

- **[Development Guide](DEVELOPMENT.md)** - Complete development guide with tools, optimizations, and workflow

## Quick Links

### Setup & Installation

- [Local Setup](../README.md#installation)
- [Docker Setup](DOCKER.md#quick-start)
- [Environment Configuration](../README.md#configuration)

### Development

- [Development Tools](DEVELOPMENT.md#development-tools)
- [Model Comparison](DEVELOPMENT.md#model-comparison-tools)
- [API Optimizations](DEVELOPMENT.md#implementation-optimizations)
- [CI/CD Pipeline](CI_CD_ARCHITECTURE.md)
- [Security Architecture](SECURITY_ARCHITECTURE.md)
- [Testing](../README.md#testing)
- [Contributing Guidelines](../README.md#contributing)

### Deployment

- [Docker Deployment](DOCKER.md#usage-patterns)
- [Automated Scheduling](DOCKER.md#automated-scheduling-with-cron)
- [Registry Usage](DOCKER.md#available-images)
- [Environment Variables](DOCKER.md#environment-variables)

## Project Structure

```text
docs/
├── README.md                    # This file - documentation index
├── DEVELOPMENT.md               # Complete developer guide (commands, tools, optimizations)
├── DOCKER.md                    # Complete Docker guide (deployment, scheduling, registry)
├── DOCKER_IMAGE_STRATEGY.md    # Development vs production image build strategy
├── CI_CD_ARCHITECTURE.md       # Separated pipeline architecture
├── SECURITY_ARCHITECTURE.md    # Multi-layered security scanning and tool migration history
└── ARTIFACTS.md                # CI/CD pipeline artifacts
```

## External Resources

- [Mealie API Documentation](https://docs.mealie.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Docker Documentation](https://docs.docker.com/)
