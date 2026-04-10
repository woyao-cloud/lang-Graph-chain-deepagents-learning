"""Agent router for MyAgent.

Routes tasks to appropriate DeepAgents SubAgents.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from myagent.models import AgentRegistryModel, RoutingRule, Task, TaskMode

if TYPE_CHECKING:
    from myagent.config import MyAgentConfig


class AgentRouter:
    """Routes tasks to appropriate agents based on rules."""

    def __init__(self, config: "MyAgentConfig | None" = None):
        """Initialize agent router.

        Args:
            config: MyAgent configuration
        """
        self.config = config

    def route_task(
        self,
        task: Task,
        registry: AgentRegistryModel,
    ) -> tuple[list[str], TaskMode]:
        """Route a task to appropriate agents.

        Args:
            task: Task to route
            registry: Agent registry

        Returns:
            Tuple of (agent_names, execution_mode)
        """
        # First, check task owner
        if task.owner:
            mode = TaskMode.PARALLEL if task.parallel else TaskMode.SEQUENTIAL
            return task.owner, mode

        # Try to find routing rule
        for rule in registry.routing_rules:
            if self._matches_rule(task.name, rule.module):
                return rule.agents, rule.mode

        # Default: return all available agents
        all_agents = list(registry.roles.keys())
        return all_agents, TaskMode.SEQUENTIAL

    def _matches_rule(self, task_name: str, rule_module: str) -> bool:
        """Check if task matches routing rule module.

        Args:
            task_name: Task name
            rule_module: Rule module pattern

        Returns:
            True if matches
        """
        task_lower = task_name.lower()
        rule_lower = rule_module.lower()

        # Exact match
        if task_lower == rule_lower:
            return True

        # Contains match
        if rule_lower in task_lower or task_lower in rule_lower:
            return True

        # Keyword match
        keywords = {
            "backend": ["backend", "后端", "api", "service"],
            "frontend": ["frontend", "前端", "ui", "web", "react", "vue"],
            "qa": ["qa", "test", "测试", "quality"],
            "architect": ["architecture", "架构", "design", "设计"],
        }

        for keyword_list in keywords.values():
            if any(k in task_lower for k in keyword_list):
                return True

        return False

    def get_agent_for_role(
        self,
        role_name: str,
        registry: AgentRegistryModel,
    ) -> dict[str, Any]:
        """Get agent configuration for a role.

        Args:
            role_name: Role name
            registry: Agent registry

        Returns:
            Dict with agent configuration
        """
        role = registry.roles.get(role_name)
        if not role:
            return {}

        return {
            "name": role.name,
            "description": role.description,
            "tools": role.tools,
            "model": role.model,
        }

    def suggest_parallel_tasks(
        self,
        tasks: list[Task],
        registry: AgentRegistryModel,
    ) -> list[list[Task]]:
        """Suggest grouping of tasks that can run in parallel.

        Args:
            tasks: List of tasks
            registry: Agent registry

        Returns:
            List of task groups
        """
        parallel_groups: list[list[Task]] = []
        sequential_tasks: list[Task] = []

        for task in tasks:
            agents, mode = self.route_task(task, registry)

            if mode == TaskMode.PARALLEL and len(agents) > 1:
                # This task can run in parallel with others
                found_group = False
                for group in parallel_groups:
                    if self._can_run_together(task, group, agents):
                        group.append(task)
                        found_group = True
                        break

                if not found_group:
                    parallel_groups.append([task])
            else:
                sequential_tasks.append(task)

        # Add sequential tasks as single-item groups
        for task in sequential_tasks:
            parallel_groups.append([task])

        return parallel_groups

    def _can_run_together(
        self,
        task: Task,
        group: list[Task],
        agents: list[str],
    ) -> bool:
        """Check if task can run in parallel with group.

        Args:
            task: Task to check
            group: Existing group
            agents: Agents for the task

        Returns:
            True if can run together
        """
        for existing in group:
            if existing.owner:
                # Check for owner conflict
                if any(a in existing.owner for a in agents):
                    return False

        return True
