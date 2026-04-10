"""Configuration management for MyAgent."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str = "anthropic"  # anthropic, openai, google, etc.
    model: str = "claude-sonnet-4-6"
    api_key: str | None = None
    base_url: str | None = None
    max_tokens: int = 8192
    temperature: float = 0.0

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Load configuration from environment variables."""
        provider = os.getenv("MYAGENT_LLM_PROVIDER", "anthropic")
        model = os.getenv("MYAGENT_LLM_MODEL", "claude-sonnet-4-6")

        # Get API key based on provider
        if provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
        else:
            api_key = None

        base_url = os.getenv("MYAGENT_LLM_BASE_URL")
        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
        )


@dataclass
class BackendConfig:
    """Backend configuration for DeepAgents."""
    backend_type: str = "filesystem"  # filesystem, state, store
    root_dir: Path = Path.cwd()
    sandbox_enabled: bool = True

    @classmethod
    def from_env(cls) -> BackendConfig:
        """Load configuration from environment variables."""
        root_str = os.getenv("MYAGENT_ROOT_DIR", str(Path.cwd()))
        sandbox = os.getenv("MYAGENT_SANDBOX_ENABLED", "true").lower() in ("true", "1", "yes")
        return cls(
            root_dir=Path(root_str),
            sandbox_enabled=sandbox,
        )


@dataclass
class WorkflowConfig:
    """Workflow configuration."""
    workflow_file: Path = Path("workflow.md")
    agent_file: Path = Path("agent.md")
    planning_file: Path = Path("PLANNING.md")
    status_file: Path = Path("STATUS.md")
    logs_dir: Path = Path("LOGS")

    def resolve_for_project(self, project_root: Path) -> WorkflowConfig:
        """Resolve paths relative to project root."""
        return WorkflowConfig(
            workflow_file=project_root / self.workflow_file,
            agent_file=project_root / self.agent_file,
            planning_file=project_root / self.planning_file,
            status_file=project_root / self.status_file,
            logs_dir=project_root / self.logs_dir,
        )


@dataclass
class QualityGateConfig:
    """Quality gate configuration."""
    lint_enabled: bool = True
    test_enabled: bool = True
    schema_check_enabled: bool = False
    security_scan_enabled: bool = False
    lint_command: str = "pylint"
    test_command: str = "pytest"
    max_retries: int = 3


@dataclass
class VCSConfig:
    """Version control configuration."""
    auto_commit: bool = True
    auto_branch: bool = True
    auto_pr: bool = False
    base_branch: str = "main"
    commit_prefix: str = "feat"


@dataclass
class HITLConfig:
    """Human-in-the-loop configuration."""
    interrupt_on_dangerous: bool = True
    require_confirmation: bool = True
    dangerous_patterns: list[str] = field(default_factory=lambda: [
        r"rm\s+-rf",
        r"git\s+push\s+--force",
        r"sudo",
        r"chmod\s+777",
        r"drop\s+database",
    ])


@dataclass
class MyAgentConfig:
    """Main configuration for MyAgent."""
    llm: LLMConfig = field(default_factory=LLMConfig.from_env)
    backend: BackendConfig = field(default_factory=BackendConfig.from_env)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    quality: QualityGateConfig = field(default_factory=QualityGateConfig)
    vcs: VCSConfig = field(default_factory=VCSConfig)
    hitl: HITLConfig = field(default_factory=HITLConfig)
    project_root: Path = Path.cwd()

    def resolve(self) -> MyAgentConfig:
        """Resolve all paths relative to project root."""
        resolved = MyAgentConfig(
            llm=self.llm,
            backend=self.backend,
            workflow=self.workflow.resolve_for_project(self.project_root),
            quality=self.quality,
            vcs=self.vcs,
            hitl=self.hitl,
            project_root=self.project_root,
        )
        return resolved


def load_config(project_root: Path | None = None) -> MyAgentConfig:
    """Load MyAgent configuration."""
    root = project_root or Path.cwd()
    config = MyAgentConfig(project_root=root)
    return config.resolve()
