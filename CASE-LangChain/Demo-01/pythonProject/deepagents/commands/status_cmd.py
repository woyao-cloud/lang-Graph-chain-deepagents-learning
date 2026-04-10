"""
deepagents status 命令 - 查看状态
用法: deepagents status [--live]
"""

import typer
from typing import Optional
import time

status_app = typer.Typer(name="status", help="查看执行状态")


@status_app.command()
def status(
    live: bool = typer.Option(False, "--live", "-l", help="实时监控"),
):
    """
    查看当前执行状态
    """
    import os

    if not os.path.exists("STATUS.md"):
        typer.echo("📋 暂无执行状态（尚未运行或 STATUS.md 未生成）")
        typer.echo("   运行 deepagents run 启动执行")
        return

    with open("STATUS.md", "r", encoding="utf-8") as f:
        content = f.read()

    if live:
        typer.echo("🔄 实时监控中（Ctrl+C 退出）...")
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear")
                with open("STATUS.md", "r", encoding="utf-8") as f:
                    print(f.read())
                time.sleep(2)
        except KeyboardInterrupt:
            typer.echo("\n👋 退出监控")
    else:
        typer.echo(content)
