"""
阶段导航器 - 管理工作流阶段推进
FR-WF-001.4: 阶段推进
"""

from typing import List, Optional, Set
from dataclasses import dataclass
from deepagents.workflow.parser import Workflow
from deepagents.workflow.dag import DAG, DAGNode


@dataclass
class ExecutionState:
    """执行状态"""
    current_phase: str
    completed_phases: Set[str]
    current_tasks: List[str]
    completed_tasks: Set[str]
    blocked_reason: Optional[str] = None


class PhaseNavigator:
    """
    阶段导航器
    管理工作流的阶段推进
    """

    def __init__(self, dag: DAG):
        self.dag = dag
        self._state: Optional[ExecutionState] = None

    def initialize(self, start_phase: Optional[str] = None) -> ExecutionState:
        """
        初始化执行状态
        可以指定起始阶段（用于断点续跑）
        """
        phases = self.dag.topological_sort()
        start_idx = 0

        if start_phase:
            for i, phase in enumerate(phases):
                if phase.id == start_phase or phase.name == start_phase:
                    start_idx = i
                    break

        current = phases[start_idx] if start_idx < len(phases) else None

        self._state = ExecutionState(
            current_phase=current.name if current else "",
            completed_phases=set(p.name for p in phases[:start_idx]),
            current_tasks=[],
            completed_tasks=set()
        )

        return self._state

    def can_execute_phase(self, phase_name: str) -> bool:
        """
        检查是否可以执行指定阶段
        条件: 所有依赖阶段已完成
        """
        for phase in self.dag.phases:
            if phase.name == phase_name:
                for dep in phase.depends:
                    if dep not in self._state.completed_phases:
                        self._state.blocked_reason = f"等待依赖阶段完成: {dep}"
                        return False
                return True
        return False

    def get_next_executable_tasks(self) -> List[DAGNode]:
        """
        获取下一个可执行的任务列表
        考虑并行和依赖关系
        """
        if not self._state:
            return []

        tasks = []
        for node in self.dag.nodes.values():
            if node.node_type != "task":
                continue
            if node.id in self._state.completed_tasks:
                continue
            # 检查依赖是否都已完成
            all_deps_done = all(
                dep in self._state.completed_phases
                for dep in node.depends
            )
            if all_deps_done:
                tasks.append(node)

        return tasks

    def complete_phase(self, phase_name: str):
        """标记阶段完成"""
        if self._state:
            self._state.completed_phases.add(phase_name)

    def complete_task(self, task_id: str):
        """标记任务完成"""
        if self._state:
            self._state.completed_tasks.add(task_id)

    @property
    def state(self) -> ExecutionState:
        return self._state
