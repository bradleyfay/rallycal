# Tech Stack Compliance Protocol

When implementing any code, strictly adhere to the tech stack defined in **CLAUDE.md**.

## Must Use

- **httpx.AsyncClient** for all HTTP operations (never requests)
- **Pydantic v2** for all data validation
- **SQLAlchemy 2.0+** async patterns for database operations
- **FastAPI** for web framework (never Flask/Django)
- **loguru** for logging (never standard logging)
- **pytest** for testing (never unittest)
- **uv** for package management (never pip directly)

## Must Follow

- All I/O operations must be async
- Use repository pattern for database operations
- Keep business logic in service layer, not routes
- Full type hints on all functions
- Absolute imports from `src.rallycal`

## Red Flags

If you find yourself wanting to:
- Use `requests.get()` → Use `httpx.AsyncClient`
- Write `unittest.TestCase` → Use pytest
- Put logic in routes → Move to service layer
- Use relative imports → Use absolute from `src.rallycal`
- Skip type hints → Add them

Review CLAUDE.md for complete requirements.