# Tasks: RallyCal v4 - Family Sports Calendar Aggregator

Based on PRD: `product-specs/prd-rallycal.md`

## Relevant Files

1. `src/rallycal/__init__.py` - Main package initialization
2. `src/rallycal/core/settings.py` - Pydantic Settings configuration with environment variables
3. `src/rallycal/core/logging.py` - Loguru logging configuration with Rich formatting
4. `src/rallycal/config/manager.py` - YAML configuration file management and validation
5. `src/rallycal/config/models.py` - Pydantic models for calendar source configuration
6. `src/rallycal/database/engine.py` - SQLModel async database engine and session management
7. `src/rallycal/database/models.py` - SQLModel database models for events and calendar sources
8. `src/rallycal/database/operations.py` - Database operations using Repository pattern
9. `src/rallycal/services/fetcher.py` - Calendar fetching service using httpx AsyncClient
10. `src/rallycal/services/processor.py` - Event processing, merging, and deduplication logic
11. `src/rallycal/utils/circuit_breaker.py` - Circuit breaker pattern for external API calls
12. `src/rallycal/utils/color_manager.py` - Consistent color assignment for calendar sources
13. `src/rallycal/utils/deduplicator.py` - Event deduplication using fuzzy matching
14. `src/rallycal/generators/ical.py` - iCal feed generation using icalendar library
15. `src/rallycal/api/main.py` - FastAPI application setup with middleware
16. `src/rallycal/api/routes.py` - API route handlers for calendar feed endpoints
17. `main.py` - Application entry point
18. `tests/conftest.py` - Pytest configuration and shared fixtures
19. `tests/unit/test_settings.py` - Unit tests for core settings
20. `tests/unit/test_config_manager.py` - Unit tests for configuration management
21. `tests/unit/test_database_models.py` - Unit tests for SQLModel models
22. `tests/unit/test_fetcher.py` - Unit tests for calendar fetching service
23. `tests/unit/test_processor.py` - Unit tests for event processing
24. `tests/unit/test_ical_generator.py` - Unit tests for iCal generation
25. `tests/integration/test_api_endpoints.py` - Integration tests for API endpoints
26. `tests/integration/test_calendar_workflow.py` - End-to-end workflow tests

## Execution Guidelines

- **Critical Path:** Tasks 1.0, 2.0, 3.0, 5.0, 6.0 are required for basic MVP functionality
- **Parallel Execution:** Tasks 3.0, 4.0, 5.0 can be developed in parallel after 2.0 is complete
- **Risk Areas:** Event deduplication logic (4.3), Git webhook security (7.2), Calendar parsing edge cases (3.2)
- **Tech Stack Constraints:** Must use SQLModel (not SQLAlchemy), httpx (not requests), loguru (not logging), pytest-asyncio (not unittest)
- **Testing Strategy:** Unit tests first for each module, integration tests after API is complete, end-to-end tests last

## Tasks

- [ ] 1.0 **Foundation Setup**: Recreate core Python package structure and configuration management system
  - [ ] 1.1 Create core package structure with proper __init__.py files
    - Relevant File IDs: 1, 17
    - **Definition of Done:**
      - All package directories exist with __init__.py files
      - Package imports work correctly
      - Entry point main.py created
    - **Technical Specs:** Follow src/rallycal/ structure per CLAUDE.md
    - **Validation:** `python -c "import src.rallycal"` succeeds
  - [ ] 1.2 Implement Pydantic Settings configuration management
    - Relevant File IDs: 2
    - **Definition of Done:**
      - Settings class validates all required environment variables
      - Database URL, log level, sync frequency configurable
      - .env file support working
    - **Prerequisites:** Task 1.1 must be complete
    - **Technical Specs:** Use Pydantic Settings, support .env files
    - **Validation:** `pytest tests/unit/test_settings.py -v`
  - [ ] 1.3 Set up loguru logging with Rich formatting
    - Relevant File IDs: 3
    - **Definition of Done:**
      - Structured logging with correlation IDs
      - Rich console output in development
      - JSON logging in production
      - Log rotation and retention configured
    - **Prerequisites:** Task 1.2 must be complete
    - **Technical Specs:** Use loguru with Rich, JSON format for production
    - **Validation:** Logs appear correctly in console and files

- [ ] 2.0 **Database Layer**: Implement SQLModel async models and database operations for event storage
  - [ ] 2.1 Create SQLModel async database engine with session management
    - Relevant File IDs: 6
    - **Definition of Done:**
      - Async SQLModel engine configured for SQLite/PostgreSQL
      - Session factory with proper lifecycle management
      - Connection pooling configured per environment
      - Database URL from settings
    - **Prerequisites:** Task 1.2 must be complete
    - **Technical Specs:** SQLModel async engine, context managers for sessions
    - **Validation:** `pytest tests/unit/test_database_engine.py -v`
  - [ ] 2.2 Design and implement SQLModel database models
    - Relevant File IDs: 7, 21
    - **Definition of Done:**
      - CalendarSource model with URL, auth, colors
      - Event model with deduplication fields
      - SyncHistory model for tracking
      - ManualEvent model for custom events
      - All relationships and indexes defined
    - **Prerequisites:** Task 2.1 must be complete
    - **Technical Specs:** SQLModel with async support, proper constraints
    - **Validation:** `pytest tests/unit/test_database_models.py -v`
  - [ ] 2.3 Implement Repository pattern for database operations
    - Relevant File IDs: 8
    - **Definition of Done:**
      - Repository classes for each model
      - CRUD operations with async methods
      - Query methods for calendar aggregation
      - Proper error handling and transactions
    - **Prerequisites:** Task 2.2 must be complete
    - **Technical Specs:** Repository pattern with async/await
    - **Validation:** `pytest tests/unit/test_repositories.py -v`

- [ ] 3.0 **Calendar Fetching Service**: Build robust async calendar retrieval with httpx and retry logic
  - [ ] 3.1 Implement base calendar fetcher with httpx AsyncClient
    - Relevant File IDs: 9, 22
    - **Definition of Done:**
      - Async HTTP client with proper timeout configuration
      - Support for different authentication methods (none, basic, API key)
      - User-agent and headers properly set
      - SSL verification configurable
    - **Prerequisites:** Task 2.0 must be complete
    - **Technical Specs:** httpx AsyncClient, 30s timeout, 3 retries
    - **Validation:** `pytest tests/unit/test_fetcher.py::test_basic_fetch -v`
  - [ ] 3.2 Add robust error handling and retry logic with circuit breaker
    - Relevant File IDs: 9, 11, 22
    - **Definition of Done:**
      - Exponential backoff retry logic
      - Circuit breaker for failing calendars
      - Graceful handling of HTTP errors, timeouts, malformed data
      - Detailed error logging with context
    - **Prerequisites:** Task 3.1 must be complete
    - **Technical Specs:** Circuit breaker pattern, max 3 retries, exponential backoff
    - **Validation:** `pytest tests/unit/test_fetcher.py::test_error_handling -v`
  - [ ] 3.3 Implement calendar parsing and validation
    - Relevant File IDs: 9, 22
    - **Definition of Done:**
      - Parse iCal/ICS format using icalendar library
      - Validate event data and handle malformed entries
      - Extract event details (title, time, location, description)
      - Handle timezone conversion properly
    - **Prerequisites:** Task 3.2 must be complete
    - **Technical Specs:** Use icalendar library, handle timezone conversion
    - **Validation:** `pytest tests/unit/test_fetcher.py::test_calendar_parsing -v`

- [ ] 4.0 **Event Processing Engine**: Implement event merging, deduplication, and color coding functionality
  - [ ] 4.1 Create color assignment system for calendar sources
    - Relevant File IDs: 12
    - **Definition of Done:**
      - Consistent color assignment based on calendar source hash
      - Color palette with good visual distinction
      - Color metadata preserved in events
      - Support for manual color overrides
    - **Prerequisites:** Task 2.0 must be complete
    - **Technical Specs:** Hash-based color assignment, 8+ distinct colors
    - **Validation:** `pytest tests/unit/test_color_manager.py -v`
  - [ ] 4.2 Implement event deduplication using fuzzy matching
    - Relevant File IDs: 13, 23
    - **Definition of Done:**
      - Fuzzy matching algorithm for title, time, location
      - Configurable similarity thresholds
      - Preserve original events when unsure
      - Handle overlapping vs duplicate events correctly
    - **Prerequisites:** Task 4.1 must be complete
    - **Technical Specs:** Use difflib or fuzzywuzzy, 85% similarity threshold
    - **Validation:** `pytest tests/unit/test_deduplicator.py -v`
  - [ ] 4.3 Build event processing and merging service
    - Relevant File IDs: 10, 23
    - **Definition of Done:**
      - Merge events from multiple calendar sources
      - Apply color coding and source labeling
      - Handle manual events integration
      - Process recurring events correctly
    - **Prerequisites:** Tasks 4.1, 4.2 must be complete
    - **Technical Specs:** Combine multiple sources, preserve event integrity
    - **Validation:** `pytest tests/unit/test_processor.py -v`

- [ ] 5.0 **iCal Generation Service**: Create RFC 5545 compliant calendar feed generation using icalendar
  - [ ] 5.1 Implement basic iCal feed generation
    - Relevant File IDs: 14, 24
    - **Definition of Done:**
      - Generate RFC 5545 compliant iCal output
      - Include all required VCALENDAR properties
      - Handle VEVENT components with proper formatting
      - Support timezone information
    - **Prerequisites:** Task 4.0 must be complete
    - **Technical Specs:** Use icalendar library, RFC 5545 compliance
    - **Validation:** `pytest tests/unit/test_ical_generator.py::test_basic_generation -v`
  - [ ] 5.2 Add color coding and source identification to events
    - Relevant File IDs: 14, 24
    - **Definition of Done:**
      - Embed color information in event descriptions/titles
      - Include calendar source name in event titles
      - Maintain original event data integrity
      - Ensure compatibility with major calendar apps
    - **Prerequisites:** Task 5.1 must be complete
    - **Technical Specs:** Color in description, source in title prefix
    - **Validation:** `pytest tests/unit/test_ical_generator.py::test_color_coding -v`
  - [ ] 5.3 Implement caching and performance optimization
    - Relevant File IDs: 14, 24
    - **Definition of Done:**
      - Cache generated iCal feeds with TTL
      - Incremental updates when only some calendars change
      - Memory-efficient processing for large calendars
      - Response time under 2 seconds per PRD requirement
    - **Prerequisites:** Task 5.2 must be complete
    - **Technical Specs:** In-memory cache with 15-minute TTL
    - **Validation:** `pytest tests/unit/test_ical_generator.py::test_caching -v`

- [ ] 6.0 **FastAPI Web Application**: Build web server with endpoints for calendar feed access
  - [ ] 6.1 Create FastAPI application with middleware setup
    - Relevant File IDs: 15, 25
    - **Definition of Done:**
      - FastAPI app with CORS middleware
      - Request logging middleware
      - Error handling middleware
      - Health check endpoint
      - Security headers middleware
    - **Prerequisites:** Task 1.0 must be complete
    - **Technical Specs:** FastAPI with async support, comprehensive middleware
    - **Validation:** `pytest tests/integration/test_api_setup.py -v`
  - [ ] 6.2 Implement calendar feed API endpoints
    - Relevant File IDs: 16, 25
    - **Definition of Done:**
      - GET /calendar endpoint serving iCal feed
      - Proper Content-Type headers (text/calendar)
      - Error responses with appropriate HTTP status codes
      - Support for conditional requests (ETags)
    - **Prerequisites:** Tasks 5.0, 6.1 must be complete
    - **Technical Specs:** FastAPI dependency injection, proper HTTP headers
    - **Validation:** `pytest tests/integration/test_api_endpoints.py -v`
  - [ ] 6.3 Add rate limiting and monitoring endpoints
    - Relevant File IDs: 16, 25
    - **Definition of Done:**
      - Rate limiting for calendar feed requests
      - /health endpoint for load balancer checks
      - /metrics endpoint for observability
      - Request/response logging
    - **Prerequisites:** Task 6.2 must be complete
    - **Technical Specs:** 100 requests/minute rate limit
    - **Validation:** `pytest tests/integration/test_rate_limiting.py -v`

- [ ] 7.0 **Configuration Management**: Implement Git-based configuration updates with webhook support
  - [ ] 7.1 Enhance configuration manager for YAML calendar sources
    - Relevant File IDs: 4, 5, 20
    - **Definition of Done:**
      - Parse and validate calendars.yaml configuration
      - Support for calendar source CRUD operations
      - Configuration schema validation with Pydantic
      - Hot-reload capability for configuration changes
    - **Prerequisites:** Task 1.0 must be complete
    - **Technical Specs:** Pydantic validation, YAML parsing, file watching
    - **Validation:** `pytest tests/unit/test_config_manager.py -v`
  - [ ] 7.2 Implement Git webhook support for configuration updates
    - Relevant File IDs: 16
    - **Definition of Done:**
      - Webhook endpoint for Git repository changes
      - Configuration file pull and validation
      - Automatic calendar source updates
      - Webhook signature verification for security
    - **Prerequisites:** Tasks 6.0, 7.1 must be complete
    - **Technical Specs:** GitHub webhook format, HMAC signature verification
    - **Validation:** `pytest tests/integration/test_git_webhooks.py -v`

- [ ] 8.0 **Testing Infrastructure**: Create comprehensive pytest-asyncio test suite
  - [ ] 8.1 Set up pytest configuration and fixtures
    - Relevant File IDs: 18
    - **Definition of Done:**
      - Async test configuration with pytest-asyncio
      - Database fixtures with SQLite in-memory
      - HTTP client fixtures for API testing
      - Mock fixtures for external dependencies
    - **Prerequisites:** Task 2.0 must be complete
    - **Technical Specs:** pytest-asyncio, in-memory SQLite for tests
    - **Validation:** `pytest --version` shows asyncio support
  - [ ] 8.2 Create unit tests for core modules
    - Relevant File IDs: 19, 20, 21, 22, 23, 24
    - **Definition of Done:**
      - 80%+ test coverage for all core modules
      - Unit tests for settings, config, database, fetcher, processor
      - Mock external dependencies (HTTP calls, file system)
      - Fast test execution (under 30 seconds)
    - **Prerequisites:** Task 8.1 must be complete
    - **Technical Specs:** pytest with mocking, 80% coverage minimum
    - **Validation:** `pytest tests/unit/ --cov=src/rallycal --cov-report=term-missing`
  - [ ] 8.3 Implement integration and end-to-end tests
    - Relevant File IDs: 25, 26
    - **Definition of Done:**
      - API endpoint integration tests
      - Full calendar workflow end-to-end tests
      - Database integration tests
      - External service integration tests with real calendars
    - **Prerequisites:** Tasks 6.0, 8.2 must be complete
    - **Technical Specs:** Real HTTP requests to test calendars
    - **Validation:** `pytest tests/integration/ tests/e2e/ -v`

- [ ] 9.0 **Deployment & Operations**: Set up production deployment with loguru logging and monitoring
  - [ ] 9.1 Enhance Docker configuration for production
    - Relevant File IDs: 17
    - **Definition of Done:**
      - Multi-stage Docker build for smaller images
      - Non-root user for security
      - Health check endpoints configured
      - Environment variable configuration
    - **Prerequisites:** Task 6.0 must be complete
    - **Technical Specs:** Alpine Linux base, non-root user, health checks
    - **Validation:** `docker build . && docker run --rm rallycal --health-check`
  - [ ] 9.2 Configure deployment platform integration
    - Relevant File IDs: 17
    - **Definition of Done:**
      - Railway.toml configuration updated for new structure
      - Environment variable configuration for production
      - Database URL and sync settings configured
      - Deployment health checks working
    - **Prerequisites:** Task 9.1 must be complete
    - **Technical Specs:** Production environment variables, database URL
    - **Validation:** Successful deployment to Railway/Render
  - [ ] 9.3 Set up monitoring and operational logging
    - Relevant File IDs: 3, 17
    - **Definition of Done:**
      - Structured logging with correlation IDs
      - Error alerting and monitoring hooks
      - Performance metrics collection
      - Log aggregation ready for production
    - **Prerequisites:** Task 9.2 must be complete
    - **Technical Specs:** JSON logging, correlation IDs, error tracking
    - **Validation:** Logs appear correctly in production environment