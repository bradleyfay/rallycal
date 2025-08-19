# Git Commit Standards

Follow **Conventional Commits 1.0.0** standard precisely.

## Format

`<type>[optional scope]: <description>`

## Types (use ONLY these)

- `feat:` A new feature
- `fix:` A bug fix
- `docs:` Documentation only changes
- `style:` Changes that don't affect code meaning (white-space, formatting, missing semi-colons, etc)
- `refactor:` Code change that neither fixes a bug nor adds a feature
- `perf:` Code change that improves performance
- `test:` Adding missing tests or correcting existing tests
- `build:` Changes to build system or external dependencies
- `ci:` Changes to CI configuration files and scripts
- `chore:` Other changes that don't modify src or test files
- `revert:` Reverts a previous commit

## Commit Message Rules

- First line: type, optional scope, and description (max 72 chars)
- Description must be lowercase and not end with a period
- Optional body: blank line, then more detailed explanation
- Optional footer: blank line, then `BREAKING CHANGE:` or issue references

## Example Format

```bash
git commit -m "feat(auth): add oauth2 integration for google login" \
           -m "" \
           -m "Implements OAuth2 flow with Google as identity provider." \
           -m "Includes token refresh mechanism and secure storage." \
           -m "" \
           -m "Closes #123"
```

## Task-Specific Format

```bash
git commit -m "<type>: <what was accomplished in parent task>" \
           -m "" \
           -m "<detailed description if needed>" \
           -m "" \
           -m "Task: <task number> from <PRD filename>"
```