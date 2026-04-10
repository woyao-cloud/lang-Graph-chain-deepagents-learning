"""
deepagents logs 命令 - 查看日志
用法: deepagents logs --agent <agent-name> [--follow]
"""

import typer
from typing import Optional

logs_app = typer.Typer(name="logs", help="查看 Sub-Agent 执行日志")


@logs_app.command()
def logs(
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="指定 Agent 名称"),
    follow: bool = typer.Option(False, "--follow", "-f", help="实时跟踪日志"),
):
    """
    查看 Sub-Agent 执行日志
    """
    import os
    from pathlib import Path

    logs_dir = Path("LOGS/agents")

    if not logs_dir.exists():
        typer.echo("❌ 日志目录不存在（LOGS/agents/）")
        return

    if agent:
        agent_log_dir = logs_dir / agent
        if not agent_log_dir.exists():
            typer.echo(f"❌ Agent 日志不存在: {agent}")
            typer.echo(f"   可用的 Agent: {', '.join([d.name for d in logs_dir.iterdir() if d.is_dir()])}")
            return

        log_files = list(agent_log_dir.glob("*.log"))
        if not log_files:
            typer.echo(f"⚠ Agent {agent} 暂无日志")
            return

        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        with open(latest_log, "r", encoding="utf-8") as f:
            content = f.read()

        if follow:
            typer.echo(f"🔄 跟踪 {agent} 日志中（Ctrl+C 退出）...")
            try:
                with open(latest_log, "r", encoding="utf-8") as f:
                    while True:
                        line = f.readline()
                        if line:
                            print(line, end="")
                        time.sleep(0.5)
            except KeyboardInterrupt:
                typer.echo("\n👋 退出跟踪")
        else:
            typer.echo(f"=== {agent} 日志 ===")
            typer.echo(content)
    else:
        typer.echo("📋 可用的 Agent 日志:")
        for d in logs_dir.iterdir():
            if d.is_dir():
                typer.echo(f"  - {d.name}/")
