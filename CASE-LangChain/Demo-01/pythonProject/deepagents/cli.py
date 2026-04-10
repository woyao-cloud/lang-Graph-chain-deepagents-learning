"""
DeepAgents CLI 入口
用法: deepagents <command> [options]
"""

import sys
import typer
from typing import Optional

app = typer.Typer(
    name="deepagents",
    help="DeepAgents Code Agent - 全自动化、可解释、可干预的工程级代码生成系统",
    add_completion=False,
)

# 注册子命令
from deepagents.commands.init_cmd import init_app
from deepagents.commands.run_cmd import run_app
from deepagents.commands.confirm_cmd import confirm_app
from deepagents.commands.status_cmd import status_app
from deepagents.commands.logs_cmd import logs_app
from deepagents.commands.intervention_cmd import intervention_app


@app.callback()
def callback():
    """DeepAgents Code Agent"""
    pass


# 注册各子命令
app.add_typer(init_app, name="init")
app.add_typer(run_app, name="run")
app.add_typer(confirm_app, name="confirm")
app.add_typer(status_app, name="status")
app.add_typer(logs_app, name="logs")
app.add_typer(intervention_app, name="")


def main():
    app()


if __name__ == "__main__":
    main()
