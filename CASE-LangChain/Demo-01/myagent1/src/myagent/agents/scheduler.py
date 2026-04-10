"""Agent scheduler for MyAgent.

Schedules and executes tasks using DeepAgents SubAgents.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from myagent.models import ExecutionResult, Phase, Task, TaskStatus

if TYPE_CHECKING:
    from myagent.config import MyAgentConfig


@dataclass
class ScheduledTask:
    """A task scheduled for execution."""
    task: Task
    phase: Phase
    agents: list[str]
    status: TaskStatus = TaskStatus.PENDING
    result: ExecutionResult | None = None
    start_time: float | None = None
    end_time: float | None = None


@dataclass
class ScheduleResult:
    """Result of scheduling multiple tasks."""
    results: list[ExecutionResult]
    total_duration: float
    success_count: int
    failure_count: int


class AgentScheduler:
    """Schedules and executes tasks using DeepAgents."""

    def __init__(self, config: "MyAgentConfig | None" = None):
        """Initialize agent scheduler.

        Args:
            config: MyAgent configuration
        """
        self.config = config
        self._scheduled_tasks: dict[str, ScheduledTask] = {}

    def schedule_parallel(
        self,
        tasks: list[Task],
        phase: Phase,
        agent_names: list[str],
    ) -> ScheduleResult:
        """Schedule tasks for parallel execution.

        Args:
            tasks: List of tasks to execute
            phase: Parent phase
            agent_names: List of agent names to use

        Returns:
            ScheduleResult
        """
        results: list[ExecutionResult] = []
        start_time = time.time()

        # Create scheduled tasks
        for task in tasks:
            scheduled = ScheduledTask(
                task=task,
                phase=phase,
                agents=agent_names,
            )
            self._scheduled_tasks[f"{phase.index}:{task.name}"] = scheduled

        # Execute in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = {}
            for task in tasks:
                future = executor.submit(
                    self._execute_task,
                    task,
                    phase,
                    agent_names,
                )
                futures[future] = task

            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(ExecutionResult(
                        task_name=task.name,
                        agent_name=",".join(agent_names),
                        success=False,
                        error=str(e),
                    ))

        end_time = time.time()
        total_duration = end_time - start_time

        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count

        return ScheduleResult(
            results=results,
            total_duration=total_duration,
            success_count=success_count,
            failure_count=failure_count,
        )

    def schedule_sequential(
        self,
        tasks: list[Task],
        phase: Phase,
        agent_names: list[str],
    ) -> ScheduleResult:
        """Schedule tasks for sequential execution.

        Args:
            tasks: List of tasks to execute
            phase: Parent phase
            agent_names: List of agent names to use

        Returns:
            ScheduleResult
        """
        results: list[ExecutionResult] = []
        start_time = time.time()

        for task in tasks:
            scheduled = ScheduledTask(
                task=task,
                phase=phase,
                agents=agent_names,
            )
            self._scheduled_tasks[f"{phase.index}:{task.name}"] = scheduled

            # Execute sequentially
            try:
                result = self._execute_task(task, phase, agent_names)
                results.append(result)
            except Exception as e:
                results.append(ExecutionResult(
                    task_name=task.name,
                    agent_name=",".join(agent_names),
                    success=False,
                    error=str(e),
                ))

        end_time = time.time()
        total_duration = end_time - start_time

        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count

        return ScheduleResult(
            results=results,
            total_duration=total_duration,
            success_count=success_count,
            failure_count=failure_count,
        )

    def _execute_task(
        self,
        task: Task,
        phase: Phase,
        agent_names: list[str],
    ) -> ExecutionResult:
        """Execute a single task.

        Args:
            task: Task to execute
            phase: Parent phase
            agent_names: Agent names to use

        Returns:
            ExecutionResult
        """
        start_time = time.time()

        # Update status
        key = f"{phase.index}:{task.name}"
        if key in self._scheduled_tasks:
            self._scheduled_tasks[key].status = TaskStatus.IN_PROGRESS
            self._scheduled_tasks[key].start_time = start_time

        # Simulate task execution
        # In real implementation, this would use DeepAgents
        time.sleep(0.1)  # Simulate some work

        # For now, return a mock result
        end_time = time.time()

        if key in self._scheduled_tasks:
            self._scheduled_tasks[key].status = TaskStatus.COMPLETED
            self._scheduled_tasks[key].end_time = end_time

        return ExecutionResult(
            task_name=task.name,
            agent_name=",".join(agent_names),
            success=True,
            output=f"Task '{task.name}' completed by {', '.join(agent_names)}",
            duration_seconds=end_time - start_time,
        )

    def get_task_status(self, phase_index: int, task_name: str) -> TaskStatus | None:
        """Get status of a scheduled task.

        Args:
            phase_index: Phase index
            task_name: Task name

        Returns:
            TaskStatus or None if not found
        """
        key = f"{phase_index}:{task_name}"
        if key in self._scheduled_tasks:
            return self._scheduled_tasks[key].status
        return None

    def get_scheduled_tasks(self) -> dict[str, ScheduledTask]:
        """Get all scheduled tasks.

        Returns:
            Dict of task_key -> ScheduledTask
        """
        return self._scheduled_tasks.copy()

    def clear(self) -> None:
        """Clear all scheduled tasks."""
        self._scheduled_tasks.clear()
