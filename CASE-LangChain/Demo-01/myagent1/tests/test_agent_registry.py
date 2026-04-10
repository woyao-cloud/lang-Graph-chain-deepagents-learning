"""Tests for agents/registry.py module."""

from __future__ import annotations

from pathlib import Path

import pytest

from myagent.agents.registry import AgentRegistry
from myagent.models import (
    AgentRegistryModel,
    AgentRole,
    RoutingRule,
    TaskMode,
)


class TestAgentRegistryInit:
    """Tests for AgentRegistry initialization."""

    def test_default_init(self):
        """Test default initialization."""
        registry = AgentRegistry()
        assert registry is not None
        assert hasattr(registry, "ROLE_PATTERN")
        assert hasattr(registry, "ROUTING_PATTERN")


class TestAgentRegistryLoad:
    """Tests for AgentRegistry.load() method."""

    def test_load_file_not_found(self, nonexistent_file: Path):
        """Test loading nonexistent file raises FileNotFoundError."""
        registry = AgentRegistry()
        with pytest.raises(FileNotFoundError) as exc_info:
            registry.load(nonexistent_file)
        assert "not found" in str(exc_info.value)

    def test_load_valid_file(self, agent_file: Path):
        """Test loading a valid agent file."""
        registry = AgentRegistry()
        model = registry.load(agent_file)

        assert isinstance(model, AgentRegistryModel)
        assert len(model.roles) > 0


class TestAgentRegistryParseContent:
    """Tests for AgentRegistry.parse_content() method."""

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        registry = AgentRegistry()
        model = registry.parse_content("")

        assert model.roles == {}
        assert model.routing_rules == []

    def test_parse_roles_section(self):
        """Test parsing roles section."""
        content = """
## Roles
- architect: 负责架构设计
- backend-dev: 后端开发
"""
        registry = AgentRegistry()
        model = registry.parse_content(content)

        assert "architect" in model.roles
        assert "backend-dev" in model.roles
        assert model.roles["architect"].description == "负责架构设计"

    def test_parse_routing_rules_section(self):
        """Test parsing routing rules section."""
        content = """
## Routing Rules
- api -> backend-dev (sequential)
- ui -> frontend-dev (parallel)
"""
        registry = AgentRegistry()
        model = registry.parse_content(content)

        assert len(model.routing_rules) == 2

    def test_parse_routing_with_multiple_agents(self):
        """Test parsing routing with multiple agents."""
        content = """
## Routing Rules
- core -> backend-dev + frontend-dev (parallel)
"""
        registry = AgentRegistry()
        model = registry.parse_content(content)

        assert len(model.routing_rules) == 1
        rule = model.routing_rules[0]
        assert len(rule.agents) == 2
        assert "backend-dev" in rule.agents
        assert "frontend-dev" in rule.agents

    def test_parse_routing_mode_parallel(self):
        """Test parsing parallel mode routing."""
        content = """
## Routing Rules
- task -> agent1 (parallel)
"""
        registry = AgentRegistry()
        model = registry.parse_content(content)

        assert model.routing_rules[0].mode == TaskMode.PARALLEL

    def test_parse_routing_mode_sequential(self):
        """Test parsing sequential mode routing."""
        content = """
## Routing Rules
- task -> agent1 (sequential)
"""
        registry = AgentRegistry()
        model = registry.parse_content(content)

        assert model.routing_rules[0].mode == TaskMode.SEQUENTIAL

    def test_parse_routing_mode_chinese(self):
        """Test parsing Chinese mode keywords."""
        content = """
## Routing Rules
- task1 -> agent1 (并发)
- task2 -> agent2 (串行)
"""
        registry = AgentRegistry()
        model = registry.parse_content(content)

        assert model.routing_rules[0].mode == TaskMode.PARALLEL
        assert model.routing_rules[1].mode == TaskMode.SEQUENTIAL

    def test_parse_ignores_unknown_sections(self):
        """Test that unknown sections are ignored."""
        content = """
## Unknown Section
- random content here
"""
        registry = AgentRegistry()
        model = registry.parse_content(content)

        assert model.roles == {}
        assert model.routing_rules == []


class TestAgentRegistryGetRole:
    """Tests for AgentRegistry.get_role() method."""

    def test_get_existing_role(self):
        """Test getting an existing role."""
        registry = AgentRegistry()
        model = AgentRegistryModel(roles={
            "architect": AgentRole(name="architect", description="Architect"),
        })

        role = registry.get_role(model, "architect")

        assert role is not None
        assert role.name == "architect"

    def test_get_nonexistent_role(self):
        """Test getting a nonexistent role returns None."""
        registry = AgentRegistry()
        model = AgentRegistryModel(roles={})

        role = registry.get_role(model, "nonexistent")

        assert role is None


class TestAgentRegistryGetRoutingRule:
    """Tests for AgentRegistry.get_routing_rule() method."""

    def test_get_exact_match(self):
        """Test getting routing rule with exact module match."""
        registry = AgentRegistry()
        model = AgentRegistryModel(routing_rules=[
            RoutingRule(module="api", agents=["backend-dev"]),
        ])

        rule = registry.get_routing_rule(model, "api")

        assert rule is not None
        assert rule.module == "api"

    def test_get_partial_match(self):
        """Test getting routing rule with partial match."""
        registry = AgentRegistry()
        model = AgentRegistryModel(routing_rules=[
            RoutingRule(module="api", agents=["backend-dev"]),
        ])

        rule = registry.get_routing_rule(model, "api/v1")

        assert rule is not None

    def test_get_no_match(self):
        """Test getting nonexistent routing rule returns None."""
        registry = AgentRegistry()
        model = AgentRegistryModel(routing_rules=[])

        rule = registry.get_routing_rule(model, "nonexistent")

        assert rule is None


class TestAgentRegistryGetDefaultRoles:
    """Tests for AgentRegistry.get_default_roles() method."""

    def test_returns_valid_model(self):
        """Test that default roles returns a valid model."""
        registry = AgentRegistry()
        model = registry.get_default_roles()

        assert isinstance(model, AgentRegistryModel)
        assert len(model.roles) > 0
        assert len(model.routing_rules) > 0

    def test_contains_standard_roles(self):
        """Test that default roles includes standard roles."""
        registry = AgentRegistry()
        model = registry.get_default_roles()

        assert "architect" in model.roles
        assert "backend-dev" in model.roles
        assert "frontend-dev" in model.roles
        assert "qa-engineer" in model.roles

    def test_standard_roles_have_tools(self):
        """Test that standard roles have tools defined."""
        registry = AgentRegistry()
        model = registry.get_default_roles()

        for role_name in ["architect", "backend-dev", "frontend-dev", "qa-engineer"]:
            role = model.roles.get(role_name)
            assert role is not None
            assert len(role.tools) > 0

    def test_routing_rules_include_architecture(self):
        """Test that routing includes architecture rule."""
        registry = AgentRegistry()
        model = registry.get_default_roles()

        arch_rule = next(
            (r for r in model.routing_rules if "架构设计" in r.module),
            None,
        )
        assert arch_rule is not None
        assert "architect" in arch_rule.agents
