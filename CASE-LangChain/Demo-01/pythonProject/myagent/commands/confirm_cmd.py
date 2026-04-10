"""
myagent confirm 命令 - 确认规划
用法: myagent confirm [--file PLANNING.md] [--revise]
"""

import os
import typer
from typing import Optional

confirm_app = typer.Typer(name="confirm", help="确认 PLANNING.md 规划文档")


@confirm_app.command()
def confirm(
    file: str = typer.Option("PLANNING.md", "--file", "-f", help="规划文件路径"),
    revise: bool = typer.Option(False, "--revise", "-r", help="标记为修订版本"),
):
    """
    确认 PLANNING.md，开始执行阶段
    """
    if not os.path.exists(file):
        typer.echo(f"❌ 文件不存在: {file}")
        raise typer.Exit(1)

    with open(file, "r", encoding="utf-8") as f:
        content = f.read()

    if revise:
        typer.echo(f"📝 规划已修订，正在重新加载...")

    typer.echo(f"✅ 规划确认完成，开始执行...")
    typer.echo("   运行 myagent run --phase execute")
