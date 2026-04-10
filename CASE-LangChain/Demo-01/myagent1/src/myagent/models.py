"""Data models for MyAgent."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class PhaseStatus(Enum):
    """Status of a phase."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskStatus(Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskMode(Enum):
    """Execution mode for a task."""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


@dataclass
class Task:
    """A task within a phase."""
    name: str
    parallel: bool = False
    owner: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    depends_on: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if isinstance(self.parallel, str):
            self.parallel = self.parallel.lower() in ("true", "1", "yes")
        if isinstance(self.owner, str):
            self.owner = [o.strip() for o in self.owner.split(",")]


@dataclass
class Phase:
    """A phase in the workflow."""
    name: str
    index: int
    depends_on: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    status: PhaseStatus = PhaseStatus.PENDING


@dataclass
class WorkflowModel:
    """Parsed workflow model."""
    phases: list[Phase] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    raw_content: str = ""


@dataclass
class AgentRole:
    """An agent role definition."""
    name: str
    description: str
    tools: list[str] = field(default_factory=list)
    model: str | None = None


@dataclass
class RoutingRule:
    """A routing rule mapping modules to agents."""
    module: str
    agents: list[str]
    mode: TaskMode = TaskMode.PARALLEL


@dataclass
class AgentRegistryModel:
    """Parsed agent registry model."""
    roles: dict[str, AgentRole] = field(default_factory=dict)
    routing_rules: list[RoutingRule] = field(default_factory=list)


@dataclass
class SubTask:
    """A subtask within a task decomposition."""
    name: str
    description: str
    assignee: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    children: list[SubTask] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)


@dataclass
class TaskTree:
    """Task decomposition tree."""
    root: SubTask
    tech_stack: dict[str, str] = field(default_factory=dict)
    file_structure: list[str] = field(default_factory=list)
    api_contracts: list[dict[str, Any]] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)


@dataclass
class PlanningDocument:
    """Planning document model."""
    title: str
    task_tree: TaskTree
    tech_stack: dict[str, str]
    file_structure: list[str]
    api_contracts: list[dict[str, Any]]
    risks: list[str]
    confirmed: bool = False
    path: Path | None = None


@dataclass
class ExecutionResult:
    """Result of a task execution."""
    task_name: str
    agent_name: str
    success: bool
    output: str = ""
    error: str | None = None
    tokens_used: int = 0
    duration_seconds: float = 0.0


@dataclass
class ProgressInfo:
    """Progress information for a task or phase."""
    name: str
    progress_percent: float
    status: str
    agent: str | None = None
    duration_seconds: float = 0.0


@dataclass
class QualityGateResult:
    """Result of a quality gate check."""
    gate_type: str  # "lint", "test", "schema"
    success: bool
    file_path: Path | None = None
    message: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass
class VCSCommit:
    """Version control commit information."""
    branch: str
    message: str
    files: list[str] = field(default_factory=list)
    author: str = "myagent"
