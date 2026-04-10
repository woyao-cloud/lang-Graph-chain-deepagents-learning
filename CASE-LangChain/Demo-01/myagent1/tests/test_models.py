"""Tests for models.py module."""

from __future__ import annotations

from pathlib import Path

import pytest

from myagent.models import (
    AgentRegistryModel,
    AgentRole,
    ExecutionResult,
    Phase,
    PhaseStatus,
    PlanningDocument,
    ProgressInfo,
    QualityGateResult,
    RoutingRule,
    SubTask,
    Task,
    TaskMode,
    TaskStatus,
    TaskTree,
    VCSCommit,
    WorkflowModel,
)


class TestEnums:
    """Tests for enum classes."""

    def test_phase_status_values(self):
        """Test PhaseStatus enum values."""
        assert PhaseStatus.PENDING.value == "pending"
        assert PhaseStatus.IN_PROGRESS.value == "in_progress"
        assert PhaseStatus.COMPLETED.value == "completed"
        assert PhaseStatus.FAILED.value == "failed"
        assert PhaseStatus.SKIPPED.value == "skipped"

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.SKIPPED.value == "skipped"

    def test_task_mode_values(self):
        """Test TaskMode enum values."""
        assert TaskMode.PARALLEL.value == "parallel"
        assert TaskMode.SEQUENTIAL.value == "sequential"


class TestTask:
    """Tests for Task dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        task = Task(name="Test Task")
        assert task.name == "Test Task"
        assert task.parallel is False
        assert task.owner == []
        assert task.status == TaskStatus.PENDING
        assert task.depends_on == []

    def test_init_with_params(self):
        """Test initialization with parameters."""
        task = Task(
            name="API Task",
            parallel=True,
            owner=["backend-dev"],
            status=TaskStatus.IN_PROGRESS,
            depends_on=["auth"],
        )
        assert task.parallel is True
        assert task.owner == ["backend-dev"]
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.depends_on == ["auth"]

    def test_post_init_string_to_bool(self):
        """Test that post_init converts string to bool."""
        task = Task(name="Test", parallel="true")
        assert task.parallel is True

        task2 = Task(name="Test", parallel="false")
        assert task2.parallel is False

    def test_post_init_string_owner(self):
        """Test that post_init converts string owner to list."""
        task = Task(name="Test", owner="a, b, c")
        assert task.owner == ["a", "b", "c"]

    def test_post_init_preserves_list_owner(self):
        """Test that post_init preserves list owner."""
        task = Task(name="Test", owner=["a", "b"])
        assert task.owner == ["a", "b"]


class TestPhase:
    """Tests for Phase dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        phase = Phase(name="Planning", index=1)
        assert phase.name == "Planning"
        assert phase.index == 1
        assert phase.depends_on == []
        assert phase.tasks == []
        assert phase.status == PhaseStatus.PENDING

    def test_init_with_params(self):
        """Test initialization with parameters."""
        phase = Phase(
            name="Implementation",
            index=2,
            depends_on=["Planning"],
            tasks=[Task(name="Task1")],
            status=PhaseStatus.IN_PROGRESS,
        )
        assert phase.depends_on == ["Planning"]
        assert len(phase.tasks) == 1
        assert phase.status == PhaseStatus.IN_PROGRESS


class TestWorkflowModel:
    """Tests for WorkflowModel dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        model = WorkflowModel()
        assert model.phases == []
        assert model.rules == []
        assert model.raw_content == ""


class TestAgentRole:
    """Tests for AgentRole dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        role = AgentRole(name="test", description="Test role")
        assert role.name == "test"
        assert role.description == "Test role"
        assert role.tools == []
        assert role.model is None

    def test_init_with_params(self):
        """Test initialization with parameters."""
        role = AgentRole(
            name="backend-dev",
            description="Backend developer",
            tools=["read_file", "write_file"],
            model="claude-sonnet-4-6",
        )
        assert role.tools == ["read_file", "write_file"]
        assert role.model == "claude-sonnet-4-6"


class TestRoutingRule:
    """Tests for RoutingRule dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        rule = RoutingRule(module="api", agents=["backend-dev"])
        assert rule.module == "api"
        assert rule.agents == ["backend-dev"]
        assert rule.mode == TaskMode.PARALLEL

    def test_init_with_sequential(self):
        """Test initialization with sequential mode."""
        rule = RoutingRule(
            module="auth",
            agents=["security"],
            mode=TaskMode.SEQUENTIAL,
        )
        assert rule.mode == TaskMode.SEQUENTIAL


class TestAgentRegistryModel:
    """Tests for AgentRegistryModel dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        model = AgentRegistryModel()
        assert model.roles == {}
        assert model.routing_rules == []


class TestSubTask:
    """Tests for SubTask dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        task = SubTask(name="Test", description="Test task")
        assert task.name == "Test"
        assert task.description == "Test task"
        assert task.assignee is None
        assert task.status == TaskStatus.PENDING
        assert task.children == []
        assert task.artifacts == []

    def test_init_with_params(self):
        """Test initialization with parameters."""
        task = SubTask(
            name="Test",
            description="Test task",
            assignee="developer",
            status=TaskStatus.COMPLETED,
            children=[SubTask(name="Child", description="Child task")],
            artifacts=["file1.py", "file2.py"],
        )
        assert task.assignee == "developer"
        assert task.status == TaskStatus.COMPLETED
        assert len(task.children) == 1
        assert task.artifacts == ["file1.py", "file2.py"]


class TestTaskTree:
    """Tests for TaskTree dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        root = SubTask(name="root", description="Root")
        tree = TaskTree(root=root)
        assert tree.root is root
        assert tree.tech_stack == {}
        assert tree.file_structure == []
        assert tree.api_contracts == []
        assert tree.risks == []


class TestPlanningDocument:
    """Tests for PlanningDocument dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        root = SubTask(name="root", description="Root")
        tree = TaskTree(root=root)
        doc = PlanningDocument(
            title="Test",
            task_tree=tree,
            tech_stack={},
            file_structure=[],
            api_contracts=[],
            risks=[],
        )
        assert doc.title == "Test"
        assert doc.task_tree is tree
        assert doc.confirmed is False
        assert doc.path is None

    def test_init_with_params(self):
        """Test initialization with parameters."""
        root = SubTask(name="root", description="Root")
        tree = TaskTree(root=root)
        path = Path("/tmp/planning.md")
        doc = PlanningDocument(
            title="Test",
            task_tree=tree,
            tech_stack={"Python": "3.11"},
            file_structure=["src/main.py"],
            api_contracts=[{"name": "API"}],
            risks=["Risk 1"],
            confirmed=True,
            path=path,
        )
        assert doc.tech_stack == {"Python": "3.11"}
        assert doc.confirmed is True
        assert doc.path == path


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        result = ExecutionResult(
            task_name="test",
            agent_name="architect",
            success=True,
        )
        assert result.task_name == "test"
        assert result.agent_name == "architect"
        assert result.success is True
        assert result.output == ""
        assert result.error is None
        assert result.tokens_used == 0
        assert result.duration_seconds == 0.0

    def test_init_with_params(self):
        """Test initialization with parameters."""
        result = ExecutionResult(
            task_name="test",
            agent_name="backend-dev",
            success=False,
            output="output text",
            error="error message",
            tokens_used=1000,
            duration_seconds=5.5,
        )
        assert result.success is False
        assert result.output == "output text"
        assert result.error == "error message"
        assert result.tokens_used == 1000
        assert result.duration_seconds == 5.5


class TestProgressInfo:
    """Tests for ProgressInfo dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        info = ProgressInfo(
            name="test",
            progress_percent=50.0,
            status="in_progress",
        )
        assert info.name == "test"
        assert info.progress_percent == 50.0
        assert info.status == "in_progress"
        assert info.agent is None
        assert info.duration_seconds == 0.0

    def test_init_with_params(self):
        """Test initialization with parameters."""
        info = ProgressInfo(
            name="test",
            progress_percent=100.0,
            status="completed",
            agent="architect",
            duration_seconds=10.5,
        )
        assert info.agent == "architect"
        assert info.duration_seconds == 10.5


class TestQualityGateResult:
    """Tests for QualityGateResult dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        result = QualityGateResult(
            gate_type="lint",
            success=True,
        )
        assert result.gate_type == "lint"
        assert result.success is True
        assert result.file_path is None
        assert result.message == ""
        assert result.errors == []

    def test_init_with_params(self):
        """Test initialization with parameters."""
        result = QualityGateResult(
            gate_type="test",
            success=False,
            file_path=Path("tests/test_main.py"),
            message="Test failed",
            errors=["Error 1", "Error 2"],
        )
        assert result.success is False
        assert result.file_path == Path("tests/test_main.py")
        assert result.message == "Test failed"
        assert len(result.errors) == 2


class TestVCSCommit:
    """Tests for VCSCommit dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        commit = VCSCommit(
            branch="main",
            message="Initial commit",
        )
        assert commit.branch == "main"
        assert commit.message == "Initial commit"
        assert commit.files == []
        assert commit.author == "myagent"

    def test_init_with_params(self):
        """Test initialization with parameters."""
        commit = VCSCommit(
            branch="feature/new-feature",
            message="feat: add new feature",
            files=["src/main.py", "tests/test_main.py"],
            author="developer",
        )
        assert commit.branch == "feature/new-feature"
        assert len(commit.files) == 2
        assert commit.author == "developer"
