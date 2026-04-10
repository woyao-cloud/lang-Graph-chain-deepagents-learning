"""Planning document generator for MyAgent.

Generates PLANNING.md from workflow phases and tasks.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from myagent.models import Phase, PlanningDocument, SubTask, TaskTree, WorkflowModel

if TYPE_CHECKING:
    from myagent.config import MyAgentConfig


class TaskDecomposer:
    """Decomposes tasks into subtasks."""

    def decompose(self, task_name: str, context: dict) -> SubTask:
        """Decompose a task into subtasks.

        Args:
            task_name: Name of the task
            context: Context including phase and workflow info

        Returns:
            SubTask with children
        """
        # Simple decomposition - in real implementation, this would use LLM
        root = SubTask(
            name=task_name,
            description=f"Main task: {task_name}",
        )

        # Add default subtasks
        root.children = [
            SubTask(
                name=f"{task_name}:analyze",
                description=f"Analyze requirements for {task_name}",
            ),
            SubTask(
                name=f"{task_name}:design",
                description=f"Design solution for {task_name}",
            ),
            SubTask(
                name=f"{task_name}:implement",
                description=f"Implement {task_name}",
            ),
            SubTask(
                name=f"{task_name}:test",
                description=f"Test {task_name}",
            ),
        ]

        return root


class PlanningGenerator:
    """Generates PLANNING.md documents."""

    def __init__(self, config: "MyAgentConfig | None" = None):
        """Initialize planning generator.

        Args:
            config: MyAgent configuration
        """
        self.config = config
        self.decomposer = TaskDecomposer()

    def generate(self, phase: Phase, workflow: WorkflowModel) -> PlanningDocument:
        """Generate planning document for a phase.

        Args:
            phase: Phase to plan
            workflow: Full workflow context

        Returns:
            PlanningDocument
        """
        # Decompose tasks
        subtasks = []
        for task in phase.tasks:
            subtask_tree = self.decomposer.decompose(task.name, {
                "phase": phase,
                "workflow": workflow,
            })
            subtasks.append(subtask_tree)

        # Build task tree
        root = SubTask(
            name=phase.name,
            description=f"Phase: {phase.name}",
            children=subtasks,
        )
        task_tree = TaskTree(
            root=root,
            tech_stack=self._suggest_tech_stack(phase),
            file_structure=self._suggest_file_structure(phase),
            api_contracts=[],
            risks=self._identify_risks(phase),
        )

        return PlanningDocument(
            title=f"Planning: {phase.name}",
            task_tree=task_tree,
            tech_stack=task_tree.tech_stack,
            file_structure=task_tree.file_structure,
            api_contracts=task_tree.api_contracts,
            risks=task_tree.risks,
            confirmed=False,
        )

    def generate_markdown(self, planning: PlanningDocument) -> str:
        """Generate Markdown content for planning document.

        Args:
            planning: PlanningDocument

        Returns:
            Markdown string
        """
        lines = [
            f"# {planning.title}",
            "",
            "## 任务分解",
            "",
            "```",
            self._render_task_tree(planning.task_tree.root, 0),
            "```",
            "",
            "## 技术栈",
            "",
        ]

        for key, value in planning.tech_stack.items():
            lines.append(f"- **{key}**: {value}")

        lines.extend([
            "",
            "## 文件结构",
            "",
        ])

        for path in planning.file_structure:
            lines.append(f"- `{path}`")

        if planning.api_contracts:
            lines.extend([
                "",
                "## API 契约",
                "",
            ])
            for contract in planning.api_contracts:
                lines.append(f"### {contract.get('name', 'API')}")
                lines.append(f"```")
                lines.append(contract.get("schema", ""))
                lines.append(f"```")
                lines.append("")

        if planning.risks:
            lines.extend([
                "## 风险识别",
                "",
            ])
            for risk in planning.risks:
                lines.append(f"- ⚠️ {risk}")

        lines.extend([
            "",
            "## 确认",
            "",
            "- [ ] 已阅读并确认上述规划",
            "- [ ] 技术栈选择合理",
            "- [ ] 文件结构符合预期",
            "",
            "---",
            f"*由 MyAgent 生成 | 确认后执行*",
        ])

        return "\n".join(lines)

    def _render_task_tree(self, task: SubTask, indent: int) -> str:
        """Render task tree as indented text."""
        prefix = "  " * indent
        lines = [f"{prefix}├── {task.name}: {task.description}"]

        for i, child in enumerate(task.children):
            is_last = i == len(task.children) - 1
            child_prefix = "  " * (indent + 1)
            child_prefix = child_prefix[:-2] + ("└──" if is_last else "├──")
            lines.append(f"{child_prefix} {child.name}: {child.description}")

            if child.children:
                lines.append(self._render_task_tree(child, indent + 2))

        return "\n".join(lines)

    def _suggest_tech_stack(self, phase: Phase) -> dict[str, str]:
        """Suggest tech stack based on phase tasks."""
        stack: dict[str, str] = {}

        for task in phase.tasks:
            for owner in task.owner:
                if owner == "backend-dev":
                    stack["Backend"] = "Python 3.11+ / FastAPI"
                elif owner == "frontend-dev":
                    stack["Frontend"] = "React 18+ / TypeScript"
                elif owner == "qa-engineer":
                    stack["Testing"] = "Pytest / Playwright"
                elif owner == "architect":
                    stack["Architecture"] = "Microservices / API-first"

        if not stack:
            stack["Language"] = "Python 3.11+"

        return stack

    def _suggest_file_structure(self, phase: Phase) -> list[str]:
        """Suggest file structure based on phase tasks."""
        structure = [
            "src/",
            "src/__init__.py",
            "src/main.py",
            "src/config.py",
            "tests/",
            "tests/__init__.py",
            "tests/test_main.py",
            "requirements.txt",
            "README.md",
        ]

        for task in phase.tasks:
            if "backend" in task.name.lower() or "api" in task.name.lower():
                structure.extend([
                    "src/api/",
                    "src/api/routes.py",
                    "src/api/models.py",
                    "src/services/",
                    "src/services/business.py",
                ])
            if "frontend" in task.name.lower() or "ui" in task.name.lower():
                structure.extend([
                    "src/ui/",
                    "src/ui/components/",
                    "src/ui/pages/",
                ])

        return structure

    def _identify_risks(self, phase: Phase) -> list[str]:
        """Identify risks for the phase."""
        risks = []

        for task in phase.tasks:
            if task.parallel:
                risks.append(f"并行任务 '{task.name}' 需要注意文件冲突")
            if len(task.owner) > 2:
                risks.append(f"任务 '{task.name}' 涉及 {len(task.owner)} 个角色，协作成本较高")

        if not risks:
            risks.append("无明显风险")

        return risks

    def save(self, planning: PlanningDocument, path: Path) -> None:
        """Save planning document to file.

        Args:
            planning: PlanningDocument
            path: File path
        """
        markdown = self.generate_markdown(planning)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        planning.path = path

    def load(self, path: Path) -> PlanningDocument:
        """Load planning document from file.

        Args:
            path: File path

        Returns:
            PlanningDocument
        """
        content = path.read_text(encoding="utf-8")

        # Simple parsing - in real implementation, would parse more thoroughly
        confirmed = "[x]" in content or "[X]" in content

        # Create a minimal planning document
        # Real implementation would parse the file more thoroughly
        root = SubTask(name="root", description="Loaded planning")

        return PlanningDocument(
            title=path.stem,
            task_tree=TaskTree(
                root=root,
                tech_stack={},
                file_structure=[],
                api_contracts=[],
                risks=[],
            ),
            tech_stack={},
            file_structure=[],
            api_contracts=[],
            risks=[],
            confirmed=confirmed,
            path=path,
        )
