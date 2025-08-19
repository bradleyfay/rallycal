# Testing Guidelines

## Test Execution Strategy

### During Development

- Run `uv run ruff check` after each file modification
- Run relevant component tests for modified areas before marking subtasks complete

### Before Task Completion

- Run component tests for modified areas first
- Then run full test suite (`uv run pytest`)
- Only proceed with git operations if all tests pass

## Test Organization

- Unit tests follow pytest conventions with test files prefixed with `test_`
- Test files mirror source structure (e.g., `src/module.py` → `tests/test_module.py`)
- Use pytest-asyncio for async tests
- Leverage pytest fixtures for test data and setup

## Test Commands

- `uv run pytest` - Run all tests
- `uv run pytest path/to/test_file.py` - Run specific test file
- `uv run pytest -v` - Verbose output
- `uv run pytest --cov` - Run with coverage reporting
