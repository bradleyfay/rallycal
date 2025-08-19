# RallyCal Implementation Tasks v2

Generated from: `product-specs/prd-rallycal.md`

## Relevant Files

- `pyproject.toml` - Modern Python project configuration with hatch build system and dependencies
- `src/rallycal/__init__.py` - Package initialization file
- `src/rallycal/__about__.py` - Version management for hatch
- `src/rallycal/core/settings.py` - Pydantic settings for environment variables and app configuration
- `src/rallycal/core/logging.py` - Loguru-based structured logging configuration
- `src/rallycal/config/models.py` - Pydantic models for calendar source configuration
- `src/rallycal/config/manager.py` - Configuration file reading and Git-based updates
- `src/rallycal/services/fetcher.py` - Async calendar fetching using httpx
- `src/rallycal/services/processor.py` - Event processing, merging, and deduplication
- `src/rallycal/models/event.py` - Pydantic models for event data validation
- `src/rallycal/utils/deduplicator.py` - Event deduplication algorithms
- `src/rallycal/utils/color_manager.py` - Color assignment and management
- `src/rallycal/database/models.py` - SQLAlchemy async models
- `src/rallycal/database/operations.py` - Database CRUD operations
- `src/rallycal/generators/ical.py` - Standards-compliant iCal feed generation
- `src/rallycal/api/main.py` - FastAPI application setup
- `src/rallycal/api/routes.py` - API route handlers
- `config/calendars.yaml` - Calendar sources configuration file
- `tests/` - Complete test suite mirroring src structure
- `Dockerfile` - Container definition
- `docker-compose.yml` - Local development environment
- `alembic/` - Database migration management

### Notes

- Unit tests follow pytest conventions with test files prefixed with `test_`
- All async operations use httpx and SQLAlchemy async patterns
- Pydantic models provide data validation at all boundaries
- Use `uv` for dependency management and `hatch` for build/development
- Ruff handles all linting, formatting, and import organization

## Task Dependencies

### Parallel Execution Groups:
- **Group A**: Tasks 1.0, 8.0 (can start immediately)
- **Group B**: Tasks 2.0, 6.0 (depends on 1.0)
- **Group C**: Tasks 3.0, 4.0, 5.0 (depends on 1.0, 2.0)
- **Group D**: Task 7.0 (depends on 3.0, 4.0, 5.0, 6.0)
- **Group E**: Task 9.0 (depends on all previous tasks)

### Critical Path:
1.0 → 2.0 → 3.0 → 4.0 → 5.0 → 7.0 → 9.0

## Tasks

- [ ] 1.0 Modern Python Foundation & Project Infrastructure
  - [ ] 1.1 Initialize hatch project structure with `hatch new --init` and create src/rallycal layout
  - [ ] 1.2 Configure pyproject.toml with modern dependencies (FastAPI, SQLAlchemy[asyncio], httpx, pydantic, icalendar, uvicorn, loguru)
  - [ ] 1.3 Add development dependencies (pytest, pytest-asyncio, pytest-cov, ruff, hatch) and configure tool sections
  - [ ] 1.4 Set up Pydantic settings model in core/settings.py for environment variable validation
  - [ ] 1.5 Configure structured logging with loguru in core/logging.py with proper levels and formatting
  - [ ] 1.6 Configure ruff for linting, formatting, and import sorting with modern Python rules

- [ ] 2.0 Core Configuration Management System
  - [ ] 2.1 Design Pydantic models for calendar sources (name, url, color, enabled, auth) in config/models.py
  - [ ] 2.2 Implement ConfigManager class with YAML parsing and validation in config/manager.py
  - [ ] 2.3 Add comprehensive Pydantic validators for URL validation and color format checking
  - [ ] 2.4 Create sample calendars.yaml with realistic sports platform examples and documentation
  - [ ] 2.5 Implement file-based configuration change detection with proper event handling
  - [ ] 2.6 Add support for manual events configuration with datetime and recurrence validation

- [ ] 3.0 Calendar Data Fetching & Processing Engine
  - [ ] 3.1 Implement async CalendarFetcher using httpx.AsyncClient with connection pooling
  - [ ] 3.2 Add iCal/ICS parsing with icalendar library and comprehensive error handling
  - [ ] 3.3 Implement retry logic with exponential backoff using tenacity for failed requests
  - [ ] 3.4 Add timeout handling and circuit breaker patterns for graceful degradation
  - [ ] 3.5 Implement caching layer with TTL and conditional requests (ETag/Last-Modified)
  - [ ] 3.6 Add support for multiple authentication methods (Bearer, Basic auth, API keys)

- [ ] 4.0 Event Aggregation & Deduplication Logic
  - [ ] 4.1 Create comprehensive Event Pydantic model with datetime validation and timezone handling
  - [ ] 4.2 Implement sophisticated duplicate detection using fuzzy matching algorithms
  - [ ] 4.3 Design async event merging pipeline with conflict resolution strategies
  - [ ] 4.4 Add deterministic color assignment system with consistent hashing
  - [ ] 4.5 Implement configurable event title formatting with source identification
  - [ ] 4.6 Create overlap detection and resolution for concurrent events from different sources

- [ ] 5.0 Data Persistence & Storage Layer
  - [ ] 5.1 Design async SQLAlchemy models for Events, CalendarSources, and SyncHistory
  - [ ] 5.2 Set up Alembic for database migrations with async engine configuration
  - [ ] 5.3 Implement async repository pattern with comprehensive CRUD operations
  - [ ] 5.4 Add connection pooling, transaction management, and proper session handling
  - [ ] 5.5 Implement cascade deletion and cleanup procedures for removed calendar sources
  - [ ] 5.6 Add database indexing strategy for performance optimization

- [ ] 6.0 iCal Feed Generation & Standards Compliance
  - [ ] 6.1 Implement ICalGenerator using icalendar library with RFC 5545 compliance
  - [ ] 6.2 Add comprehensive timezone handling and VTIMEZONE generation
  - [ ] 6.3 Implement color coding via CATEGORIES and X-CUSTOM properties
  - [ ] 6.4 Add event categorization, source labeling, and metadata preservation
  - [ ] 6.5 Ensure full RFC 5545 compliance with validation and error reporting
  - [ ] 6.6 Implement intelligent caching with conditional generation and ETags

- [ ] 7.0 FastAPI Web Server & API Endpoints
  - [ ] 7.1 Set up FastAPI application with async middleware, CORS, and security headers
  - [ ] 7.2 Implement calendar feed endpoint (/calendar.ics) with proper HTTP headers
  - [ ] 7.3 Add comprehensive health check endpoints with dependency validation
  - [ ] 7.4 Implement Git webhook handler for configuration updates with signature verification
  - [ ] 7.5 Add request/response logging, metrics collection, and performance monitoring
  - [ ] 7.6 Implement rate limiting, request validation, and security best practices

- [ ] 8.0 Comprehensive Testing Framework
  - [ ] 8.1 Configure pytest with async support, coverage reporting, and test discovery
  - [ ] 8.2 Create unit tests for all Pydantic models with edge cases and validation scenarios
  - [ ] 8.3 Implement async calendar fetching tests with httpx mock responses
  - [ ] 8.4 Add extensive event processing tests with duplicate detection validation
  - [ ] 8.5 Create async database tests with fixtures and transaction rollback
  - [ ] 8.6 Implement FastAPI integration tests with TestClient and endpoint validation
  - [ ] 8.7 Add end-to-end tests for complete calendar aggregation workflow

- [ ] 9.0 Containerization & Cloud Deployment Pipeline
  - [ ] 9.1 Create optimized multi-stage Dockerfile with security scanning
  - [ ] 9.2 Set up docker-compose.yml with database and development hot-reload
  - [ ] 9.3 Implement health checks, readiness probes, and graceful shutdown
  - [ ] 9.4 Add environment-specific configuration with secrets management
  - [ ] 9.5 Create GitHub Actions workflow with testing, security scanning, and deployment
  - [ ] 9.6 Set up infrastructure-as-code with Terraform/Pulumi for cloud deployment