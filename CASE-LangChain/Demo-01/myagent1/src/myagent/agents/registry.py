"""Agent registry for MyAgent.

Loads and manages agent roles from agent.md.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from myagent.models import AgentRegistryModel, AgentRole, RoutingRule, TaskMode

if TYPE_CHECKING:
    pass


class AgentRegistry:
    """Registry for agent roles and routing rules."""

    # Regex patterns
    ROLE_PATTERN = re.compile(r"^- (.+?):\s*(.+)$")
    ROUTING_PATTERN = re.compile(r"^-\s*(.+?)\s*->\s*(.+?)\s*\(?\s*(并发|串行|parallel|sequential)?\s*\)?$")

    def load(self, path: Path) -> AgentRegistryModel:
        """Load agent registry from file.

        Args:
            path: Path to agent.md file

        Returns:
            AgentRegistryModel
        """
        if not path.exists():
            raise FileNotFoundError(f"Agent registry file not found: {path}")

        content = path.read_text(encoding="utf-8")
        return self.parse_content(content)

    def parse_content(self, content: str) -> AgentRegistryModel:
        """Parse agent registry content.

        Args:
            content: agent.md content

        Returns:
            AgentRegistryModel
        """
        lines = content.split("\n")

        roles: dict[str, AgentRole] = {}
        routing_rules: list[RoutingRule] = []
        current_section = ""

        for line in lines:
            stripped = line.strip()

            # Track sections
            if stripped.lower() == "## roles":
                current_section = "roles"
                continue
            elif stripped.lower() == "## routing rules":
                current_section = "routing"
                continue

            # Parse role
            if current_section == "roles":
                role_match = self.ROLE_PATTERN.match(stripped)
                if role_match:
                    name = role_match.group(1).strip()
                    description = role_match.group(2).strip()
                    roles[name] = AgentRole(
                        name=name,
                        description=description,
                        tools=[],
                    )

            # Parse routing rule
            elif current_section == "routing":
                routing_match = self.ROUTING_PATTERN.match(stripped)
                if routing_match:
                    module = routing_match.group(1).strip()
                    agents_str = routing_match.group(2).strip()
                    mode_str = routing_match.group(3) or "并发"

                    agents = [a.strip() for a in agents_str.split("+")]
                    mode = TaskMode.PARALLEL if mode_str in ("并发", "parallel") else TaskMode.SEQUENTIAL

                    routing_rules.append(RoutingRule(
                        module=module,
                        agents=agents,
                        mode=mode,
                    ))

        return AgentRegistryModel(
            roles=roles,
            routing_rules=routing_rules,
        )

    def get_role(self, registry: AgentRegistryModel, name: str) -> AgentRole | None:
        """Get role by name.

        Args:
            registry: Agent registry model
            name: Role name

        Returns:
            AgentRole or None
        """
        return registry.roles.get(name)

    def get_routing_rule(self, registry: AgentRegistryModel, module: str) -> RoutingRule | None:
        """Get routing rule for a module.

        Args:
            registry: Agent registry model
            module: Module name

        Returns:
            RoutingRule or None
        """
        for rule in registry.routing_rules:
            if module in rule.module or rule.module in module:
                return rule
        return None

    def get_default_roles(self) -> AgentRegistryModel:
        """Get default agent roles.

        Returns:
            AgentRegistryModel with default roles
        """
        roles = {
            "architect": AgentRole(
                name="architect",
                description="负责架构设计、技术选型、PLANNING.md 生成与接口契约定义",
                tools=["read_file", "write_file", "edit_file", "grep", "glob"],
            ),
            "backend-dev": AgentRole(
                name="backend-dev",
                description="精通 Python/Go/Java，负责业务逻辑、API 与数据库设计",
                tools=["read_file", "write_file", "edit_file", "execute"],
            ),
            "frontend-dev": AgentRole(
                name="frontend-dev",
                description="精通 Vue/React，负责 UI 组件、状态管理与路由",
                tools=["read_file", "write_file", "edit_file", "execute"],
            ),
            "qa-engineer": AgentRole(
                name="qa-engineer",
                description="负责单元测试、集成测试用例生成与覆盖率校验",
                tools=["read_file", "write_file", "execute"],
            ),
        }

        routing_rules = [
            RoutingRule(module="架构设计", agents=["architect"], mode=TaskMode.SEQUENTIAL),
            RoutingRule(module="核心模块", agents=["backend-dev", "frontend-dev"], mode=TaskMode.PARALLEL),
            RoutingRule(module="测试", agents=["qa-engineer"], mode=TaskMode.SEQUENTIAL),
        ]

        return AgentRegistryModel(
            roles=roles,
            routing_rules=routing_rules,
        )
