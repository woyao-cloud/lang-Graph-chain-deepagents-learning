"""Task decomposer for MyAgent.

Decomposes tasks into executable subtasks using LLM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from myagent.models import Phase, SubTask, Task, TaskTree

if TYPE_CHECKING:
    pass


class TaskDecomposer:
    """Decomposes tasks into subtask trees."""

    def decompose(self, task: Task, context: dict[str, Any]) -> SubTask:
        """Decompose a task into subtasks.

        Args:
            task: Task to decompose
            context: Context including phase and workflow info

        Returns:
            SubTask root with children
        """
        # Create root subtask
        root = SubTask(
            name=task.name,
            description=f"Main task: {task.name}",
            assignee=task.owner[0] if task.owner else None,
        )

        # Decompose based on task type and owners
        children = self._decompose_by_owners(task, context)
        root.children = children

        return root

    def _decompose_by_owners(self, task: Task, context: dict[str, Any]) -> list[SubTask]:
        """Decompose task based on assigned owners.

        Args:
            task: Task to decompose
            context: Context dict

        Returns:
            List of child subtasks
        """
        children: list[SubTask] = []

        phase = context.get("phase")
        phase_name = phase.name if phase else "Unknown"

        for owner in task.owner:
            if owner == "architect":
                children.extend([
                    SubTask(
                        name=f"{task.name}:architecture",
                        description="设计系统架构和技术选型",
                        assignee="architect",
                    ),
                    SubTask(
                        name=f"{task.name}:api-design",
                        description="设计 API 接口契约",
                        assignee="architect",
                    ),
                ])
            elif owner == "backend-dev":
                children.extend([
                    SubTask(
                        name=f"{task.name}:backend-analysis",
                        description="分析需求并设计数据模型",
                        assignee="backend-dev",
                    ),
                    SubTask(
                        name=f"{task.name}:backend-implement",
                        description="实现后端业务逻辑",
                        assignee="backend-dev",
                    ),
                    SubTask(
                        name=f"{task.name}:backend-test",
                        description="编写后端单元测试",
                        assignee="backend-dev",
                    ),
                ])
            elif owner == "frontend-dev":
                children.extend([
                    SubTask(
                        name=f"{task.name}:frontend-design",
                        description="设计 UI 组件和页面",
                        assignee="frontend-dev",
                    ),
                    SubTask(
                        name=f"{task.name}:frontend-implement",
                        description="实现前端界面",
                        assignee="frontend-dev",
                    ),
                    SubTask(
                        name=f"{task.name}:frontend-test",
                        description="编写前端测试",
                        assignee="frontend-dev",
                    ),
                ])
            elif owner == "qa-engineer":
                children.extend([
                    SubTask(
                        name=f"{task.name}:test-plan",
                        description="制定测试计划",
                        assignee="qa-engineer",
                    ),
                    SubTask(
                        name=f"{task.name}:test-cases",
                        description="编写测试用例",
                        assignee="qa-engineer",
                    ),
                    SubTask(
                        name=f"{task.name}:test-execute",
                        description="执行测试",
                        assignee="qa-engineer",
                    ),
                ])

        return children

    def decompose_phase(self, phase: Phase, context: dict[str, Any]) -> TaskTree:
        """Decompose an entire phase into a task tree.

        Args:
            phase: Phase to decompose
            context: Context dict

        Returns:
            TaskTree
        """
        root_subtasks = []

        for task in phase.tasks:
            subtask = self.decompose(task, {**context, "phase": phase})
            root_subtasks.append(subtask)

        # Create phase root
        phase_root = SubTask(
            name=phase.name,
            description=f"Phase {phase.index}: {phase.name}",
            children=root_subtasks,
        )

        return TaskTree(
            root=phase_root,
            tech_stack=self._suggest_tech_stack(phase),
            file_structure=self._suggest_file_structure(phase),
            api_contracts=[],
            risks=self._identify_risks(phase),
        )

    def _suggest_tech_stack(self, phase: Phase) -> dict[str, str]:
        """Suggest tech stack based on phase and tasks."""
        stack: dict[str, str] = {}

        for task in phase.tasks:
            for owner in task.owner:
                if owner == "backend-dev":
                    if "Backend" not in stack:
                        stack["Backend"] = "Python 3.11+ / FastAPI"
                elif owner == "frontend-dev":
                    if "Frontend" not in stack:
                        stack["Frontend"] = "React 18+ / TypeScript"
                elif owner == "qa-engineer":
                    if "Testing" not in stack:
                        stack["Testing"] = "Pytest + Playwright"
                elif owner == "architect":
                    if "Architecture" not in stack:
                        stack["Architecture"] = "Clean Architecture / Microservices"

        if not stack:
            stack["Language"] = "Python 3.11+"

        return stack

    def _suggest_file_structure(self, phase: Phase) -> list[str]:
        """Suggest file structure based on phase tasks."""
        structure = [
            "src/__init__.py",
            "src/main.py",
            "src/config.py",
            "tests/__init__.py",
            "requirements.txt",
            "README.md",
        ]

        for task in phase.tasks:
            if any(owner in task.owner for owner in ["backend-dev", "architect"]):
                structure.extend([
                    "src/api/",
                    "src/api/routes.py",
                    "src/api/models.py",
                    "src/services/",
                    "src/services/business.py",
                    "src/models/",
                ])
            if any(owner in task.owner for owner in ["frontend-dev"]):
                structure.extend([
                    "src/ui/",
                    "src/ui/components/",
                    "src/ui/pages/",
                    "src/ui/hooks/",
                ])
            if any(owner in task.owner for owner in ["qa-engineer"]):
                structure.extend([
                    "tests/test_api/",
                    "tests/test_services/",
                    "tests/conftest.py",
                ])

        return list(dict.fromkeys(structure))  # Remove duplicates while preserving order

    def _identify_risks(self, phase: Phase) -> list[str]:
        """Identify risks for the phase."""
        risks = []

        parallel_tasks = [t for t in phase.tasks if t.parallel]
        if len(parallel_tasks) > 1:
            risks.append(f"⚠️ {len(parallel_tasks)} 个并行任务需要注意文件冲突和依赖管理")

        multi_owner_tasks = [t for t in phase.tasks if len(t.owner) > 1]
        if multi_owner_tasks:
            risks.append(f"⚠️ {len(multi_owner_tasks)} 个任务涉及多个角色，需要明确职责边界")

        if len(phase.tasks) > 5:
            risks.append(f"⚠️ 阶段包含 {len(phase.tasks)} 个任务，建议拆分为更小的阶段")

        if not risks:
            risks.append("✅ 无明显风险")

        return risks
