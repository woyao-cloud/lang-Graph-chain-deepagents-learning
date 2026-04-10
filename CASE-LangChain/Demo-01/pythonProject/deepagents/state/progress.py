"""
Progress Tracker - 实时进度追踪
FR-PROGRESS-001: 进度追踪
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import time


@dataclass
class TaskProgress:
    """任务进度"""
    task_id: str
    task_name: str
    agent: str
    status: str  # "pending", "running", "completed", "failed", "skipped"
    progress: float  # 0-100
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration: float = 0.0
    error: Optional[str] = None


@dataclass
class PhaseProgress:
    """阶段进度"""
    phase_name: str
    status: str  # "pending", "running", "completed", "blocked"
    tasks: Dict[str, TaskProgress] = field(default_factory=dict)
    progress: float = 0.0


@dataclass
class SessionProgress:
    """会话进度"""
    session_id: str
    current_phase: int
    total_phases: int
    overall_progress: float = 0.0
    phases: Dict[str, PhaseProgress] = field(default_factory=dict)
    started_at: str = ""
    last_updated: str = ""


class ProgressTracker:
    """
    进度追踪器
    实时追踪任务和阶段进度
    """

    def __init__(self, project_name: str = "project"):
        self.project_name = project_name
        self.session_id = self._generate_session_id()
        self._progress: SessionProgress = SessionProgress(
            session_id=self.session_id,
            current_phase=0,
            total_phases=0,
            started_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat()
        )
        self._observers: list = []

    def _generate_session_id(self) -> str:
        """生成会话 ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # === Phase 管理 ===

    def set_total_phases(self, total: int):
        """设置总阶段数"""
        self._progress.total_phases = total
        self._save()

    def start_phase(self, phase_name: str):
        """开始阶段"""
        if phase_name not in self._progress.phases:
            self._progress.phases[phase_name] = PhaseProgress(
                phase_name=phase_name,
                status="running"
            )

        self._progress.phases[phase_name].status = "running"
        self._progress.current_phase = len(self._progress.phases)
        self._progress.last_updated = datetime.now().isoformat()
        self._save()

    def complete_phase(self, phase_name: str):
        """完成阶段"""
        if phase_name in self._progress.phases:
            self._progress.phases[phase_name].status = "completed"
            self._progress.phases[phase_name].progress = 100.0
            self._progress.last_updated = datetime.now().isoformat()
            self._update_overall_progress()
            self._save()

    def block_phase(self, phase_name: str):
        """阻塞阶段"""
        if phase_name in self._progress.phases:
            self._progress.phases[phase_name].status = "blocked"
            self._progress.last_updated = datetime.now().isoformat()
            self._save()

    # === Task 管理 ===

    def start_task(self, task_id: str, task_name: str, agent: str, phase_name: str):
        """开始任务"""
        if phase_name not in self._progress.phases:
            self.start_phase(phase_name)

        task = TaskProgress(
            task_id=task_id,
            task_name=task_name,
            agent=agent,
            status="running",
            progress=0.0,
            started_at=datetime.now().isoformat()
        )

        self._progress.phases[phase_name].tasks[task_id] = task
        self._progress.last_updated = datetime.now().isoformat()
        self._save()

    def update_task_progress(self, task_id: str, phase_name: str, progress: float):
        """更新任务进度"""
        if phase_name in self._progress.phases:
            task = self._progress.phases[phase_name].tasks.get(task_id)
            if task:
                task.progress = min(100.0, max(0.0, progress))
                self._progress.last_updated = datetime.now().isoformat()
                self._update_phase_progress(phase_name)
                self._save()

    def complete_task(
        self,
        task_id: str,
        phase_name: str,
        success: bool = True,
        error: Optional[str] = None
    ):
        """完成任务"""
        if phase_name in self._progress.phases:
            task = self._progress.phases[phase_name].tasks.get(task_id)
            if task:
                task.status = "completed" if success else "failed"
                task.completed_at = datetime.now().isoformat()
                task.progress = 100.0 if success else task.progress
                if task.started_at:
                    start = datetime.fromisoformat(task.started_at)
                    task.duration = (datetime.now() - start).total_seconds()
                if error:
                    task.error = error

                self._progress.last_updated = datetime.now().isoformat()
                self._update_phase_progress(phase_name)
                self._save()

    def skip_task(self, task_id: str, phase_name: str):
        """跳过任务"""
        if phase_name in self._progress.phases:
            task = self._progress.phases[phase_name].tasks.get(task_id)
            if task:
                task.status = "skipped"
                task.progress = 100.0
                self._update_phase_progress(phase_name)
                self._save()

    # === 进度计算 ===

    def _update_phase_progress(self, phase_name: str):
        """更新阶段进度"""
        phase = self._progress.phases.get(phase_name)
        if not phase:
            return

        tasks = list(phase.tasks.values())
        if not tasks:
            return

        total_progress = sum(t.progress for t in tasks)
        phase.progress = total_progress / len(tasks)

        # 检查是否全部完成
        if all(t.status == "completed" for t in tasks):
            phase.progress = 100.0

        self._update_overall_progress()

    def _update_overall_progress(self):
        """更新整体进度"""
        phases = list(self._progress.phases.values())
        if not phases:
            return

        total_progress = sum(p.progress for p in phases)
        self._progress.overall_progress = total_progress / len(phases)

    # === 报告生成 ===

    def generate_status_report(self) -> str:
        """生成状态报告"""
        lines = [
            f"# Status Report - {self.project_name}",
            "",
            f"**Session:** {self.session_id}",
            f"**Overall Progress:** {self._progress.overall_progress:.1f}%",
            f"**Current Phase:** {self._progress.current_phase}/{self._progress.total_phases}",
            "",
            "---",
            ""
        ]

        for phase_name, phase in self._progress.phases.items():
            status_icon = self._get_status_icon(phase.status)
            lines.append(f"## {status_icon} {phase_name} ({phase.progress:.0f}%)")

            for task_id, task in phase.tasks.items():
                task_icon = self._get_status_icon(task.status)
                duration_str = f" ({task.duration:.1f}s)" if task.duration > 0 else ""
                lines.append(f"  {task_icon} {task.task_name} [{task.agent}]{duration_str}")

                if task.error:
                    lines.append(f"    Error: {task.error[:100]}")

            lines.append("")

        return "\n".join(lines)

    def _get_status_icon(self, status: str) -> str:
        """获取状态图标"""
        icons = {
            "pending": "[ ]",
            "running": "[~]",
            "completed": "[X]",
            "failed": "[!]",
            "blocked": "[B]",
            "skipped": "[-]"
        }
        return icons.get(status, "[?]")

    def save_status(self):
        """保存状态到文件"""
        self._save()

    def _save(self):
        """保存进度数据"""
        import os
        os.makedirs("LOGS", exist_ok=True)

        status_file = os.path.join("LOGS", "STATUS.md")
        with open(status_file, "w", encoding="utf-8") as f:
            f.write(self.generate_status_report())

        # 保存 JSON 格式
        json_file = os.path.join("LOGS", "progress.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": self._progress.session_id,
                "current_phase": self._progress.current_phase,
                "total_phases": self._progress.total_phases,
                "overall_progress": self._progress.overall_progress,
                "phases": {
                    name: {
                        "status": phase.status,
                        "progress": phase.progress,
                        "tasks": {
                            tid: {
                                "status": t.status,
                                "progress": t.progress,
                                "agent": t.agent,
                                "duration": t.duration
                            }
                            for tid, t in phase.tasks.items()
                        }
                    }
                    for name, phase in self._progress.phases.items()
                },
                "started_at": self._progress.started_at,
                "last_updated": self._progress.last_updated
            }, f, ensure_ascii=False, indent=2)

    def get_progress(self) -> SessionProgress:
        """获取当前进度"""
        return self._progress


# 全局进度追踪器
_progress_tracker: Optional[ProgressTracker] = None


def get_progress_tracker(project_name: str = "project") -> ProgressTracker:
    """获取全局进度追踪器"""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker(project_name)
    return _progress_tracker
