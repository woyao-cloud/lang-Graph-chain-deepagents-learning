"""Task runner for MyAgent.

Executes tasks using DeepAgents.
"""

from __future__ import annotations

import pickle
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from myagent.models import ExecutionResult, Task, TaskStatus

if TYPE_CHECKING:
    from myagent.config import MyAgentConfig


class Checkpoint:
    """Execution checkpoint for resume functionality."""

    def __init__(self, checkpoint_dir: Path):
        """Initialize checkpoint.

        Args:
            checkpoint_dir: Directory to store checkpoints
        """
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        task_name: str,
        phase_index: int,
        state: dict[str, Any],
    ) -> str:
        """Save checkpoint.

        Args:
            task_name: Task name
            phase_index: Phase index
            state: State to save

        Returns:
            Checkpoint ID
        """
        checkpoint_id = f"{phase_index}_{task_name}_{int(time.time())}"
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.pkl"

        with open(checkpoint_file, "wb") as f:
            pickle.dump({
                "task_name": task_name,
                "phase_index": phase_index,
                "state": state,
                "timestamp": time.time(),
            }, f)

        return checkpoint_id

    def load(self, checkpoint_id: str) -> dict[str, Any] | None:
        """Load checkpoint.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            State dict or None if not found
        """
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.pkl"
        if not checkpoint_file.exists():
            return None

        with open(checkpoint_file, "rb") as f:
            return pickle.load(f)

    def get_latest(self, task_name: str | None = None) -> str | None:
        """Get latest checkpoint.

        Args:
            task_name: Optional task name filter

        Returns:
            Latest checkpoint ID or None
        """
        checkpoints = list(self.checkpoint_dir.glob("*.pkl"))
        if not checkpoints:
            return None

        # Sort by modification time
        checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        if task_name:
            for cp in checkpoints:
                if task_name in cp.stem:
                    return cp.stem
            return None

        return checkpoints[0].stem if checkpoints else None


class TaskRunner:
    """Executes tasks with checkpoint support."""

    def __init__(self, config: "MyAgentConfig | None" = None):
        """Initialize task runner.

        Args:
            config: MyAgent configuration
        """
        self.config = config
        self.checkpoint: Checkpoint | None = None

        if config:
            self.checkpoint = Checkpoint(config.workflow.logs_dir / "checkpoints")

    def execute(
        self,
        task: Task,
        phase_index: int,
        context: dict[str, Any],
    ) -> ExecutionResult:
        """Execute a task.

        Args:
            task: Task to execute
            phase_index: Phase index
            context: Execution context

        Returns:
            ExecutionResult
        """
        start_time = time.time()

        # Check for checkpoint to resume
        if self.checkpoint:
            latest = self.checkpoint.get_latest(task.name)
            if latest:
                saved_state = self.checkpoint.load(latest)
                if saved_state:
                    # Resume from checkpoint
                    context = {**saved_state["state"], **context}

        try:
            # Execute task
            # In real implementation, this would use DeepAgents
            result = self._do_execute(task, context)

            end_time = time.time()

            # Save checkpoint on success
            if self.checkpoint:
                self.checkpoint.save(task.name, phase_index, {
                    "status": "completed",
                    "result": result,
                })

            return ExecutionResult(
                task_name=task.name,
                agent_name=",".join(task.owner) if task.owner else "unknown",
                success=True,
                output=str(result),
                duration_seconds=end_time - start_time,
            )

        except Exception as e:
            end_time = time.time()

            # Save checkpoint on failure
            if self.checkpoint:
                self.checkpoint.save(task.name, phase_index, {
                    "status": "failed",
                    "error": str(e),
                })

            return ExecutionResult(
                task_name=task.name,
                agent_name=",".join(task.owner) if task.owner else "unknown",
                success=False,
                error=str(e),
                duration_seconds=end_time - start_time,
            )

    def _do_execute(
        self,
        task: Task,
        context: dict[str, Any],
    ) -> Any:
        """Actually execute the task.

        This is a placeholder that would use DeepAgents in real implementation.

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Execution result
        """
        # Simulate execution
        import time
        time.sleep(0.1)

        return {
            "task": task.name,
            "status": "completed",
            "context": context,
        }

    def resume(self, checkpoint_id: str | None = None) -> ExecutionResult | None:
        """Resume from checkpoint.

        Args:
            checkpoint_id: Checkpoint ID (latest if None)

        Returns:
            ExecutionResult or None
        """
        if not self.checkpoint:
            return None

        if checkpoint_id is None:
            checkpoint_id = self.checkpoint.get_latest()

        if not checkpoint_id:
            return None

        saved_state = self.checkpoint.load(checkpoint_id)
        if not saved_state:
            return None

        # Re-execute with saved state
        # This is a simplified resume - real implementation would be more complex
        return ExecutionResult(
            task_name=saved_state["task_name"],
            agent_name="unknown",
            success=saved_state["state"].get("status") == "completed",
            output=str(saved_state["state"]),
            error=saved_state["state"].get("error"),
        )
