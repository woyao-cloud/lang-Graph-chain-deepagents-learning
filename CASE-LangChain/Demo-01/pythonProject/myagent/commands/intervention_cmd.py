"""
人工干预命令 - skip / rollback / approve / reject
用法:
    myagent skip --task <task-name>
    myagent rollback --task <task-name>
    myagent approve --operation <operation-id>
    myagent reject --operation <operation-id>
"""

import typer

intervention_app = typer.Typer(help="人工干预命令（skip/rollback/approve/reject）")


@intervention_app.command("skip")
def skip(
    task: str = typer.Option(..., "--task", "-t", help="要跳过的任务名称"),
):
    """跳过指定任务"""
    typer.echo(f"⏭ 跳过任务: {task}")
    # TODO: 实现任务跳过逻辑


@intervention_app.command("rollback")
def rollback(
    task: str = typer.Option(..., "--task", "-t", help="要回退的任务名称"),
):
    """回退指定任务"""
    typer.echo(f"⏪ 回退任务: {task}")
    # TODO: 实现任务回退逻辑


@intervention_app.command("approve")
def approve(
    operation: str = typer.Option(..., "--operation", "-o", help="操作 ID"),
):
    """批准危险操作"""
    typer.echo(f"✅ 批准操作: {operation}")
    # TODO: 实现批准逻辑


@intervention_app.command("reject")
def reject(
    operation: str = typer.Option(..., "--operation", "-o", help="操作 ID"),
):
    """拒绝危险操作"""
    typer.echo(f"❌ 拒绝操作: {operation}")
    # TODO: 实现拒绝逻辑
