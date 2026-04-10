# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MyAgent** is an automated code generation system with human-in-the-loop capabilities, inspired by Claude Code. It uses workflow-driven multi-agent orchestration to deliver end-to-end engineering projects.

## Commands

```bash
# Install dependencies
cd D:/python-projects/langchain/CASE-LangChain/Demo-01/myagent1
pip install -r requirements.txt

# Initialize a new project
myagent init --name <project-name>

# Run workflow phases
myagent run --phase <plan|execute> [--parallel] [--watch] [--resume]

# Confirm planning
myagent confirm --file PLANNING.md [--revise]

# View status and logs
myagent status [--live]
myagent logs --agent <agent-name> [--follow]

# Human-in-the-loop interventions
myagent skip --task <task-name>
myagent rollback --task <task-name>
myagent approve --operation <operation-id>
```

## Architecture

### Core Modules (8 Functional Areas)

```
myagent/
├── workflow/           # FR-WF-001: workflow.md parsing → DAG construction
├── planner/            # FR-PLAN-001: PLANNING.md generation with task decomposition
├── agents/             # FR-AGENT-001: Sub-Agent instantiation and routing
│   └── roles/          # Role definitions: architect, backend-dev, frontend-dev, qa-engineer
├── executor/           # FR-EXEC-001: Task execution with tool calling
├── progress/           # FR-PROGRESS-001: Real-time progress tracking
├── hitl/               # FR-HITL-001: Human-in-the-loop pause/intervention
├── quality/            # FR-QA-001: Lint, test, schema validation gates
└── vcs/                # FR-VCS-001: Git branch creation, commit, PR
```

### Configuration Files

- **workflow.md** - Defines phases, tasks, dependencies, parallel execution marks, quality gates
- **agent.md** - Defines roles (architect, backend-dev, frontend-dev, qa-engineer) and routing rules

### Data Flow

```
workflow.md + agent.md → Main Agent (Supervisor) → PLANNING.md (human confirmed)
    → Sub-Agent调度 (parallel/sequential) → Quality Gates → STATUS.md + LOGS/
```

### Key Design Patterns

- **DAG-based scheduling**: Tasks form a directed acyclic graph; parallel tasks are auto-detected
- **Human-in-the-loop**: Planning phase pauses for human confirmation; dangerous operations require approval
- **Context isolation**: Each Sub-Agent runs in isolated sandbox environment
- **State persistence**: Checkpoint-based resume for interrupted execution

## Project Structure

```
myagent1/
├── requirments/         # Requirements documentation
│   ├── README.md
│   └── SPEC.md          # Full specification (834 lines)
├── src/                 # Source code (to be implemented)
├── tests/               # Unit and integration tests
├── LOGS/                # Execution logs (generated)
├── STATUS.md            # Execution status (generated)
└── PLANNING.md          # Generated planning documents
```

## Conventions

- Use immutable data patterns (create new objects, never mutate)
- Files should be 200-400 lines; 800 max
- Validate all input at system boundaries
- Comprehensive error handling at every level
- See `requirments/SPEC.md` for full requirements including 8 use cases (UC-1 through UC-8)
