"""
deepagents init 命令 - 初始化项目
用法: deepagents init --name <project-name>
"""

import os
import typer
from pathlib import Path
from typing import Optional

init_app = typer.Typer(name="init", help="Initialize project, generate workflow.md and agent.md")


DEFAULT_WORKFLOW_MD = """# Workflow Configuration

## Phases

- [Phase 1] 需求分析与架构设计 (depends: none)
  - Task: 架构设计 (owner: architect)
- [Phase 2] 核心模块开发 (depends: Phase 1)
  - Task: 模块A开发 (parallel: true, owner: backend-dev)
  - Task: 模块B开发 (parallel: true, owner: backend-dev, frontend-dev)
- [Phase 3] 联调与测试 (depends: Phase 2)
  - Task: 集成测试 (owner: qa-engineer)
- [Phase 4] 部署与交付 (depends: Phase 3)

## Rules

- 每阶段输出必须通过自动化校验（Lint/Test）
- 并行任务需使用独立命名空间，避免文件冲突
- 所有变更需自动生成 Commit Message 并推送至 Feature Branch
- 危险操作（rm -rf、git push --force）需人工二次确认
"""

DEFAULT_AGENT_MD = """# Agent Registry

## Roles

- architect:
    description: 负责架构设计、技术选型、PLANNING.md 生成与接口契约定义
    tools: [read_file, write_file, edit_file, glob, grep, execute]
    model: openai/gpt-4o

- backend-dev:
    description: 精通 Python/Go/Java，负责业务逻辑、API 与数据库设计
    tools: [read_file, write_file, edit_file, glob, grep, execute, git_status, git_commit]
    model: openai/gpt-4o

- frontend-dev:
    description: 精通 Vue/React，负责 UI 组件、状态管理与路由
    tools: [read_file, write_file, edit_file, glob, grep, execute]
    model: openai/gpt-4o

- qa-engineer:
    description: 负责单元测试、集成测试用例生成与覆盖率校验
    tools: [read_file, write_file, glob, grep, execute, run_tests]
    model: openai/gpt-4o

## Routing Rules

- 架构设计 -> architect (串行)
- 后端业务模块 -> backend-dev (并发)
- 前端模块 -> frontend-dev (并发)
- 测试任务 -> qa-engineer (串行)
- 全局协调 -> architect (串行主导)
"""


@init_app.command()
def init(
    name: str = typer.Option(..., "--name", "-n", help="项目名称"),
    force: bool = typer.Option(False, "--force", "-f", help="强制覆盖已存在的文件"),
    project_dir: Optional[str] = typer.Option(None, "--dir", "-d", help="项目目录（默认当前目录）"),
):
    """
    初始化新项目，生成 workflow.md 和 agent.md 配置文件
    """
    target_dir = Path(project_dir) if project_dir else Path.cwd()
    project_name = name

    typer.echo(f"[*] Initializing project: {project_name}")
    typer.echo(f"[*] Project directory: {target_dir}")

    files_created = []

    # workflow.md
    workflow_path = target_dir / "workflow.md"
    _write_if_not_exists(workflow_path, DEFAULT_WORKFLOW_MD, force, files_created, "workflow.md")

    # agent.md
    agent_path = target_dir / "agent.md"
    _write_if_not_exists(agent_path, DEFAULT_AGENT_MD, force, files_created, "agent.md")

    # 创建目录结构
    dirs_created = []
    for subdir in ["src", "LOGS", "LOGS/workflow", "LOGS/agents", "LOGS/quality"]:
        d = target_dir / subdir
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            dirs_created.append(subdir)

    if files_created or dirs_created:
        typer.echo(f"\n[*] Project initialized!")
        typer.echo(f"\nCreated files:")
        for f in files_created:
            typer.echo(f"  - {f}")
        if dirs_created:
            typer.echo(f"\nCreated directories:")
            for d in dirs_created:
                typer.echo(f"  - {d}/")
        typer.echo("\n[*] Next: deepagents run --phase plan")
    else:
        typer.echo("\n[!] Files exist, use --force to overwrite")


def _write_if_not_exists(path: Path, content: str, force: bool, files_list: list, display_name: str):
    """Write file if not exists or force=True"""
    if path.exists() and not force:
        typer.echo(f"[!] {display_name} exists, skipped (use --force to overwrite)")
        return
    path.write_text(content, encoding="utf-8")
    files_list.append(display_name)
