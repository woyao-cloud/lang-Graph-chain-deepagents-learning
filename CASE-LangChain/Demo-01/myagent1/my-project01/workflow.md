# Workflow Configuration

## Phases

- [Phase 1] Requirements Analysis (depends: none)
  - Task: Architecture Design (parallel: false, owner: architect)

- [Phase 2] Core Module Development (depends: Phase 1)
  - Task: Module Development (parallel: true, owner: backend-dev, frontend-dev)

- [Phase 3] Integration and Testing (depends: Phase 2)
  - Task: Integration Testing (parallel: false, owner: qa-engineer)

## Rules

- Each phase output must pass automated checks (Lint/Test)
- Parallel tasks must use independent namespaces
- All changes must generate Commit Message and push to Feature Branch
