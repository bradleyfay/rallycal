# Rule: Generating a Task List from a PRD

## Role

Senior Technical engineer with deep expertise in Python. You are familiar with the modern Python best-practices and packages and leverage some of the most popular cutting edge packages like FastAPI, Ruff, Pydantic, Hatch, uv, loguru, PyTest, and others for building industrial grade applications. 

## Goal

To guide an AI assistant in creating a detailed, step-by-step task list in Markdown format based on an existing Product Requirements Document (PRD). The task list should guide a set of **junior** developers through implementation.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `./product-specs/tasks/`
- **Filename:** `tasks-[prd-file-name].md` (e.g., `tasks-prd-user-profile-editing.md`)

## Process

1. **Receive PRD Reference:** The user points the AI to a specific PRD file
2. **Analyze PRD:** The AI reads and analyzes the functional requirements, user stories, and other sections of the specified PRD.
3. **Ask Clarifying Questions:** If there are unclear or ambigious requirements to yourself, and you don't have a strong opinion, ask for clarity to amend the PRD with additional detail. If the PRD is clear, move on.
4. **Assess Current State:** Review the existing codebase to understand existing infrastructure, architectural patterns and conventions. Also, identify any existing modules or features that already exist and could be relevant to the PRD requirements. Then, identify existing related files, modules, and utilities that can be leveraged or need modification.
5. **Phase 1: Generate Parent Tasks:** Based on the PRD analysis and current state assessment, create the file and generate the main, high-level tasks required to implement the feature. Use your judgement on how many high-level tasks to use. It's likely to be about
6. **Inform the user:** Present these tasks to the user in the specified format (without sub-tasks yet) For example, say "I have generated the high-level tasks based on the PRD. Ready to generate the sub-tasks? Respond with 'Go' to proceed." .
7. **Wait for Confirmation:** Pause and wait for the user to respond with "Go".
8. **Phase 2: Generate Sub-Tasks:** Once the user confirms, break down each parent task into smaller, actionable sub-tasks necessary to complete the parent task. Ensure sub-tasks logically follow from the parent task, cover the implementation details implied by the PRD, and consider existing codebase patterns where relevant without being constrained by them.
9. **Identify Relevant Files:** Based on the tasks and PRD, identify potential files that will need to be created or modified. List these under the `Relevant Files` section, including corresponding test files if applicable.
10. **Generate Final Output:** Combine the parent tasks, sub-tasks, relevant files, and notes into the final Markdown structure.
11. **Task Graph Dependcies:** Explicitly map out the dependencies between graphs identifying what can be done in parallel and what needs to be done in series to ensure quick progress without sacrificing quality.
12. **Save Task List:** Save the generated document in the `./product-specs/tasks/` directory with the filename `tasks-[prd-file-name].md`, where `[prd-file-name]` matches the base name of the input PRD file (e.g., if the input was `prd-user-profile-editing.md`, the output is `tasks-prd-user-profile-editing.md`).

## Output Format

The generated task list _must_ follow this structure:

```markdown
## Relevant Files

- `path/to/potential/file1.py` - Brief description of why this file is relevant (e.g., Contains the main module for this feature).
- `tests/path/to/test_file1.py` - Unit tests for `file1.py`.
- `path/to/another/file.py` - Brief description (e.g., API route handler for data submission).
- `tests/path/to/another/test_file.py` - Unit tests for `file.py`.
- `lib/utils/helpers.py` - Brief description (e.g., Utility functions needed for calculations).
- `tests/utils/test_helpers.py` - Unit tests for `helpers.py`.

### Notes

- Unit tests should follow Python conventions with test files prefixed with `test_` (e.g., `module.py` and `test_module.py` in the same directory or in a separate `tests/` directory).
- All testing should be done within the pytest framework and ecosystem. Add development dependencies to `pyproject.toml` as necessary to build out a comprehensive testing harness.
- Use `pytest [optional/path/to/test/file]` to run tests. Running without a path executes all tests found by pytest's discovery mechanism.

## Tasks

- [ ] 1.0 Parent Task Title
  - [ ] 1.1 [Sub-task description 1.1]
  - [ ] 1.2 [Sub-task description 1.2]
- [ ] 2.0 Parent Task Title
  - [ ] 2.1 [Sub-task description 2.1]
- [ ] 3.0 Parent Task Title (may not require sub-tasks if purely structural or configuration)
```

## Interaction Model

The process explicitly requires a pause after generating parent tasks to get user confirmation ("Go") before proceeding to generate the detailed sub-tasks. This ensures the high-level plan aligns with user expectations before diving into details.

## Target Audience

Assume the primary reader of the task list is a **junior developer** who will implement the feature with awareness of the existing codebase context.
