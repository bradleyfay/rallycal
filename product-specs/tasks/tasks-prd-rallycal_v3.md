# Task List for RallyCal Implementation

## Relevant Files

1. `src/rallycal/__init__.py` - Package initialization
2. `src/rallycal/__about__.py` - Version information
3. `src/rallycal/core/__init__.py` - Core module initialization
4. `src/rallycal/core/settings.py` - Pydantic settings configuration
5. `src/rallycal/core/logging.py` - Loguru logging setup
6. `src/rallycal/core/exceptions.py` - Custom exception classes
7. `src/rallycal/database/__init__.py` - Database module initialization
8. `src/rallycal/database/engine.py` - SQLAlchemy async engine configuration
9. `src/rallycal/database/models.py` - SQLModel database models
10. `src/rallycal/database/repositories.py` - Repository pattern implementation
11. `src/rallycal/models/__init__.py` - Pydantic models initialization
12. `src/rallycal/models/calendar.py` - Calendar configuration models
13. `src/rallycal/models/event.py` - Event data models
14. `src/rallycal/models/sync.py` - Sync status models
15. `src/rallycal/config/__init__.py` - Configuration module initialization
16. `src/rallycal/config/manager.py` - Configuration file manager
17. `src/rallycal/config/validator.py` - Configuration validation logic
18. `src/rallycal/services/__init__.py` - Services module initialization
19. `src/rallycal/services/fetcher.py` - Calendar fetching service
20. `src/rallycal/services/processor.py` - Event processing service
21. `src/rallycal/services/scheduler.py` - Sync scheduling service
22. `src/rallycal/generators/__init__.py` - Generator module initialization
23. `src/rallycal/generators/ical.py` - iCal feed generator
24. `src/rallycal/utils/__init__.py` - Utilities module initialization
25. `src/rallycal/utils/deduplicator.py` - Event deduplication utilities
26. `src/rallycal/utils/color_manager.py` - Color coding utilities
27. `src/rallycal/utils/circuit_breaker.py` - Circuit breaker implementation
28. `src/rallycal/utils/retry.py` - Retry logic utilities
29. `src/rallycal/api/__init__.py` - API module initialization
30. `src/rallycal/api/app.py` - FastAPI application setup
31. `src/rallycal/api/routes/__init__.py` - Routes module initialization
32. `src/rallycal/api/routes/calendar.py` - Calendar feed endpoints
33. `src/rallycal/api/routes/health.py` - Health check endpoints
34. `src/rallycal/api/routes/webhook.py` - Git webhook endpoints
35. `src/rallycal/api/dependencies.py` - FastAPI dependencies
36. `src/rallycal/api/middleware.py` - API middleware configuration
37. `src/rallycal/main.py` - Application entry point
38. `alembic.ini` - Alembic configuration file
39. `alembic/env.py` - Alembic environment setup
40. `alembic/versions/001_initial_schema.py` - Initial database migration
41. `.env.example` - Environment variables template
42. `config/calendars.yaml` - Calendar configuration file (existing)
43. `tests/conftest.py` - Pytest fixtures and configuration
44. `tests/unit/test_models.py` - Unit tests for models
45. `tests/unit/test_fetcher.py` - Unit tests for fetcher
46. `tests/unit/test_processor.py` - Unit tests for processor
47. `tests/unit/test_deduplicator.py` - Unit tests for deduplication
48. `tests/integration/test_api.py` - API integration tests
49. `tests/integration/test_database.py` - Database integration tests
50. `tests/e2e/test_workflow.py` - End-to-end workflow tests
51. `Dockerfile` - Docker container configuration (existing)
52. `docker-compose.yml` - Docker compose configuration (existing)
53. `.github/workflows/ci.yml` - CI workflow configuration
54. `.github/workflows/deploy.yml` - Deployment workflow
55. `railway.toml` - Railway deployment config (existing)
56. `render.yaml` - Render deployment config (existing)

### Notes

- Break complex parent tasks into 4-8 actionable subtasks for optimal execution flow
- Ensure each subtask represents a complete, testable unit of work
- Consider architectural decisions that may require approval gates when structuring tasks
- Group related functionality to minimize context switching during implementation
- Follow CLAUDE.md tech stack requirements strictly (FastAPI, SQLModel, httpx, etc.)
- All code must be Python 3.13+ with full async/await patterns

## Tasks

- [ ] 1.0 Initialize Project Foundation and Core Structure
  - [ ] 1.1 Create package directory structure
    - Relevant File IDs: 1, 3, 7, 11, 15, 18, 22, 24, 29, 31
    - Create all necessary module directories following the structure in CLAUDE.md
    - Initialize each module with appropriate `__init__.py` files
  - [ ] 1.2 Set up version management
    - Relevant File IDs: 2
    - Create `__about__.py` with version string
    - Configure hatch to use this for versioning
  - [ ] 1.3 Implement core settings with Pydantic
    - Relevant File IDs: 4, 41
    - Define all application settings using pydantic-settings
    - Support environment variables with `.env` file
    - Include database URL, sync intervals, API configuration
  - [ ] 1.4 Configure Loguru logging system
    - Relevant File IDs: 5
    - Set up structured logging with Loguru
    - Configure Rich console output for development
    - Add log rotation and different levels per environment
  - [ ] 1.5 Create custom exception classes
    - Relevant File IDs: 6
    - Define application-specific exceptions
    - Include exceptions for fetch failures, validation errors, etc.
  - [ ] 1.6 Create main application entry point
    - Relevant File IDs: 37
    - Implement async main function
    - Set up application lifecycle management

- [ ] 2.0 Implement Database Layer with SQLModel
  - [ ] 2.1 Configure async SQLAlchemy engine
    - Relevant File IDs: 8
    - Set up async engine with aiosqlite for dev
    - Configure connection pooling
    - Support PostgreSQL for production
  - [ ] 2.2 Define SQLModel database models
    - Relevant File IDs: 9
    - Create Event model with all iCal fields
    - Create CalendarSource model for tracking sources
    - Create SyncStatus model for sync history
    - Add appropriate indexes and relationships
  - [ ] 2.3 Implement repository pattern
    - Relevant File IDs: 10
    - Create base repository class with CRUD operations
    - Implement EventRepository with bulk operations
    - Implement CalendarSourceRepository
    - Use async context managers for sessions
  - [ ] 2.4 Set up Alembic migrations
    - Relevant File IDs: 38, 39, 40
    - Configure Alembic for async operations
    - Create initial schema migration
    - Add migration for indexes and constraints
  - [ ] 2.5 Create database dependency injection
    - Relevant File IDs: 35
    - Implement get_db dependency for FastAPI
    - Ensure proper session lifecycle management

- [ ] 3.0 Build Configuration Management System
  - [ ] 3.1 Define Pydantic models for configuration
    - Relevant File IDs: 11, 12, 13, 14
    - Create CalendarSource model with auth options
    - Create ManualEvent model with recurrence support
    - Create GlobalSettings model
    - Add validation rules for all fields
  - [ ] 3.2 Implement configuration file manager
    - Relevant File IDs: 16
    - Load and parse YAML configuration
    - Watch for file changes using watchdog
    - Trigger reload on changes
    - Handle parsing errors gracefully
  - [ ] 3.3 Create configuration validator
    - Relevant File IDs: 17
    - Validate calendar URLs are accessible
    - Check authentication credentials
    - Verify color codes are valid
    - Test manual event recurrence rules
  - [ ] 3.4 Build configuration caching layer
    - Relevant File IDs: 16
    - Cache parsed configuration in memory
    - Invalidate cache on file changes
    - Provide thread-safe access to configuration

- [ ] 4.0 Create Calendar Fetching Service
  - [ ] 4.1 Implement async HTTP client with httpx
    - Relevant File IDs: 19
    - Configure httpx AsyncClient with timeouts
    - Support basic auth, API key, and OAuth
    - Handle redirects and different content types
    - Add user agent headers for compatibility
  - [ ] 4.2 Build calendar fetching logic
    - Relevant File IDs: 19
    - Parse iCal/ICS feeds using icalendar library
    - Handle malformed calendar data gracefully
    - Support webcal:// protocol conversion
    - Extract all event properties
  - [ ] 4.3 Implement retry mechanism
    - Relevant File IDs: 28
    - Use tenacity for retry decoration
    - Configure exponential backoff
    - Different strategies for different error types
    - Log retry attempts
  - [ ] 4.4 Add circuit breaker pattern
    - Relevant File IDs: 27
    - Track failure rates per calendar source
    - Open circuit after threshold failures
    - Implement half-open state for recovery
    - Auto-close after success
  - [ ] 4.5 Create response caching
    - Relevant File IDs: 19
    - Implement ETag support for conditional requests
    - Cache successful responses with TTL
    - Invalidate cache on configuration changes

- [ ] 5.0 Develop Event Processing and Deduplication Engine
  - [ ] 5.1 Build event parser and normalizer
    - Relevant File IDs: 20
    - Parse all iCal event fields
    - Normalize timezones using pendulum
    - Handle all-day events correctly
    - Process recurring events with rrule
  - [ ] 5.2 Implement deduplication logic
    - Relevant File IDs: 25
    - Create fuzzy matching algorithm
    - Compare title, time, and location
    - Use configurable similarity threshold
    - Handle slight variations in data
  - [ ] 5.3 Create color coding system
    - Relevant File IDs: 26
    - Generate consistent colors per calendar
    - Use hash-based color assignment
    - Support custom color overrides
    - Ensure color contrast standards
  - [ ] 5.4 Build event merger
    - Relevant File IDs: 20
    - Merge duplicate events intelligently
    - Preserve most complete information
    - Handle conflicting data
    - Maintain source attribution
  - [ ] 5.5 Process manual events
    - Relevant File IDs: 20
    - Inject manual events from config
    - Process recurrence rules
    - Apply color coding
    - Merge with fetched events

- [ ] 6.0 Implement iCal Feed Generator
  - [ ] 6.1 Create RFC 5545 compliant generator
    - Relevant File IDs: 23
    - Generate valid VCALENDAR structure
    - Include all required properties
    - Add PRODID and VERSION fields
    - Handle special characters correctly
  - [ ] 6.2 Build event serializer
    - Relevant File IDs: 23
    - Convert database events to VEVENT format
    - Embed color information in properties
    - Add source calendar labels
    - Preserve all original fields
  - [ ] 6.3 Implement streaming response
    - Relevant File IDs: 23
    - Generate iCal data as async generator
    - Avoid loading all events in memory
    - Support chunked transfer encoding
  - [ ] 6.4 Add calendar metadata
    - Relevant File IDs: 23
    - Set calendar name and description
    - Include timezone definitions
    - Add refresh interval hints
    - Set appropriate cache headers

- [ ] 7.0 Build FastAPI Web Server and API Endpoints
  - [ ] 7.1 Set up FastAPI application
    - Relevant File IDs: 30, 36
    - Initialize FastAPI with OpenAPI docs
    - Configure CORS for calendar apps
    - Add request/response logging middleware
    - Set up error handling middleware
  - [ ] 7.2 Implement calendar feed endpoint
    - Relevant File IDs: 32
    - Create GET /calendar.ics endpoint
    - Support webcal:// protocol
    - Set correct content-type headers
    - Add caching headers
  - [ ] 7.3 Create health and status endpoints
    - Relevant File IDs: 33
    - Implement /health for liveness check
    - Add /ready for readiness check
    - Create /status with sync information
    - Include metrics in response
  - [ ] 7.4 Build webhook endpoint
    - Relevant File IDs: 34
    - Create POST /webhook/github endpoint
    - Verify webhook signatures
    - Parse GitHub webhook payload
    - Trigger configuration reload
  - [ ] 7.5 Set up API dependencies
    - Relevant File IDs: 35
    - Create database session dependency
    - Add configuration dependency
    - Implement authentication (future)

- [ ] 8.0 Add Scheduled Synchronization System
  - [ ] 8.1 Configure APScheduler
    - Relevant File IDs: 21
    - Set up async job scheduler
    - Configure job stores
    - Add executors for async jobs
    - Enable job persistence
  - [ ] 8.2 Implement sync orchestration
    - Relevant File IDs: 21
    - Create main sync job
    - Fetch calendars in parallel
    - Process events sequentially
    - Update database atomically
  - [ ] 8.3 Add adaptive scheduling
    - Relevant File IDs: 21
    - Adjust intervals based on change frequency
    - Respect rate limits
    - Handle failed syncs
    - Support manual trigger
  - [ ] 8.4 Create sync monitoring
    - Relevant File IDs: 21
    - Track sync duration
    - Log success/failure rates
    - Store sync history
    - Generate sync reports

- [ ] 9.0 Implement Git-based Configuration Updates
  - [ ] 9.1 Handle GitHub webhooks
    - Relevant File IDs: 34
    - Parse webhook events
    - Filter for calendars.yaml changes
    - Verify webhook signatures
    - Queue configuration reload
  - [ ] 9.2 Build Git integration
    - Relevant File IDs: 16
    - Clone configuration repository
    - Pull latest changes
    - Support private repositories
    - Handle merge conflicts
  - [ ] 9.3 Implement configuration rollback
    - Relevant File IDs: 16, 17
    - Keep previous configuration version
    - Validate new configuration
    - Rollback on validation failure
    - Log all configuration changes
  - [ ] 9.4 Add configuration versioning
    - Relevant File IDs: 16
    - Track configuration versions
    - Store configuration history
    - Support rollback to specific version

- [ ] 10.0 Create Comprehensive Test Suite
  - [ ] 10.1 Set up testing infrastructure
    - Relevant File IDs: 43
    - Configure pytest with async support
    - Create fixtures for database
    - Mock external services
    - Set up test configuration
  - [ ] 10.2 Write unit tests for models
    - Relevant File IDs: 44
    - Test Pydantic model validation
    - Test SQLModel relationships
    - Verify field constraints
    - Check serialization
  - [ ] 10.3 Create service unit tests
    - Relevant File IDs: 45, 46, 47
    - Test fetcher with mocked responses
    - Test processor logic
    - Test deduplication algorithm
    - Verify color assignment
  - [ ] 10.4 Implement integration tests
    - Relevant File IDs: 48, 49
    - Test API endpoints
    - Test database operations
    - Verify configuration loading
    - Test webhook handling
  - [ ] 10.5 Add end-to-end tests
    - Relevant File IDs: 50
    - Test complete sync workflow
    - Verify calendar generation
    - Test configuration updates
    - Validate output format

- [ ] 11.0 Set up Logging, Monitoring, and Error Handling
  - [ ] 11.1 Configure structured logging
    - Relevant File IDs: 5
    - Set up JSON logging for production
    - Add correlation IDs
    - Include context in logs
    - Configure log aggregation
  - [ ] 11.2 Implement error tracking
    - Relevant File IDs: 6, 30
    - Catch and log all exceptions
    - Group similar errors
    - Add Sentry integration (optional)
    - Create error reports
  - [ ] 11.3 Add performance monitoring
    - Relevant File IDs: 30, 36
    - Track request duration
    - Monitor database queries
    - Measure sync performance
    - Track memory usage
  - [ ] 11.4 Create alerting system
    - Relevant File IDs: 21
    - Alert on sync failures
    - Monitor feed availability
    - Track error rates
    - Send notifications

- [ ] 12.0 Configure Docker Containerization
  - [ ] 12.1 Optimize Dockerfile
    - Relevant File IDs: 51
    - Use multi-stage build
    - Minimize image size
    - Add health check
    - Run as non-root user
  - [ ] 12.2 Update docker-compose
    - Relevant File IDs: 52
    - Add database service
    - Configure volumes
    - Set environment variables
    - Add development overrides
  - [ ] 12.3 Add container security
    - Relevant File IDs: 51
    - Scan for vulnerabilities
    - Use minimal base image
    - Remove unnecessary packages
    - Set resource limits

- [ ] 13.0 Implement CI/CD Pipeline
  - [ ] 13.1 Create CI workflow
    - Relevant File IDs: 53
    - Run tests on pull requests
    - Check code with ruff
    - Run type checking
    - Generate coverage reports
  - [ ] 13.2 Add deployment workflow
    - Relevant File IDs: 54
    - Build Docker images
    - Push to registry
    - Deploy to staging
    - Support production deploy
  - [ ] 13.3 Implement quality gates
    - Relevant File IDs: 53
    - Require passing tests
    - Check coverage threshold
    - Verify no security issues
    - Enforce code standards
  - [ ] 13.4 Add dependency management
    - Relevant File IDs: 53
    - Check for vulnerabilities
    - Update dependencies
    - Create update PRs
    - Test compatibility

- [ ] 14.0 Deploy to Cloud Platform
  - [ ] 14.1 Configure Railway deployment
    - Relevant File IDs: 55
    - Set environment variables
    - Configure database
    - Set up domain
    - Enable auto-deploy
  - [ ] 14.2 Set up Render deployment
    - Relevant File IDs: 56
    - Configure web service
    - Set up managed database
    - Configure environment
    - Add health checks
  - [ ] 14.3 Implement production readiness
    - Relevant File IDs: 30, 55, 56
    - Configure SSL/TLS
    - Set up monitoring
    - Implement backups
    - Add rate limiting
  - [ ] 14.4 Create deployment documentation
    - Relevant File IDs: 55, 56
    - Document deployment process
    - Create runbook
    - Add troubleshooting guide
    - Include rollback procedures

## Task Dependencies Graph

### Execution Phases

**Phase 1: Foundation (Days 1-2)**
- 1.0 Initialize Project Foundation → Required for all other tasks
- Start 10.1 (testing infrastructure setup) in parallel

**Phase 2: Data & Configuration (Days 3-4)**
- 2.0 Database Layer (depends on 1.0)
- 3.0 Configuration Management (depends on 1.0)
- These can run in parallel

**Phase 3: Core Services (Days 5-7)**
- 4.0 Calendar Fetching (depends on 3.0)
- 5.0 Event Processing (depends on 2.0, 3.0)
- 6.0 iCal Generator (depends on 2.0, 5.0)

**Phase 4: API & Scheduling (Days 8-9)**
- 7.0 FastAPI Server (depends on 6.0)
- 8.0 Scheduled Sync (depends on 4.0, 5.0)
- 9.0 Git Updates (depends on 3.0, 7.4)

**Phase 5: Quality & Testing (Days 7-10, overlapping)**
- 10.2-10.5 Tests (continuous, after each component)
- 11.0 Monitoring (depends on 7.0)

**Phase 6: Deployment (Days 10-12)**
- 12.0 Docker (can start early, finalize after 7.0)
- 13.0 CI/CD (depends on 10.0, 12.0)
- 14.0 Cloud Deploy (depends on 12.0, 13.0)

### Parallel Execution Opportunities

**Can be done in parallel:**
- Database models (2.2) and Configuration models (3.1)
- Calendar fetching (4.0) and Event processing setup (5.1-5.2)
- Different API endpoints (7.2, 7.3, 7.4)
- Unit tests for different components (10.2, 10.3)
- Railway (14.1) and Render (14.2) deployments

**Must be sequential:**
- Database engine (2.1) → Models (2.2) → Repository (2.3)
- Configuration models (3.1) → Manager (3.2) → Validator (3.3)
- Event processing (5.0) → iCal Generator (6.0)
- FastAPI setup (7.1) → Endpoints (7.2-7.5)
- Docker (12.0) → CI/CD (13.0) → Deploy (14.0)

### Critical Path

1. Project Foundation (1.0)
2. Database Layer (2.0) + Configuration (3.0)
3. Calendar Fetching (4.0) + Event Processing (5.0)
4. iCal Generator (6.0)
5. FastAPI Server (7.0)
6. Docker + CI/CD (12.0, 13.0)
7. Cloud Deployment (14.0)

### Recommended Developer Assignment

**Developer 1: Foundation & Infrastructure**
- Tasks: 1.0, 11.0, 12.0
- Focus: Core setup, logging, containerization

**Developer 2: Data Layer**
- Tasks: 2.0, 10.1, 10.2
- Focus: Database, models, testing infrastructure

**Developer 3: Configuration & Integration**
- Tasks: 3.0, 9.0, 10.4
- Focus: Config management, Git integration

**Developer 4: Calendar Services**
- Tasks: 4.0, 5.0, 10.3
- Focus: Fetching, processing, deduplication

**Developer 5: API & Deployment**
- Tasks: 6.0, 7.0, 8.0, 13.0, 14.0
- Focus: Web server, scheduling, deployment

All developers should collaborate on end-to-end testing (10.5) and documentation.