# Risk-Based Approval Gates

## Auto-Proceed (no approval needed)

Continue without user approval when:

- Implementation details within established patterns
- Test additions for existing functionality  
- Documentation updates
- Code formatting and style fixes
- Bug fixes that don't change APIs
- Dependency group contains only low-risk changes

## Manual Approval Required

Pause and request approval for:

- New architectural patterns
- External dependency additions
- Database schema changes
- API contract modifications
- Security-related changes
- Moving between dependency groups
- Breaking changes or BREAKING CHANGE commits

## Dependency Boundary Gates

Always pause for approval when:

- All tasks in a dependency group are complete
- Ready to move to next dependency group
- Critical path dependencies are about to change
- Architecture decisions affect multiple components
