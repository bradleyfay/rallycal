# RallyCal Implementation Tasks

Generated from: `product-specs/prd-rallycal.md`

## Relevant Files

- `src/rallycal/config/manager.py` - Configuration file reading and Git-based updates with Pydantic validation
- `tests/config/test_manager.py` - Unit tests for configuration management
- `src/rallycal/services/calendar_fetcher.py` - Async iCal/ICS feed retrieval using httpx
- `tests/services/test_calendar_fetcher.py` - Unit tests for calendar fetching with mock responses
- `src/rallycal/services/event_processor.py` - Event merging, deduplication, and color coding with Pydantic models
- `tests/services/test_event_processor.py` - Unit tests for event processing logic
- `src/rallycal/database/models.py` - SQLAlchemy async models for events and configuration
- `tests/database/test_models.py` - Unit tests for database models
- `src/rallycal/database/operations.py` - Async database CRUD operations
- `tests/database/test_operations.py` - Unit tests for database operations
- `src/rallycal/services/ical_generator.py` - Standards-compliant iCal feed generation
- `tests/services/test_ical_generator.py` - Unit tests for iCal generation and validation
- `src/rallycal/api/main.py` - FastAPI application and middleware setup
- `tests/api/test_main.py` - Unit tests for API application
- `src/rallycal/api/routes/calendar.py` - Calendar feed serving endpoints
- `tests/api/routes/test_calendar.py` - Unit tests for calendar routes
- `src/rallycal/models/events.py` - Pydantic models for event data validation
- `tests/models/test_events.py` - Unit tests for Pydantic event models
- `src/rallycal/utils/duplicate_detector.py` - Event deduplication algorithms
- `tests/utils/test_duplicate_detector.py` - Unit tests for duplicate detection
- `src/rallycal/utils/color_manager.py` - Color assignment and management utilities
- `tests/utils/test_color_manager.py` - Unit tests for color management
- `config/calendars.yaml` - Calendar sources configuration file with examples
- `src/rallycal/core/logging.py` - Loguru logging configuration
- `src/rallycal/core/settings.py` - Pydantic settings for environment variables
- `Dockerfile` - Multi-stage container definition for production
- `docker-compose.yml` - Local development environment setup
- `pyproject.toml` - Hatch build configuration with modern dependencies

### Notes

- Unit tests should follow Python conventions with test files prefixed with `test_` (e.g., `module.py` and `test_module.py` in corresponding tests/ directory).
- All testing should be done within the pytest framework and ecosystem. Use pytest-asyncio for async tests.
- Use `pytest [optional/path/to/test/file]` to run tests. Running without a path executes all tests found by pytest's discovery mechanism.
- Leverage `hatch` for project scaffolding, dependency management, and build processes.
- Use `ruff` for all linting, formatting, and type checking instead of separate tools.
- All HTTP operations should use `httpx` for async support and modern API.
- Data validation at application boundaries should use Pydantic models throughout.

## Tasks

- [ ] 1.0 Modern Python Foundation & Development Setup
  - [ ] 1.1 Configure hatch in pyproject.toml with modern dependencies (FastAPI, SQLAlchemy[asyncio], httpx, pydantic, pydantic-settings, icalendar, uvicorn, loguru)
  - [ ] 1.2 Add development dependencies for modern toolchain (pytest, pytest-asyncio, pytest-cov, pytest-mock, ruff, hatch)
  - [ ] 1.3 Use `hatch new --init` to scaffold project structure, then add custom subdirectories under src/rallycal/
  - [ ] 1.4 Create comprehensive tests/ directory structure mirroring src/rallycal/ layout
  - [ ] 1.5 Set up loguru logging configuration with structured logging and proper levels
  - [ ] 1.6 Create Pydantic settings model for environment variable validation and type safety
  - [ ] 1.7 Configure ruff in pyproject.toml for linting, formatting, and type checking with modern rules

- [ ] 2.0 Configuration Management with Pydantic
  - [ ] 2.1 Design comprehensive Pydantic models for calendar sources (name, url, color, enabled, auth_config, sync_interval)
  - [ ] 2.2 Implement ConfigManager class with Pydantic validation for YAML configuration parsing
  - [ ] 2.3 Add Pydantic validators for URL validation, color format checking, and comprehensive error messages
  - [ ] 2.4 Implement file-based configuration change detection with proper event handling
  - [ ] 2.5 Create sample calendars.yaml with realistic sports platform examples and documentation
  - [ ] 2.6 Add Pydantic models for manual events with full validation (datetime, recurrence, categories)
  - [ ] 2.7 Design Git webhook handler using FastAPI with signature verification for security

- [ ] 3.0 Async Calendar Fetcher Service
  - [ ] 3.1 Implement CalendarFetcher class using httpx.AsyncClient with connection pooling and timeouts
  - [ ] 3.2 Add async iCal/ICS parsing with icalendar library and Pydantic model validation
  - [ ] 3.3 Implement tenacity-based retry logic with exponential backoff and jitter for failed requests
  - [ ] 3.4 Add comprehensive timeout handling, circuit breaker pattern, and graceful degradation
  - [ ] 3.5 Implement Redis-based caching with TTL and conditional requests (ETag/Last-Modified)
  - [ ] 3.6 Add support for multiple authentication methods (Bearer tokens, Basic auth, API keys) via Pydantic
  - [ ] 3.7 Create health monitoring system with metrics collection and alerting for calendar sources

- [ ] 4.0 Event Processing Engine with Data Validation
  - [ ] 4.1 Implement comprehensive Event Pydantic model with datetime validation, timezone handling, and field constraints
  - [ ] 4.2 Create sophisticated duplicate detection using fuzzy matching and configurable similarity thresholds
  - [ ] 4.3 Implement async event merging pipeline with conflict resolution and priority handling
  - [ ] 4.4 Add deterministic color assignment system with consistent hashing and visual accessibility
  - [ ] 4.5 Implement configurable event title formatting with source identification and custom templates
  - [ ] 4.6 Create overlap detection and resolution for concurrent events from different sources
  - [ ] 4.7 Add manual event integration with validation, priority handling, and source tracking

- [ ] 5.0 Database Layer with Modern ORM
  - [ ] 5.1 Design async SQLAlchemy models for Events, CalendarSources, and SyncHistory with proper relationships
  - [ ] 5.2 Implement Alembic migrations with async engine and proper transaction handling
  - [ ] 5.3 Create async repository pattern with comprehensive CRUD operations and bulk operations
  - [ ] 5.4 Add async connection pooling, transaction management, and proper session handling
  - [ ] 5.5 Implement cascade deletion and cleanup procedures for removed calendar sources
  - [ ] 5.6 Add database indexing strategy for performance optimization and query analysis
  - [ ] 5.7 Create backup procedures and data integrity checks with automated validation

- [ ] 6.0 Standards-Compliant iCal Generator
  - [ ] 6.1 Implement async ICalGenerator using icalendar library with proper RFC 5545 compliance
  - [ ] 6.2 Add comprehensive timezone handling, daylight saving time support, and VTIMEZONE generation
  - [ ] 6.3 Implement color coding via CATEGORIES property and X-CUSTOM properties for compatibility
  - [ ] 6.4 Add event categorization, source labeling, and metadata preservation
  - [ ] 6.5 Ensure full RFC 5545 compliance with validation and error reporting
  - [ ] 6.6 Implement intelligent caching with conditional generation and ETags for performance
  - [ ] 6.7 Add comprehensive iCal validation, lint checking, and compatibility testing

- [ ] 7.0 FastAPI Web Server & API Layer
  - [ ] 7.1 Set up FastAPI application with async middleware, CORS, compression, and security headers
  - [ ] 7.2 Implement calendar feed endpoint (/calendar.ics) with proper content-type and caching headers
  - [ ] 7.3 Add comprehensive health check endpoints with dependency validation and metrics
  - [ ] 7.4 Implement admin API endpoints for configuration management with proper authentication
  - [ ] 7.5 Add request/response logging, metrics collection, and performance monitoring
  - [ ] 7.6 Implement rate limiting, request validation, and security best practices
  - [ ] 7.7 Add OpenAPI documentation with examples and comprehensive API specification

- [ ] 8.0 Comprehensive Testing Framework
  - [ ] 8.1 Configure pytest with async support, coverage reporting, and test discovery
  - [ ] 8.2 Create comprehensive unit tests for Pydantic configuration models with edge cases
  - [ ] 8.3 Implement async calendar fetching tests with httpx mock responses and error scenarios
  - [ ] 8.4 Add extensive event processing tests with duplicate detection and edge case validation
  - [ ] 8.5 Create async database tests with test database fixtures and transaction rollback
  - [ ] 8.6 Implement FastAPI integration tests with TestClient and real endpoint testing
  - [ ] 8.7 Add end-to-end tests for complete calendar aggregation workflow with real data
  - [ ] 8.8 Set up pytest fixtures, factories, and test data generators for comprehensive coverage

- [ ] 9.0 Containerization & Modern Deployment Pipeline
  - [ ] 9.1 Create optimized multi-stage Dockerfile with proper Python base image and security scanning
  - [ ] 9.2 Set up docker-compose.yml with Redis, database, and development hot-reload support
  - [ ] 9.3 Implement comprehensive health checks, readiness probes, and graceful shutdown handling
  - [ ] 9.4 Add environment-specific configuration with secrets management and validation
  - [ ] 9.5 Create GitHub Actions workflow with matrix testing, security scanning, and automated deployment
  - [ ] 9.6 Implement comprehensive CI pipeline with ruff checking, pytest execution, and coverage reporting
  - [ ] 9.7 Set up infrastructure-as-code with Terraform/Pulumi for cloud deployment and monitoring