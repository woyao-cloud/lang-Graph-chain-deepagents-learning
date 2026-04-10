"""Workflow parser for MyAgent.

Parses workflow.md Markdown files into WorkflowModel.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from myagent.models import Phase, PhaseStatus, Task, TaskMode, TaskStatus, WorkflowModel

if TYPE_CHECKING:
    pass


class WorkflowParser:
    """Parser for workflow.md files."""

    # Regex patterns for parsing
    PHASE_PATTERN = re.compile(
        r"- \[Phase (\d+)\]\s*(.+?)\s*\((depends:\s*(.+?))?\)"
    )
    TASK_PATTERN = re.compile(
        r"-\s*Task:\s*(.+?)\s*\(parallel:\s*(true|false)?,?\s*owner:\s*(.+?)?\)"
    )
    RULE_PATTERN = re.compile(r"-\s*(.+?)$")

    def parse(self, path: Path) -> WorkflowModel:
        """Parse workflow.md file.

        Args:
            path: Path to workflow.md file

        Returns:
            WorkflowModel with parsed phases and tasks
        """
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {path}")

        content = path.read_text(encoding="utf-8")
        return self.parse_content(content)

    def parse_content(self, content: str) -> WorkflowModel:
        """Parse workflow.md content string.

        Args:
            content: Workflow.md content

        Returns:
            WorkflowModel with parsed phases and tasks
        """
        lines = content.split("\n")

        phases: list[Phase] = []
        current_phase: Phase | None = None
        rules: list[str] = []
        in_rules_section = False

        for line in lines:
            stripped = line.strip()

            # Track sections
            if stripped.lower() == "## rules":
                in_rules_section = True
                continue

            # Parse phase header
            phase_match = self.PHASE_PATTERN.match(stripped)
            if phase_match:
                phase_index = int(phase_match.group(1))
                phase_name = phase_match.group(2).strip()
                depends_str = phase_match.group(4) or ""
                depends = [d.strip() for d in depends_str.split(",") if d.strip()]

                current_phase = Phase(
                    name=phase_name,
                    index=phase_index,
                    depends_on=depends,
                    tasks=[],
                    status=PhaseStatus.PENDING,
                )
                phases.append(current_phase)
                in_rules_section = False
                continue

            # Parse task within phase
            if current_phase:
                task_match = self.TASK_PATTERN.match(stripped)
                if task_match:
                    task_name = task_match.group(1).strip()
                    parallel_str = task_match.group(2) or "false"
                    parallel = parallel_str.lower() == "true"
                    owner_str = task_match.group(3) or ""
                    owners = [o.strip() for o in owner_str.split(",") if o.strip()]

                    task = Task(
                        name=task_name,
                        parallel=parallel,
                        owner=owners,
                        status=TaskStatus.PENDING,
                    )
                    current_phase.tasks.append(task)
                    continue

            # Parse rule
            if in_rules_section:
                rule_match = self.RULE_PATTERN.match(stripped)
                if rule_match:
                    rule = rule_match.group(1).strip()
                    if rule:
                        rules.append(rule)

        return WorkflowModel(
            phases=phases,
            rules=rules,
            raw_content=content,
        )

    def extract_phases(self, content: str) -> list[Phase]:
        """Extract phases from workflow content.

        Args:
            content: Workflow.md content

        Returns:
            List of Phase objects
        """
        workflow = self.parse_content(content)
        return workflow.phases

    def extract_tasks(self, phase: Phase) -> list[Task]:
        """Extract tasks from a phase.

        Args:
            phase: Phase object

        Returns:
            List of Task objects
        """
        return phase.tasks

    def validate(self, workflow: WorkflowModel) -> list[str]:
        """Validate workflow model.

        Args:
            workflow: WorkflowModel to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        # Check for duplicate phase indices
        indices = [p.index for p in workflow.phases]
        if len(indices) != len(set(indices)):
            errors.append("Duplicate phase indices found")

        # Check phase dependencies exist
        phase_names = {p.name for p in workflow.phases}
        for phase in workflow.phases:
            for dep in phase.depends_on:
                if dep not in phase_names and dep != "none":
                    errors.append(f"Phase '{phase.name}' depends on non-existent phase '{dep}'")

        # Check for circular dependencies
        if self._has_cycle(workflow):
            errors.append("Circular dependency detected in workflow")

        return errors

    def _has_cycle(self, workflow: WorkflowModel) -> bool:
        """Check for circular dependencies using DFS.

        Args:
            workflow: WorkflowModel to check

        Returns:
            True if cycle exists
        """
        graph: dict[str, list[str]] = {}
        for phase in workflow.phases:
            graph[phase.name] = phase.depends_on

        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor == "none":
                    continue
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for phase in workflow.phases:
            if phase.name not in visited:
                if dfs(phase.name):
                    return True

        return False
