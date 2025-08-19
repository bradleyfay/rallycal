# Task List Management

Guidelines for managing task lists in markdown files to track progress on completing a PRD

## Parallel Execution Strategy

Before executing any tasks:
1. Read through the entire plan to identify task dependencies and parallel execution opportunities
2. Review **CLAUDE.md tech stack requirements** to ensure compliance with architectural patterns

- **Dependency Analysis**: Understand which task groups can run simultaneously vs. which require sequential execution
- **Batch Execution**: Execute all subtasks within a dependency group simultaneously  
- **Batch Approval**: Approve entire dependency groups, not individual subtasks
- **TodoWrite Integration**: Track multiple parallel work streams with TodoWrite tool
- **Smart Boundaries**: Pause for approval only at dependency boundaries and architectural decisions

## Continuous Validation

Follow [testing guidelines](protocols/testing-guidelines.md) and [approval gates](protocols/approval-gates.md) for quality control.

## Task Implementation

- **Dependency-Aware Execution:** Execute all subtasks within a dependency group simultaneously. Only pause for approval at dependency boundaries or architectural decisions.
- **Completion protocol:**  
  1. When you finish a **sub‑task**, immediately mark it as completed by changing `[ ]` to `[x]`.
  2. If **all** subtasks underneath a parent task are now `[x]`, follow this sequence:
     - **First**: Apply [testing guidelines](protocols/testing-guidelines.md) 
     - **TodoWrite Update**: Mark all completed subtasks and update relevant files list
     - **Only if all tests pass**: Stage changes (`git add .`)
     - **Clean up**: Remove any temporary files and temporary code before committing
     - **Commit**: Follow [git commit standards](protocols/git-commit-standards.md)

  3. Once all the subtasks are marked completed and changes have been committed, mark the **parent task** as completed.

## Task List Maintenance

1. **Update the task list as you work:**
   - Mark tasks and subtasks as completed (`[x]`) per the protocol above.
   - Add new tasks as they emerge.

2. **Maintain the "Relevant Files" section:**
   - List every file created or modified.
   - Give each file a one‑line description of its purpose.

## AI Instructions

When working with task lists, the AI must:

1. Follow [tech stack compliance](protocols/tech-stack-compliance.md) for all implementations.
2. Regularly update the task list file after finishing any significant work.
3. Follow the completion protocol:
   - Mark each finished **sub‑task** `[x]`.
   - Mark the **parent task** `[x]` once **all** its subtasks are `[x]`.
4. Add newly discovered tasks.
5. Keep "Relevant Files" accurate and up to date.
6. Before starting work, check which sub‑task is next.
7. Apply [approval gates](protocols/approval-gates.md) to determine when to pause for user approval.
8. Use TodoWrite tool to maintain visibility into parallel work streams.
9. Execute dependency groups in parallel when possible.
