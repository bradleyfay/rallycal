# Git Commit Command

Review all outstanding git changes, logically bundle them into related groups, and create conventional commits following best practices.

## Process

1. **Analyze Changes**
   - Run `git status` to see all modified, added, and deleted files
   - Run `git diff` to understand the nature of changes
   - Identify logical groupings of related changes

2. **Bundle Changes**
   - Group related files that represent a single feature, fix, or change
   - Separate infrastructure changes from application code
   - Keep documentation updates in their own commits
   - Isolate dependency updates from functional changes
   - Group test files with the code they test

3. **Create Conventional Commits**
   Use conventional commit format with these types:
   - `feat`: New features or capabilities
   - `fix`: Bug fixes
   - `docs`: Documentation only changes
   - `style`: Code style changes (formatting, missing semicolons, etc)
   - `refactor`: Code changes that neither fix bugs nor add features
   - `perf`: Performance improvements
   - `test`: Adding or updating tests
   - `build`: Changes to build system or dependencies
   - `ci`: Changes to CI/CD configuration
   - `chore`: Other changes that don't modify src or test files
   - `revert`: Reverts a previous commit

   Include scope when relevant: `feat(auth): add OAuth support`

4. **Handle Pre-commit Hooks**
   If pre-commit hooks are configured:
   - Stage files for each logical commit group
   - Attempt to commit
   - If pre-commit hooks fail:
     a. Analyze the error output to understand what failed
     b. Fix the issues based on the error messages:
        - **Formatting errors**: Run the formatter and re-stage
        - **Linting errors**: Fix the code issues and re-stage
        - **Type errors**: Correct type annotations and re-stage
        - **Import sorting**: Let the tool auto-fix or manually fix
        - **Security issues**: Address security concerns or add exceptions with justification
        - **Large files**: Consider using Git LFS or excluding the file
     c. Re-run the commit after fixes
     d. If hooks fail again after fixes, analyze why and either:
        - Make additional fixes
        - Skip specific hooks with `--no-verify` if the issue is a false positive (document why)
   - Continue until all commits succeed

5. **Commit Message Format**

   ```text
   <type>[optional scope]: <description>

   [optional body]

   [optional footer(s)]

   > Generated with [Claude Code](https://claude.ai/code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

   - Keep description under 50 characters
   - Use imperative mood ("add" not "added")
   - Don't capitalize first letter after colon
   - No period at end of description
   - Body explains what and why, not how
   - Footer includes breaking changes or issue references

6. **Best Practices**
   - Make atomic commits (one logical change per commit)
   - Don't mix refactoring with feature changes
   - Keep commits focused and easy to review
   - Test changes work before committing
   - Never commit:
     - Secrets, API keys, or passwords
     - Large binary files (unless using LFS)
     - Generated files that can be rebuilt
     - Personal IDE configurations (unless team-agreed)

7. **Error Recovery**
   If any step fails:
   - Save work with `git stash` if needed
   - Fix the underlying issue
   - Continue from where the process stopped
   - If commits get tangled, use `git reset --soft HEAD~n` to undo and retry

## Example Workflow

```bash
# 1. Check status
git status
git diff

# 2. Stage and commit first logical group
git add src/auth/*.py tests/test_auth.py
git commit -m "feat(auth): implement JWT authentication"

# If pre-commit fails with formatting:
ruff format src/auth/*.py tests/test_auth.py
git add src/auth/*.py tests/test_auth.py
git commit -m "feat(auth): implement JWT authentication"

# 3. Continue with next group
git add docs/API.md
git commit -m "docs: update API documentation for auth endpoints"

# 4. Final verification
git log --oneline -n 5
```

## Important Notes

- Always review changes before committing
- If unsure about grouping, prefer smaller commits over large ones
- Run tests locally before committing if test suite exists
- Check CI/CD will pass by running linters and formatters first
- When fixing pre-commit failures, understand what the tool is fixing and why
