"""DAG builder for workflow tasks.

Constructs a Directed Acyclic Graph from workflow phases and tasks.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from myagent.models import Phase, Task, WorkflowModel


@dataclass
class DAGNode:
    """A node in the DAG representing a phase or task."""
    id: str
    name: str
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DAG:
    """Directed Acyclic Graph representation."""
    nodes: dict[str, DAGNode] = field(default_factory=dict)

    def add_node(self, node: DAGNode) -> None:
        """Add a node to the DAG."""
        self.nodes[node.id] = node

    def add_edge(self, from_id: str, to_id: str) -> None:
        """Add a directed edge from -> to."""
        if from_id in self.nodes:
            self.nodes[from_id].dependents.append(to_id)
        if to_id in self.nodes:
            self.nodes[to_id].dependencies.append(from_id)

    def get_parallel_tasks(self) -> list[str]:
        """Get task IDs that can be executed in parallel.

        Returns:
            List of task IDs with no dependencies on each other
        """
        # Tasks that have no pending dependencies can run in parallel
        parallel: list[str] = []
        for node in self.nodes.values():
            if not node.dependencies:
                parallel.append(node.id)
        return parallel

    def topological_sort(self) -> list[str]:
        """Get nodes in topological order (respecting dependencies).

        Returns:
            List of node IDs in execution order
        """
        in_degree: dict[str, int] = {node_id: 0 for node_id in self.nodes}

        # Calculate in-degrees
        for node in self.nodes.values():
            for dep in node.dependencies:
                in_degree[node.id] += 1

        # Start with nodes that have no dependencies
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result: list[str] = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)

            # Reduce in-degree for dependents
            for dependent_id in self.nodes[node_id].dependents:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        # Check for cycle
        if len(result) != len(self.nodes):
            raise ValueError("Cycle detected in DAG")

        return result

    def get_execution_levels(self) -> list[list[str]]:
        """Get nodes grouped by execution level.

        Nodes in the same level can be executed in parallel.

        Returns:
            List of levels, each containing node IDs
        """
        levels: list[list[str]] = []
        remaining = set(self.nodes.keys())

        while remaining:
            # Find nodes with no dependencies in remaining set
            current_level = []
            for node_id in list(remaining):
                node = self.nodes[node_id]
                if all(dep not in remaining for dep in node.dependencies):
                    current_level.append(node_id)

            if not current_level:
                raise ValueError("Cycle detected - cannot progress")

            levels.append(current_level)
            remaining -= set(current_level)

        return levels


class DAGBuilder:
    """Builder for constructing DAG from workflow model."""

    def build(self, workflow: WorkflowModel) -> DAG:
        """Build DAG from workflow model.

        Args:
            workflow: Parsed workflow model

        Returns:
            DAG representing the workflow
        """
        dag = DAG()

        # Add all phases as nodes
        for phase in workflow.phases:
            phase_id = f"phase:{phase.index}"
            dag.add_node(DAGNode(
                id=phase_id,
                name=phase.name,
                metadata={"phase": phase, "type": "phase"},
            ))

        # Add edges for phase dependencies
        for phase in workflow.phases:
            phase_id = f"phase:{phase.index}"
            for dep in phase.depends_on:
                if dep.lower() == "none":
                    continue
                # Find phase by name or index
                dep_id = self._find_phase_id(workflow, dep)
                if dep_id:
                    dag.add_edge(dep_id, phase_id)

        # Add task nodes and edges
        for phase in workflow.phases:
            phase_id = f"phase:{phase.index}"
            for task in phase.tasks:
                task_id = f"task:{phase.index}:{task.name}"
                dag.add_node(DAGNode(
                    id=task_id,
                    name=task.name,
                    metadata={
                        "phase": phase,
                        "task": task,
                        "type": "task",
                        "parallel": task.parallel,
                        "owners": task.owner,
                    },
                ))
                # Tasks depend on their phase
                dag.add_edge(phase_id, task_id)

                # Tasks depend on other tasks in same phase if sequential
                if not task.parallel:
                    prev_task_id = None
                    for prev_task in phase.tasks:
                        prev_task_id = f"task:{phase.index}:{prev_task.name}"
                        if prev_task_id == task_id:
                            break
                        if prev_task_id:
                            dag.add_edge(prev_task_id, task_id)

        return dag

    def _find_phase_id(self, workflow: WorkflowModel, dep: str) -> str | None:
        """Find phase ID by name or index.

        Args:
            workflow: Workflow model
            dep: Dependency name or index

        Returns:
            Phase ID or None if not found
        """
        # Try as index first
        try:
            index = int(dep.replace("Phase ", "").replace("phase ", ""))
            return f"phase:{index}"
        except ValueError:
            pass

        # Try as name
        for phase in workflow.phases:
            if phase.name == dep:
                return f"phase:{phase.index}"

        return None

    def get_parallel_tasks(self, dag: DAG | None = None, workflow: WorkflowModel | None = None) -> list[Task]:
        """Get tasks that can be executed in parallel.

        Args:
            dag: Pre-built DAG (optional)
            workflow: Workflow model (used if dag not provided)

        Returns:
            List of tasks that can run in parallel
        """
        if dag is None and workflow is None:
            raise ValueError("Either dag or workflow must be provided")

        if dag is None and workflow:
            dag = self.build(workflow)

        parallel_tasks: list[Task] = []
        for node in dag.nodes.values():
            if node.metadata.get("type") == "task" and node.metadata.get("parallel"):
                parallel_tasks.append(node.metadata["task"])

        return parallel_tasks

    def get_execution_order(self, workflow: WorkflowModel) -> list[str]:
        """Get phases in execution order.

        Args:
            workflow: Workflow model

        Returns:
            List of phase IDs in topological order
        """
        dag = self.build(workflow)
        return dag.topological_sort()
