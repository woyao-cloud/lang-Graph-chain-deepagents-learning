"""Progress tracker for MyAgent.

Tracks execution progress and generates status reports.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from myagent.models import Phase, PhaseStatus, ProgressInfo, TaskStatus

if TYPE_CHECKING:
    pass


@dataclass
class PhaseProgress:
    """Progress for a single phase."""
    phase: Phase
    status: PhaseStatus = PhaseStatus.PENDING
    task_progress: dict[str, float] = field(default_factory=dict)  # task_name -> percent
    task_statuses: dict[str, TaskStatus] = field(default_factory=dict)
    start_time: float | None = None
    end_time: float | None = None
    current_task: str | None = None


@dataclass
class ProgressTracker:
    """Tracks overall execution progress."""
    phases: dict[int, PhaseProgress] = field(default_factory=dict)
    _start_time: float = field(default_factory=time.time)

    def start_phase(self, phase: Phase) -> None:
        """Start tracking a phase.

        Args:
            phase: Phase to track
        """
        self.phases[phase.index] = PhaseProgress(
            phase=phase,
            status=PhaseStatus.IN_PROGRESS,
            start_time=time.time(),
        )

        # Initialize task progress
        for task in phase.tasks:
            self.phases[phase.index].task_progress[task.name] = 0.0
            self.phases[phase.index].task_statuses[task.name] = TaskStatus.PENDING

    def update_task(
        self,
        phase_index: int,
        task_name: str,
        progress: float,
        status: TaskStatus | None = None,
    ) -> None:
        """Update task progress.

        Args:
            phase_index: Phase index
            task_name: Task name
            progress: Progress percentage (0-100)
            status: Optional task status
        """
        if phase_index in self.phases:
            self.phases[phase_index].task_progress[task_name] = progress
            if status:
                self.phases[phase_index].task_statuses[task_name] = status
            self.phases[phase_index].current_task = task_name

    def complete_phase(self, phase_index: int, success: bool = True) -> None:
        """Mark phase as complete.

        Args:
            phase_index: Phase index
            success: Whether phase completed successfully
        """
        if phase_index in self.phases:
            self.phases[phase_index].status = (
                PhaseStatus.COMPLETED if success else PhaseStatus.FAILED
            )
            self.phases[phase_index].end_time = time.time()

            # Mark all tasks as complete
            for task_name in self.phases[phase_index].task_progress:
                self.phases[phase_index].task_progress[task_name] = 100.0

    def get_phase_progress(self, phase_index: int) -> PhaseProgress | None:
        """Get progress for a phase.

        Args:
            phase_index: Phase index

        Returns:
            PhaseProgress or None
        """
        return self.phases.get(phase_index)

    def get_overall_progress(self) -> float:
        """Get overall progress percentage.

        Returns:
            Progress percentage (0-100)
        """
        if not self.phases:
            return 0.0

        total_progress = 0.0
        for phase_progress in self.phases.values():
            if phase_progress.task_progress:
                phase_avg = sum(phase_progress.task_progress.values()) / len(phase_progress.task_progress)
                total_progress += phase_avg
            else:
                total_progress += 100.0 if phase_progress.status == PhaseStatus.COMPLETED else 0.0

        return total_progress / len(self.phases) if self.phases else 0.0

    def get_progress_info(self) -> list[ProgressInfo]:
        """Get progress info for all tasks.

        Returns:
            List of ProgressInfo
        """
        info: list[ProgressInfo] = []

        for phase_progress in self.phases.values():
            phase = phase_progress.phase

            for task in phase.tasks:
                progress = phase_progress.task_progress.get(task.name, 0.0)
                status = phase_progress.task_statuses.get(task.name, TaskStatus.PENDING)
                duration = 0.0

                if phase_progress.start_time:
                    end = phase_progress.end_time or time.time()
                    duration = end - phase_progress.start_time

                info.append(ProgressInfo(
                    name=f"{phase.name} / {task.name}",
                    progress_percent=progress,
                    status=status.value,
                    agent=", ".join(task.owner) if task.owner else None,
                    duration_seconds=duration,
                ))

        return info

    def format_progress_bar(self, progress: float, width: int = 30) -> str:
        """Format progress as ASCII bar.

        Args:
            progress: Progress percentage
            width: Bar width in characters

        Returns:
            Progress bar string
        """
        filled = int(width * progress / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {progress:.1f}%"

    def get_summary(self) -> str:
        """Get progress summary.

        Returns:
            Summary string
        """
        lines = [
            "# 进度追踪",
            "",
        ]

        for phase_progress in self.phases.values():
            phase = phase_progress.phase
            lines.append(f"## {phase.name}")

            status_icon = {
                PhaseStatus.PENDING: "⏳",
                PhaseStatus.IN_PROGRESS: "🔄",
                PhaseStatus.COMPLETED: "✅",
                PhaseStatus.FAILED: "❌",
                PhaseStatus.SKIPPED: "⏭️",
            }.get(phase_progress.status, "❓")

            lines.append(f"状态: {status_icon} {phase_progress.status.value}")

            for task in phase.tasks:
                progress = phase_progress.task_progress.get(task.name, 0.0)
                bar = self.format_progress_bar(progress)
                lines.append(f"  - {task.name}: {bar}")

            lines.append("")

        overall = self.get_overall_progress()
        lines.append(f"总体进度: {self.format_progress_bar(overall)}")

        return "\n".join(lines)
