"""Risk analyzer for planning documents."""

from __future__ import annotations

from typing import Any

from myagent.models import Phase, PlanningDocument, Task, TaskTree


class RiskAnalyzer:
    """Analyzes risks in planning documents."""

    def analyze(self, planning: PlanningDocument | TaskTree, context: dict[str, Any] | None = None) -> list[str]:
        """Analyze risks in planning.

        Args:
            planning: PlanningDocument or TaskTree
            context: Optional context

        Returns:
            List of risk descriptions
        """
        risks: list[str] = []

        if isinstance(planning, PlanningDocument):
            risks.extend(self._analyze_document(planning))
        else:
            risks.extend(self._analyze_tree(planning))

        return risks

    def _analyze_document(self, doc: PlanningDocument) -> list[str]:
        """Analyze risks in planning document."""
        risks: list[str] = []

        # Check tech stack
        if not doc.tech_stack:
            risks.append("⚠️ 未指定技术栈")

        # Check file structure
        if not doc.file_structure or len(doc.file_structure) < 3:
            risks.append("⚠️ 文件结构过于简单")

        # Check API contracts
        if not doc.api_contracts:
            risks.append("⚠️ 未定义 API 契约，多个团队可能产生集成问题")

        # Check risks
        if not doc.risks:
            risks.append("⚠️ 未识别风险")

        return risks

    def _analyze_tree(self, tree: TaskTree) -> list[str]:
        """Analyze risks in task tree."""
        risks: list[str] = []

        # Count tasks
        task_count = self._count_tasks(tree.root)
        if task_count > 20:
            risks.append(f"⚠️ 任务树包含 {task_count} 个任务，可能过于复杂")

        # Check depth
        depth = self._get_depth(tree.root)
        if depth > 5:
            risks.append(f"⚠️ 任务树深度为 {depth}，建议拆分为更小的阶段")

        return risks

    def _count_tasks(self, task: "SubTask") -> int:
        """Count total tasks in tree."""
        count = 1
        for child in task.children:
            count += self._count_tasks(child)
        return count

    def _get_depth(self, task: "SubTask", current_depth: int = 0) -> int:
        """Get tree depth."""
        if not task.children:
            return current_depth
        return max(self._get_depth(child, current_depth + 1) for child in task.children)

    def suggest_mitigations(self, risks: list[str]) -> dict[str, str]:
        """Suggest mitigations for identified risks.

        Args:
            risks: List of risk descriptions

        Returns:
            Dict of risk -> mitigation
        """
        mitigations: dict[str, str] = {}

        for risk in risks:
            if "技术栈" in risk:
                mitigations[risk] = "在 PLANNING.md 中明确技术栈选择"
            elif "文件结构" in risk:
                mitigations[risk] = "细化文件结构，添加目录说明"
            elif "API 契约" in risk:
                mitigations[risk] = "在规划阶段明确定义 API Schema"
            elif "集成问题" in risk:
                mitigations[risk] = "增加 API 评审环节"
            elif "复杂" in risk:
                mitigations[risk] = "将大任务拆分为多个小任务"
            elif "深度" in risk:
                mitigations[risk] = "拆分为多个阶段，每个阶段关注特定层次"

        return mitigations
