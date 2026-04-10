"""Tests for agent router module."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from myagent.agents.router import AgentRouter
from myagent.models import Task, AgentRegistryModel, AgentRole, RoutingRule, TaskMode


@pytest.fixture
def sample_registry():
    """Create a sample agent registry."""
    roles = {
        "architect": AgentRole(name="architect", description="Architecture"),
        "backend-dev": AgentRole(name="backend-dev", description="Backend"),
        "frontend-dev": AgentRole(name="frontend-dev", description="Frontend"),
    }
    routing_rules = [
        RoutingRule(module="backend", agents=["backend-dev"], mode=TaskMode.SEQUENTIAL),
        RoutingRule(module="frontend", agents=["frontend-dev"], mode=TaskMode.PARALLEL),
    ]
    return AgentRegistryModel(roles=roles, routing_rules=routing_rules)


class TestAgentRouter:
    """Tests for AgentRouter."""

    def test_init_with_config(self):
        """Test AgentRouter initialization with config."""
        router = AgentRouter()
        assert router.config is None

    def test_route_task_uses_owner(self, sample_registry):
        """Test route_task uses task owner if specified."""
        router = AgentRouter()
        task = Task(name="test-task", parallel=True, owner=["architect"])

        agents, mode = router.route_task(task, sample_registry)

        assert agents == ["architect"]
        assert mode == TaskMode.PARALLEL

    def test_route_task_sequential(self, sample_registry):
        """Test route_task with sequential task."""
        router = AgentRouter()
        task = Task(name="test-task", parallel=False, owner=["backend-dev"])

        agents, mode = router.route_task(task, sample_registry)

        assert agents == ["backend-dev"]
        assert mode == TaskMode.SEQUENTIAL

    def test_route_task_no_owner_uses_rule(self, sample_registry):
        """Test route_task uses routing rule when no owner."""
        router = AgentRouter()
        task = Task(name="backend-api", parallel=False, owner=[])

        agents, mode = router.route_task(task, sample_registry)

        assert "backend-dev" in agents

    def test_route_task_no_owner_no_rule(self, sample_registry):
        """Test route_task returns all agents when no match."""
        router = AgentRouter()
        task = Task(name="unknown-task", parallel=False, owner=[])

        agents, mode = router.route_task(task, sample_registry)

        assert len(agents) > 0
        assert mode == TaskMode.SEQUENTIAL


class TestAgentRouterMatchesRule:
    """Tests for AgentRouter._matches_rule()."""

    def test_matches_rule_exact(self):
        """Test _matches_rule with exact match."""
        router = AgentRouter()
        assert router._matches_rule("backend", "backend") is True

    def test_matches_rule_contains(self):
        """Test _matches_rule with contains match."""
        router = AgentRouter()
        assert router._matches_rule("backend-api-task", "backend") is True
        assert router._matches_rule("task-backend-something", "backend") is True

    def test_matches_rule_keyword(self):
        """Test _matches_rule with keyword match."""
        router = AgentRouter()
        assert router._matches_rule("implement-api", "api") is True
        assert router._matches_rule("test-service", "test") is True

    def test_matches_rule_no_match(self):
        """Test _matches_rule with no match."""
        router = AgentRouter()
        assert router._matches_rule("random-task", "unknown-module") is False


class TestAgentRouterGetAgentForRole:
    """Tests for AgentRouter.get_agent_for_role()."""

    def test_get_agent_for_role_exists(self, sample_registry):
        """Test get_agent_for_role with existing role."""
        router = AgentRouter()
        result = router.get_agent_for_role("architect", sample_registry)

        assert result["name"] == "architect"
        assert result["description"] == "Architecture"

    def test_get_agent_for_role_not_exists(self, sample_registry):
        """Test get_agent_for_role with non-existent role."""
        router = AgentRouter()
        result = router.get_agent_for_role("nonexistent", sample_registry)

        assert result == {}


class TestAgentRouterSuggestParallel:
    """Tests for AgentRouter.suggest_parallel_tasks()."""

    def test_suggest_parallel_single_task(self, sample_registry):
        """Test suggest_parallel_tasks with single task."""
        router = AgentRouter()
        tasks = [Task(name="test", parallel=True, owner=["architect"])]

        groups = router.suggest_parallel_tasks(tasks, sample_registry)

        assert len(groups) == 1

    def test_suggest_parallel_multiple_tasks(self, sample_registry):
        """Test suggest_parallel_tasks with multiple tasks."""
        router = AgentRouter()
        tasks = [
            Task(name="backend-1", parallel=True, owner=["backend-dev"]),
            Task(name="backend-2", parallel=True, owner=["backend-dev"]),
            Task(name="frontend-1", parallel=True, owner=["frontend-dev"]),
        ]

        groups = router.suggest_parallel_tasks(tasks, sample_registry)

        assert len(groups) >= 1

    def test_suggest_parallel_no_parallel(self, sample_registry):
        """Test suggest_parallel_tasks with non-parallel tasks."""
        router = AgentRouter()
        tasks = [
            Task(name="task1", parallel=False, owner=["architect"]),
            Task(name="task2", parallel=False, owner=["architect"]),
        ]

        groups = router.suggest_parallel_tasks(tasks, sample_registry)

        assert len(groups) == 2


class TestAgentRouterCanRunTogether:
    """Tests for AgentRouter._can_run_together()."""

    def test_can_run_together_no_owners(self):
        """Test _can_run_together when no owners specified."""
        router = AgentRouter()
        task = Task(name="task1", parallel=True, owner=[])
        group = [Task(name="task2", parallel=True, owner=[])]

        assert router._can_run_together(task, group, ["agent1"]) is True

    def test_can_run_together_no_conflict(self):
        """Test _can_run_together when no owner conflict."""
        router = AgentRouter()
        task = Task(name="task1", parallel=True, owner=["backend-dev"])
        group = [Task(name="task2", parallel=True, owner=["frontend-dev"])]

        assert router._can_run_together(task, group, ["backend-dev"]) is True

    def test_can_run_together_with_conflict(self):
        """Test _can_run_together when owner conflict."""
        router = AgentRouter()
        task = Task(name="task1", parallel=True, owner=["backend-dev"])
        group = [Task(name="task2", parallel=True, owner=["backend-dev"])]

        assert router._can_run_together(task, group, ["backend-dev"]) is False