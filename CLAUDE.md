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
- Testing framework: pytest with pytest-asyncio
- Linting/formatting: ruff

## Tech Stack Requirements (DO NOT DEVIATE)

### Core Technologies

- **Python**: 3.13+ (use async/await patterns throughout)
- **Web Framework**: FastAPI (not Flask, Django, etc.)
- **ORM**: SQLModel
- **HTTP Client**: httpx AsyncClient (not requests, urllib, aiohttp)
- **Validation**: Pydantic v2 for all data boundaries
- **Package Manager**: uv (not pip, poetry, pipenv, conda)
- **Build System**: hatch (not setuptools directly)
- **Calendar Library**: icalendar for parsing/generation
- **Logging**: loguru (not standard logging) and Rich
- **Testing**: pytest with pytest-asyncio (never unittest)
- **Linting/Formatting**: ruff (not black, flake8, pylint, isort separately)
- **Environment Management**: python-dotenv for .env files  
- **Date/Time**: pendulum or arrow (more robust than datetime)

### Architectural Patterns

- **Repository Pattern**: All database operations through repository classes
- **Dependency Injection**: Use FastAPI's Depends() system
- **Service Layer**: Business logic in service classes, not in routes
- **Error Handling**: Structured exceptions with proper HTTP status codes
- **Configuration**: Pydantic Settings with environment variables
- **Async First**: All I/O operations must be async (database, HTTP, file I/O)
- **Type Hints**: Full type annotations on all functions and methods

### File Structure Conventions

```txt
src/rallycal/
├── api/            # FastAPI routes and middleware
├── config/         # Configuration and settings
├── core/           # Core utilities (logging, settings)
├── database/       # SQLAlchemy models and operations
├── models/         # Pydantic models for validation
├── services/       # Business logic and service layer
├── utils/          # Utility functions and helpers
└── generators/     # iCal generation logic
tests/              # Mirror src structure exactly
```

### Coding Standards

- No business logic in route handlers (thin controllers)
- Separate Pydantic models from SQLAlchemy models
- Use async context managers for database sessions
- Always use absolute imports from `src.rallycal`
- Test files must be prefixed with `test_`
- One class/major function per file when reasonable

## Architecture Overview

### Current State

- Core Python foundation established with modern tooling
- Configuration management system implemented
- Calendar fetching and processing services complete
- Database layer with SQLAlchemy models ready
- iCal generation system functional

### Core Components

1. **Calendar Fetcher Service** - Async retrieval with httpx, caching, retry logic
2. **Event Processor** - Merges, deduplicates with fuzzy matching, color-codes events  
3. **Configuration Manager** - YAML-based with Pydantic validation, Git webhook support
4. **iCal Generator** - RFC 5545 compliant output with timezone handling
5. **Web Server** - FastAPI with async middleware (to be implemented)
6. **Database** - SQLAlchemy async with Alembic migrations

### Configuration Management

- YAML-based configuration with Pydantic validation
- Git-based configuration updates via webhooks
- Color coding per calendar source with consistent hashing
- Manual event support with recurrence rules

### Database Strategy

- **Development**: SQLite with async support
- **Production**: PostgreSQL with async driver
- **Migrations**: Alembic with async engine
- **Session Management**: Async context managers
- **Connection Pooling**: Configured per environment

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
