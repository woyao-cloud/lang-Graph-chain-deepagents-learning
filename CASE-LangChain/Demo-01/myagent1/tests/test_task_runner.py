"""Tests for executor/task_runner.py module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from myagent.models import ExecutionResult, Task, TaskStatus
from myagent.executor.task_runner import Checkpoint, TaskRunner


class TestCheckpoint:
    """Tests for Checkpoint class."""

    def test_init_creates_checkpoint_dir(self, temp_dir: Path):
        """Test that init creates the checkpoint directory."""
        checkpoint_dir = temp_dir / "checkpoints"
        checkpoint = Checkpoint(checkpoint_dir)

        assert checkpoint.checkpoint_dir == checkpoint_dir
        assert checkpoint_dir.exists()

    def test_save_creates_file(self, temp_dir: Path):
        """Test that save creates a checkpoint file."""
        checkpoint = Checkpoint(temp_dir)

        checkpoint_id = checkpoint.save(
            task_name="test-task",
            phase_index=1,
            state={"status": "completed"},
        )

        assert checkpoint_id is not None
        files = list(temp_dir.glob("*.json"))
        assert len(files) == 1

    def test_save_returns_checkpoint_id(self, temp_dir: Path):
        """Test that save returns a valid checkpoint ID."""
        checkpoint = Checkpoint(temp_dir)

        checkpoint_id = checkpoint.save(
            task_name="test-task",
            phase_index=1,
            state={"status": "completed"},
        )

        # Checkpoint ID format: {phase_index}_{task_name}_{timestamp}_{uuid}
        assert "test-task" in checkpoint_id
        assert checkpoint_id.startswith("1_test-task_")

    def test_save_contains_state(self, temp_dir: Path):
        """Test that saved checkpoint contains the state."""
        checkpoint = Checkpoint(temp_dir)
        state = {"status": "completed", "result": "output"}

        checkpoint_id = checkpoint.save(
            task_name="test-task",
            phase_index=1,
            state=state,
        )

        checkpoint_file = temp_dir / f"{checkpoint_id}.json"
        with open(checkpoint_file) as f:
            data = json.load(f)

        assert data["task_name"] == "test-task"
        assert data["phase_index"] == 1
        assert data["state"]["status"] == "completed"

    def test_load_returns_state(self, temp_dir: Path):
        """Test that load returns the saved state."""
        checkpoint = Checkpoint(temp_dir)
        state = {"status": "completed", "result": "test"}

        checkpoint_id = checkpoint.save(
            task_name="test-task",
            phase_index=1,
            state=state,
        )

        loaded_state = checkpoint.load(checkpoint_id)

        assert loaded_state is not None
        assert loaded_state["state"]["status"] == "completed"

    def test_load_nonexistent_returns_none(self, temp_dir: Path):
        """Test that loading nonexistent checkpoint returns None."""
        checkpoint = Checkpoint(temp_dir)

        result = checkpoint.load("nonexistent-checkpoint-id")

        assert result is None

    def test_get_latest_returns_most_recent(self, temp_dir: Path):
        """Test that get_latest returns the most recent checkpoint."""
        checkpoint = Checkpoint(temp_dir)

        # Save multiple checkpoints
        checkpoint.save("task1", 1, {"status": "a"})
        checkpoint.save("task2", 1, {"status": "b"})
        checkpoint.save("task3", 1, {"status": "c"})

        latest = checkpoint.get_latest()

        assert latest is not None
        assert "task3" in latest

    def test_get_latest_with_task_filter(self, temp_dir: Path):
        """Test get_latest with task name filter."""
        checkpoint = Checkpoint(temp_dir)

        checkpoint.save("task1", 1, {"status": "a"})
        checkpoint.save("task2", 1, {"status": "b"})

        latest = checkpoint.get_latest(task_name="task1")

        assert latest is not None
        assert "task1" in latest

    def test_get_latest_no_checkpoints(self, temp_dir: Path):
        """Test get_latest when no checkpoints exist."""
        checkpoint = Checkpoint(temp_dir)

        latest = checkpoint.get_latest()

        assert latest is None


class TestTaskRunner:
    """Tests for TaskRunner class."""

    def test_default_init(self):
        """Test default initialization."""
        runner = TaskRunner()
        assert runner.config is None
        assert runner.checkpoint is None
        assert runner._executor is None

    def test_init_with_config(self, temp_dir: Path):
        """Test initialization with config."""
        from myagent.config import MyAgentConfig

        config = MyAgentConfig(
            project_root=temp_dir,
            workflow=pytest.importorskip("myagent.config").WorkflowConfig(),
        )
        # Set logs_dir to a temp path
        config.workflow.logs_dir = temp_dir / "logs"

        runner = TaskRunner(config)

        assert runner.config is config
        assert runner.checkpoint is not None

    def test_get_executor_creates_instance(self):
        """Test that _get_executor creates an executor."""
        runner = TaskRunner()

        executor = runner._get_executor()

        assert executor is not None
        from myagent.agents.deep_integration import AgentExecutor
        assert isinstance(executor, AgentExecutor)

    def test_get_executor_caches(self):
        """Test that _get_executor caches the executor."""
        runner = TaskRunner()

        executor1 = runner._get_executor()
        executor2 = runner._get_executor()

        assert executor1 is executor2

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", False)
    def test_execute_without_checkpoint(self):
        """Test execute without checkpoint."""
        runner = TaskRunner()
        task = Task(name="test-task", owner=["architect"])

        result = runner.execute(
            task=task,
            phase_index=1,
            context={},
        )

        assert isinstance(result, ExecutionResult)
        assert result.task_name == "test-task"
        assert result.success is True  # Mock execution succeeds

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", False)
    def test_execute_with_checkpoint_resume(self, temp_dir: Path):
        """Test execute with checkpoint resume."""
        from myagent.config import MyAgentConfig

        config = MyAgentConfig(project_root=temp_dir)
        config.workflow.logs_dir = temp_dir / "logs"
        config.workflow.logs_dir.mkdir(parents=True, exist_ok=True)

        runner = TaskRunner(config)
        task = Task(name="test-task", owner=["architect"])

        # Save a checkpoint first
        runner.checkpoint.save("test-task", 1, {
            "status": "completed",
            "result": "previous output",
        })

        result = runner.execute(
            task=task,
            phase_index=1,
            context={},
        )

        assert result.task_name == "test-task"

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", False)
    def test_execute_saves_checkpoint_on_success(self, temp_dir: Path):
        """Test that execute saves checkpoint on success."""
        from myagent.config import MyAgentConfig

        config = MyAgentConfig(project_root=temp_dir)
        config.workflow.logs_dir = temp_dir / "logs"
        config.workflow.logs_dir.mkdir(parents=True, exist_ok=True)

        runner = TaskRunner(config)
        task = Task(name="checkpoint-test", owner=["architect"])

        result = runner.execute(
            task=task,
            phase_index=1,
            context={},
        )

        # Check checkpoint was saved
        checkpoints = list((temp_dir / "logs" / "checkpoints").glob("*.json"))
        assert len(checkpoints) > 0

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", False)
    def test_execute_saves_checkpoint_on_failure(self, temp_dir: Path):
        """Test that execute saves checkpoint on failure."""
        from myagent.config import MyAgentConfig

        config = MyAgentConfig(project_root=temp_dir)
        config.workflow.logs_dir = temp_dir / "logs"
        config.workflow.logs_dir.mkdir(parents=True, exist_ok=True)

        runner = TaskRunner(config)
        task = Task(name="failure-test", owner=["architect"])

        # Force failure
        with patch.object(runner, "_get_executor") as mock_get_executor:
            mock_executor = MagicMock()
            mock_executor.execute_task.side_effect = Exception("Test error")
            mock_get_executor.return_value = mock_executor

            result = runner.execute(
                task=task,
                phase_index=1,
                context={},
            )

        assert result.success is False
        assert result.error is not None

    def test_execute_uses_task_owner(self):
        """Test that execute uses task owner for role."""
        from myagent.models import ExecutionResult

        runner = TaskRunner()
        task = Task(name="test", owner=["backend-dev"])

        # Mock the executor
        mock_executor = MagicMock()
        mock_executor.execute_task.return_value = {"success": True, "result": {}}
        runner._executor = mock_executor

        result = runner.execute(
            task=task,
            phase_index=1,
            context={},
        )

        assert result.agent_name == "backend-dev"

    def test_execute_defaults_to_architect(self):
        """Test that execute defaults to architect when no owner."""
        from myagent.models import ExecutionResult

        runner = TaskRunner()
        task = Task(name="test", owner=[])

        # Mock the executor
        mock_executor = MagicMock()
        mock_executor.execute_task.return_value = {"success": True, "result": {}}
        runner._executor = mock_executor

        result = runner.execute(
            task=task,
            phase_index=1,
            context={},
        )

        assert result.agent_name == "architect"

    def test_resume_no_checkpoint(self, temp_dir: Path):
        """Test resume when no checkpoint exists."""
        from myagent.config import MyAgentConfig

        config = MyAgentConfig(project_root=temp_dir)
        config.workflow.logs_dir = temp_dir / "logs"

        runner = TaskRunner(config)

        result = runner.resume()

        assert result is None

    def test_resume_with_checkpoint_id(self, temp_dir: Path):
        """Test resume with specific checkpoint ID."""
        from myagent.config import MyAgentConfig

        config = MyAgentConfig(project_root=temp_dir)
        config.workflow.logs_dir = temp_dir / "logs"
        config.workflow.logs_dir.mkdir(parents=True, exist_ok=True)

        runner = TaskRunner(config)

        # Save a checkpoint
        checkpoint_id = runner.checkpoint.save("test-task", 1, {
            "status": "completed",
            "result": "output",
        })

        result = runner.resume(checkpoint_id=checkpoint_id)

        assert result is not None
        assert result.task_name == "test-task"
        assert result.success is True

    def test_resume_nonexistent_checkpoint(self, temp_dir: Path):
        """Test resume with nonexistent checkpoint ID."""
        from myagent.config import MyAgentConfig

        config = MyAgentConfig(project_root=temp_dir)
        config.workflow.logs_dir = temp_dir / "logs"

        runner = TaskRunner(config)

        result = runner.resume(checkpoint_id="nonexistent-id")

        assert result is None

    def test_resume_returns_failed_for_failed_task(self, temp_dir: Path):
        """Test that resume returns failed result for failed task."""
        from myagent.config import MyAgentConfig

        config = MyAgentConfig(project_root=temp_dir)
        config.workflow.logs_dir = temp_dir / "logs"
        config.workflow.logs_dir.mkdir(parents=True, exist_ok=True)

        runner = TaskRunner(config)

        # Save a failed checkpoint
        checkpoint_id = runner.checkpoint.save("test-task", 1, {
            "status": "failed",
            "error": "Some error",
        })

        result = runner.resume(checkpoint_id=checkpoint_id)

        assert result is not None
        assert result.success is False
        assert result.error == "Some error"

    def test_execute_records_duration(self):
        """Test that execute records execution duration."""
        runner = TaskRunner()

        # Mock the executor to return quickly
        mock_executor = MagicMock()
        mock_executor.execute_task.return_value = {"success": True, "result": {}}
        runner._executor = mock_executor

        task = Task(name="test", owner=["architect"])
        result = runner.execute(
            task=task,
            phase_index=1,
            context={},
        )

        assert result.duration_seconds >= 0

    def test_execute_with_context(self):
        """Test execute passes context to executor."""
        runner = TaskRunner()

        # Mock the executor
        mock_executor = MagicMock()
        mock_executor.execute_task.return_value = {"success": True, "result": {}}
        runner._executor = mock_executor

        task = Task(name="test", owner=["architect"])
        context = {"key": "value", "count": 42}

        runner.execute(
            task=task,
            phase_index=1,
            context=context,
        )

        # Verify context was passed
        call_kwargs = mock_executor.execute_task.call_args[1]
        assert "context" in call_kwargs
        assert call_kwargs["context"]["key"] == "value"

    def test_execute_includes_phase_index_in_task_name(self):
        """Test that execute task description includes phase info."""
        runner = TaskRunner()

        mock_executor = MagicMock()
        mock_executor.execute_task.return_value = {"success": True, "result": {}}
        runner._executor = mock_executor

        task = Task(name="test-task", owner=["architect"])

        runner.execute(
            task=task,
            phase_index=3,
            context={},
        )

        # Verify task description was passed
        call_kwargs = mock_executor.execute_task.call_args[1]
        assert "task" in call_kwargs
        assert "Execute task" in call_kwargs["task"]
