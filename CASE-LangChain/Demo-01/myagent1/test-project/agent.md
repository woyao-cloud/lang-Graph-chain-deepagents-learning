# Agent Registry

## Roles

- architect: Architecture design, tech stack selection, PLANNING.md generation
- backend-dev: Python/Go/Java, business logic, API and database design
- frontend-dev: Vue/React, UI components, state management
- qa-engineer: Unit tests, integration tests, coverage validation

## Routing Rules

- Architecture Design -> architect (sequential)
- Core Module -> backend-dev + frontend-dev (parallel)
- Testing -> qa-engineer (sequential)
