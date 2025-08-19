# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RallyCal is a family sports calendar aggregator that combines multiple iCal/ICS feeds from youth sports platforms into a single subscribable calendar feed. The project is in early development (MVP phase) with a minimal Python codebase.

## Development Commands

### Package Management (uv)
- `uv sync` - Install dependencies
- `uv sync --dev` - Install development dependencies
- `uv run python main.py` - Run the application
- `uv run pytest` - Run tests (when implemented)
- `uv run ruff check` - Run linting
- `uv run ruff format` - Format code

### Development Workflow
- Python 3.13+ is required
- Uses uv as the package manager (not pip)
- No test framework is currently configured
- No linting configuration is currently set up

## Architecture Overview

### Current State
- Single `main.py` file with minimal "Hello World" implementation
- No dependencies currently defined in pyproject.toml
- Project is containerized with Docker (planned)
- Cloud deployment with Infrastructure-as-Code (planned)

### Planned Architecture (from PRD)
The application will be built around these core components:
1. **Calendar Fetcher Service** - Retrieves data from source calendars
2. **Event Processor** - Merges, deduplicates, and color-codes events  
3. **Configuration Manager** - Handles Git-based config updates
4. **iCal Generator** - Produces standards-compliant output feed
5. **Web Server** - Serves the aggregated calendar feed (FastAPI planned)
6. **Database** - SQLite initially, PostgreSQL migration path

### Configuration Management
- YAML-based configuration for calendar sources
- Git-based configuration management for mobile updates
- Color coding per calendar source
- Manual event support

### Technology Stack
- **Language**: Python 3.13+
- **Web Framework**: FastAPI (planned)
- **Database**: SQLite → PostgreSQL migration path
- **Containerization**: Docker
- **Infrastructure**: Cloud deployment with Terraform/Pulumi
- **CI/CD**: GitHub Actions

## Key Features to Implement

1. **Calendar Aggregation**: Support for iCal/ICS feeds from sports platforms
2. **Visual Distinction**: Color coding and labeling for different calendars
3. **Git-based Config**: Version-controlled calendar source management
4. **Universal Compatibility**: Standard iCal output for all calendar apps
5. **Automated Deployment**: Infrastructure-as-code deployment

## Development Notes

- This is an early-stage project with comprehensive PRD documentation
- Focus on MVP features: basic aggregation, color coding, git-based config
- Target users are sports parents managing 6+ different calendar subscriptions
- Output must be compatible with iPhone, Google Calendar, and Outlook
- Configuration should be simple enough for mobile GitHub app editing