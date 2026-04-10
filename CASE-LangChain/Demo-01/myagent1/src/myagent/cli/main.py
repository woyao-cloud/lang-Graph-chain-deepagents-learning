"""CLI main entry point for MyAgent."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from myagent import __version__


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """MyAgent - 全自动化、可解释、可干预的工程级代码生成系统."""
    pass


@main.command()
@click.option("--name", required=True, help="项目名称")
@click.option("--path", default=".", help="项目路径")
def init(name: str, path: str) -> None:
    """初始化新项目 (UC-1)."""
    from myagent.cli.commands import init_project

    project_path = Path(path).resolve() / name
    init_project(project_path, name)


@main.command()
@click.option("--phase", required=True, type=click.Choice(["plan", "execute"]), help="执行阶段")
@click.option("--parallel", is_flag=True, help="启用并行执行")
@click.option("--watch", is_flag=True, help="实时监控进度")
@click.option("--resume", is_flag=True, help="从断点恢复")
@click.option("--project", default=".", help="项目路径")
def run(
    phase: str,
    parallel: bool,
    watch: bool,
    resume: bool,
    project: str,
) -> None:
    """启动执行 (UC-2, UC-4, UC-7)."""
    from myagent.cli.commands import run_phase

    project_path = Path(project).resolve()
    run_phase(
        project_path=project_path,
        phase=phase,
        parallel=parallel,
        watch=watch,
        resume=resume,
    )


@main.command()
@click.option("--file", default="PLANNING.md", help="规划文件路径")
@click.option("--revise", is_flag=True, help="标记为修订")
@click.option("--project", default=".", help="项目路径")
def confirm(file: str, revise: bool, project: str) -> None:
    """确认规划 (UC-3)."""
    from myagent.cli.commands import confirm_planning

    project_path = Path(project).resolve()
    confirm_planning(project_path, file, revise)


@main.command()
@click.option("--live", is_flag=True, help="实时监控")
@click.option("--project", default=".", help="项目路径")
def status(live: bool, project: str) -> None:
    """查看状态 (UC-6)."""
    from myagent.cli.commands import show_status

    project_path = Path(project).resolve()
    show_status(project_path, live)


@main.command()
@click.option("--agent", required=True, help="Agent 名称")
@click.option("--follow", is_flag=True, help="实时跟踪日志")
@click.option("--project", default=".", help="项目路径")
def logs(agent: str, follow: bool, project: str) -> None:
    """查看日志 (UC-6)."""
    from myagent.cli.commands import show_logs

    project_path = Path(project).resolve()
    show_logs(project_path, agent, follow)


@main.command()
@click.option("--task", required=True, help="任务名称")
@click.option("--project", default=".", help="项目路径")
def skip(task: str, project: str) -> None:
    """跳过任务 (UC-8)."""
    from myagent.cli.commands import skip_task

    project_path = Path(project).resolve()
    skip_task(project_path, task)


@main.command()
@click.option("--task", required=True, help="任务名称")
@click.option("--project", default=".", help="项目路径")
def rollback(task: str, project: str) -> None:
    """回退任务 (UC-8)."""
    from myagent.cli.commands import rollback_task

    project_path = Path(project).resolve()
    rollback_task(project_path, task)


@main.command()
@click.option("--operation", required=True, help="操作ID")
@click.option("--project", default=".", help="项目路径")
def approve(operation: str, project: str) -> None:
    """批准危险操作 (UC-8)."""
    from myagent.cli.commands import approve_operation

    project_path = Path(project).resolve()
    approve_operation(project_path, operation)


@main.command()
@click.option("--operation", required=True, help="操作ID")
@click.option("--project", default=".", help="项目路径")
def reject(operation: str, project: str) -> None:
    """拒绝危险操作 (UC-8)."""
    from myagent.cli.commands import reject_operation

    project_path = Path(project).resolve()
    reject_operation(project_path, operation)


if __name__ == "__main__":
    main()
