"""Pytest configuration and fixtures for MyAgent tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_workflow_content() -> str:
    """Sample workflow.md content for testing."""
    return """# Workflow

## Rules
- Follow clean architecture
- Write tests first

- [Phase 1] Planning (depends: none)
  - Task: Create architecture (parallel: true, owner: architect)
  - Task: Design database (parallel: false, owner: backend-dev)

- [Phase 2] Implementation (depends: Planning)
  - Task: Implement API (parallel: false, owner: backend-dev)
  - Task: Implement UI (parallel: true, owner: frontend-dev)

- [Phase 3] Testing (depends: Implementation)
  - Task: Write tests (parallel: false, owner: qa-engineer)
"""


@pytest.fixture
def sample_agent_content() -> str:
    """Sample agent.md content for testing."""
    return """# Agent Roles

## Roles
- architect: 负责架构设计、技术选型、PLANNING.md 生成与接口契约定义
- backend-dev: 精通 Python/Go/Java，负责业务逻辑、API 与数据库设计
- frontend-dev: 精通 Vue/React，负责 UI 组件、状态管理与路由
- qa-engineer: 负责单元测试、集成测试用例生成与覆盖率校验

## Routing Rules
- 架构设计 -> architect (sequential)
- 核心模块 -> backend-dev + frontend-dev (parallel)
- 测试 -> qa-engineer (sequential)
"""


@pytest.fixture
def mock_env_vars() -> Generator[None, None, None]:
    """Set up mock environment variables."""
    original_env = os.environ.copy()

    os.environ["MYAGENT_LLM_PROVIDER"] = "anthropic"
    os.environ["MYAGENT_LLM_MODEL"] = "claude-sonnet-4-6"
    os.environ["ANTHROPIC_API_KEY"] = "test-api-key"
    os.environ["MYAGENT_ROOT_DIR"] = "/tmp/myagent"
    os.environ["MYAGENT_SANDBOX_ENABLED"] = "true"

    yield

    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def workflow_file(temp_dir: Path, sample_workflow_content: str) -> Path:
    """Create a temporary workflow.md file."""
    path = temp_dir / "workflow.md"
    path.write_text(sample_workflow_content, encoding="utf-8")
    return path


@pytest.fixture
def agent_file(temp_dir: Path, sample_agent_content: str) -> Path:
    """Create a temporary agent.md file."""
    path = temp_dir / "agent.md"
    path.write_text(sample_agent_content, encoding="utf-8")
    return path


@pytest.fixture
def nonexistent_file(temp_dir: Path) -> Path:
    """Path to a nonexistent file."""
    return temp_dir / "nonexistent.md"
