# Architecture Refactor Task List v01

## Overview
This task list implements the simplified architecture decisions for RallyCal, focusing on developer experience, maintainability, and rapid MVP delivery.

## Relevant Files

- `CLAUDE.md` - AI assistant guidelines requiring updates for new tech stack
- `DEPLOYMENT.md` - Move from root to `docs/` directory
- `VALIDATION.md` - Move from root to `docs/` directory
- `docs/` - New directory to organize documentation
- `CONTRIBUTING.md` - New file for developer setup and workflow
- `pyproject.toml` - Dependencies need updating for SQLModel and new tools
- `.pre-commit-config.yaml` - New file for pre-commit hooks configuration
- `.env.example` - New file documenting required environment variables
- `.github/workflows/main.yml` - Simplified CI/CD pipeline
- `.github/workflows/README.md` - New file documenting CI/CD pipelines
- `src/rallycal/database/models.py` - Convert from SQLAlchemy to SQLModel
- `src/rallycal/models/` - Directory can be removed (unified with SQLModel)
- `src/rallycal/core/settings.py` - Update for dotenv integration
- `src/rallycal/services/scheduler.py` - New file for APScheduler integration
- `src/rallycal/utils/cache.py` - New file for in-memory caching
- `tests/conftest.py` - Update for SQLModel and simplified testing
- `alembic/` - Keep but update for SQLModel compatibility

### Notes

- This refactor prioritizes simplicity and developer experience over complex patterns
- All changes maintain backward compatibility where possible
- Testing uses SQLite in-memory for speed and simplicity
- Deployment targets Railway/Render instead of complex AWS infrastructure

## Tasks

- [ ] 1.0 Migrate from SQLAlchemy to SQLModel
- [ ] 2.0 Implement Development Quality Gates
- [ ] 3.0 Simplify Deployment Strategy
- [ ] 4.0 Add Task Scheduling with APScheduler
- [ ] 5.0 Implement Simple Caching Layer
- [ ] 6.0 Reorganize Documentation Structure
- [ ] 7.0 Update Documentation and Guidelines
- [ ] 8.0 Set Up Simplified CI/CD Pipeline
- [ ] 9.0 Clean Up Obsolete Code and Dependencies