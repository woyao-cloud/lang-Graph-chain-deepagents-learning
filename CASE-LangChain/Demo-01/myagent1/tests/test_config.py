"""Tests for config.py module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from myagent.config import (
    BackendConfig,
    HITLConfig,
    LLMConfig,
    MyAgentConfig,
    QualityGateConfig,
    VCSConfig,
    WorkflowConfig,
    load_config,
)


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = LLMConfig()
        assert config.provider == "anthropic"
        assert config.model == "claude-sonnet-4-6"
        assert config.api_key is None
        assert config.base_url is None
        assert config.max_tokens == 8192
        assert config.temperature == 0.0

    def test_from_env_with_env_vars(self, mock_env_vars: None):
        """Test loading config from environment variables."""
        config = LLMConfig.from_env()
        assert config.provider == "anthropic"
        assert config.model == "claude-sonnet-4-6"
        assert config.api_key == "test-api-key"

    def test_from_env_openai_provider(self):
        """Test loading OpenAI config from environment."""
        with patch.dict("os.environ", {
            "MYAGENT_LLM_PROVIDER": "openai",
            "MYAGENT_LLM_MODEL": "gpt-4",
            "OPENAI_API_KEY": "openai-key",
        }, clear=False):
            config = LLMConfig.from_env()
            assert config.provider == "openai"
            assert config.model == "gpt-4"
            assert config.api_key == "openai-key"

    def test_from_env_unknown_provider(self):
        """Test loading unknown provider config."""
        with patch.dict("os.environ", {
            "MYAGENT_LLM_PROVIDER": "unknown",
            "MYAGENT_LLM_MODEL": "model-x",
        }, clear=False):
            config = LLMConfig.from_env()
            assert config.provider == "unknown"
            assert config.api_key is None

    def test_custom_values(self):
        """Test custom configuration values."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4-turbo",
            api_key="secret-key",
            base_url="https://custom.api.com",
            max_tokens=4096,
            temperature=0.7,
        )
        assert config.provider == "openai"
        assert config.model == "gpt-4-turbo"
        assert config.api_key == "secret-key"
        assert config.base_url == "https://custom.api.com"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7


class TestBackendConfig:
    """Tests for BackendConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = BackendConfig()
        assert config.backend_type == "filesystem"
        assert config.root_dir == Path.cwd()
        assert config.sandbox_enabled is True

    def test_from_env(self, mock_env_vars: None):
        """Test loading config from environment variables."""
        config = BackendConfig.from_env()
        assert config.root_dir == Path("/tmp/myagent")
        assert config.sandbox_enabled is True

    def test_from_env_sandbox_disabled(self):
        """Test loading config with sandbox disabled."""
        with patch.dict("os.environ", {
            "MYAGENT_SANDBOX_ENABLED": "false",
        }, clear=False):
            config = BackendConfig.from_env()
            assert config.sandbox_enabled is False

    def test_from_env_sandbox_various_true_values(self):
        """Test various true values for sandbox."""
        for value in ("true", "1", "yes"):
            with patch.dict("os.environ", {
                "MYAGENT_SANDBOX_ENABLED": value,
            }, clear=False):
                config = BackendConfig.from_env()
                assert config.sandbox_enabled is True


class TestWorkflowConfig:
    """Tests for WorkflowConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = WorkflowConfig()
        assert config.workflow_file == Path("workflow.md")
        assert config.agent_file == Path("agent.md")
        assert config.planning_file == Path("PLANNING.md")
        assert config.status_file == Path("STATUS.md")
        assert config.logs_dir == Path("LOGS")

    def test_resolve_for_project(self, temp_dir: Path):
        """Test resolving paths for a project root."""
        project_root = temp_dir / "myproject"
        project_root.mkdir()

        config = WorkflowConfig()
        resolved = config.resolve_for_project(project_root)

        assert resolved.workflow_file == project_root / "workflow.md"
        assert resolved.agent_file == project_root / "agent.md"
        assert resolved.planning_file == project_root / "PLANNING.md"
        assert resolved.status_file == project_root / "STATUS.md"
        assert resolved.logs_dir == project_root / "LOGS"

    def test_resolve_returns_new_instance(self):
        """Test that resolve_for_project returns a new instance."""
        config = WorkflowConfig()
        project_root = Path("/tmp/project")

        resolved = config.resolve_for_project(project_root)

        # Verify it's a new instance
        assert resolved is not config
        assert config.workflow_file == Path("workflow.md")


class TestQualityGateConfig:
    """Tests for QualityGateConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = QualityGateConfig()
        assert config.lint_enabled is True
        assert config.test_enabled is True
        assert config.schema_check_enabled is False
        assert config.security_scan_enabled is False
        assert config.lint_command == "pylint"
        assert config.test_command == "pytest"
        assert config.max_retries == 3

    def test_custom_values(self):
        """Test custom configuration values."""
        config = QualityGateConfig(
            lint_enabled=False,
            test_enabled=False,
            max_retries=5,
        )
        assert config.lint_enabled is False
        assert config.test_enabled is False
        assert config.max_retries == 5


class TestVCSConfig:
    """Tests for VCSConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = VCSConfig()
        assert config.auto_commit is True
        assert config.auto_branch is True
        assert config.auto_pr is False
        assert config.base_branch == "main"
        assert config.commit_prefix == "feat"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = VCSConfig(
            auto_commit=False,
            auto_branch=False,
            base_branch="develop",
            commit_prefix="fix",
        )
        assert config.auto_commit is False
        assert config.auto_branch is False
        assert config.base_branch == "develop"
        assert config.commit_prefix == "fix"


class TestHITLConfig:
    """Tests for HITLConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = HITLConfig()
        assert config.interrupt_on_dangerous is True
        assert config.require_confirmation is True
        assert len(config.dangerous_patterns) > 0
        assert r"rm\s+-rf" in config.dangerous_patterns
        assert r"git\s+push\s+--force" in config.dangerous_patterns

    def test_dangerous_patterns_field_factory(self):
        """Test that dangerous_patterns uses field factory."""
        config1 = HITLConfig()
        config2 = HITLConfig()

        # Verify separate instances
        config1.dangerous_patterns.append("custom-pattern")
        assert "custom-pattern" not in config2.dangerous_patterns

    def test_custom_patterns(self):
        """Test custom dangerous patterns."""
        patterns = [r"drop\s+table", r"format\s+disk"]
        config = HITLConfig(dangerous_patterns=patterns)
        assert config.dangerous_patterns == patterns


class TestMyAgentConfig:
    """Tests for MyAgentConfig dataclass."""

    def test_default_values(self, mock_env_vars: None):
        """Test default configuration values."""
        config = MyAgentConfig()
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.backend, BackendConfig)
        assert isinstance(config.workflow, WorkflowConfig)
        assert isinstance(config.quality, QualityGateConfig)
        assert isinstance(config.vcs, VCSConfig)
        assert isinstance(config.hitl, HITLConfig)
        assert config.project_root == Path.cwd()

    def test_resolve(self, temp_dir: Path):
        """Test resolving all paths."""
        config = MyAgentConfig(project_root=temp_dir)
        resolved = config.resolve()

        # Verify resolved paths
        assert resolved.workflow.workflow_file == temp_dir / "workflow.md"
        assert resolved.workflow.agent_file == temp_dir / "agent.md"
        assert resolved.workflow.logs_dir == temp_dir / "LOGS"
        assert resolved.project_root == temp_dir

    def test_resolve_returns_new_instance(self):
        """Test that resolve returns a new instance."""
        config = MyAgentConfig()
        resolved = config.resolve()

        assert resolved is not config
        assert resolved.workflow is not config.workflow


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_default(self, mock_env_vars: None):
        """Test loading config with default project root."""
        config = load_config()
        assert isinstance(config, MyAgentConfig)
        assert config.project_root == Path.cwd()

    def test_load_config_custom_root(self, temp_dir: Path):
        """Test loading config with custom project root."""
        config = load_config(project_root=temp_dir)
        assert config.project_root == temp_dir

    def test_load_config_resolves_paths(self, temp_dir: Path):
        """Test that load_config resolves all paths."""
        config = load_config(project_root=temp_dir)
        assert config.workflow.workflow_file == temp_dir / "workflow.md"
        assert config.workflow.logs_dir == temp_dir / "LOGS"
