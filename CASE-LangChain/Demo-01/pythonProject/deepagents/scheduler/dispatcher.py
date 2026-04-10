"""
任务分发器 - 将任务分配给对应的 Sub-Agent
FR-AGENT-001.2: 任务路由
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from deepagents.workflow.parser import Task, Phase
from deepagents.workflow.dag import DAGNode


@dataclass
class TaskAssignment:
    """任务分配"""
    task_id: str
    task_name: str
    assigned_agents: List[str]  # 分配的 Agent 列表
    mode: str  # "parallel" 或 "sequential"
    depends_on: List[str] = None  # 依赖的任务 ID


class TaskRouter:
    """
    任务路由器
    根据 agent.md 的 Routing Rules 将任务分配给对应 Agent
    """

    def __init__(self, agent_config: Dict):
        self.agent_config = agent_config
        self.routing_rules = agent_config.get("routing_rules", {})

    def route(self, task: Task, phase_name: str) -> TaskAssignment:
        """
        将任务路由到对应的 Agent
        """
        # 查找匹配的路由规则
        matched_agents = self._find_matching_agents(task.name)

        if not matched_agents:
            # 默认使用 task.owner
            matched_agents = task.owner or ["backend-dev"]

        return TaskAssignment(
            task_id=task.name,
            task_name=task.name,
            assigned_agents=matched_agents,
            mode="parallel" if task.parallel else "sequential",
            depends_on=[]
        )

    def _find_matching_agents(self, task_name: str) -> List[str]:
        """
        根据任务名称查找匹配的 Agent
        使用简单的关键词匹配
        """
        matched = []

        # 前端相关任务
        if any(keyword in task_name for keyword in ["前端", "界面", "UI", "frontend"]):
            matched.append("frontend-dev")

        # 后端相关任务
        if any(keyword in task_name for keyword in ["后端", "API", "服务", "backend"]):
            matched.append("backend-dev")

        # 测试相关任务
        if any(keyword in task_name for keyword in ["测试", "test", "QA"]):
            matched.append("qa-engineer")

        # 架构设计任务
        if any(keyword in task_name for keyword in ["架构", "设计", "architect"]):
            matched.append("architect")

        # 默认后端开发
        if not matched:
            matched.append("backend-dev")

        return matched

    def batch_route(self, tasks: List[Task], phase_name: str) -> List[TaskAssignment]:
        """
        批量路由任务
        """
        return [self.route(task, phase_name) for task in tasks]


class ConflictDetector:
    """
    冲突检测器
    检测并行任务之间的共享依赖冲突
    """

    def __init__(self):
        self.assignments: List[TaskAssignment] = []

    def add_assignment(self, assignment: TaskAssignment):
        self.assignments.append(assignment)

    def detect_conflicts(self) -> List[Dict]:
        """
        检测冲突
        返回冲突列表
        """
        conflicts = []

        # 检查是否有相同的 Agent 被分配到相互依赖的任务
        for i, a1 in enumerate(self.assignments):
            for a2 in self.assignments[i + 1:]:
                # 检查是否有共同的 Agent
                common_agents = set(a1.assigned_agents) & set(a2.assigned_agents)
                if common_agents:
                    # 检查是否有循环依赖
                    if self._has_circular_dependency(a1, a2):
                        conflicts.append({
                            "type": "circular_dependency",
                            "task1": a1.task_name,
                            "task2": a2.task_name,
                            "common_agents": list(common_agents)
                        })

        return conflicts

    def _has_circular_dependency(self, a1: TaskAssignment, a2: TaskAssignment) -> bool:
        """检测两个任务之间是否有循环依赖"""
        return (
            a1.task_id in (a2.depends_on or [])
            and a2.task_id in (a1.depends_on or [])
        )
