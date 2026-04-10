"""
myagent run 命令 - 启动执行
用法: myagent run --phase <plan|execute> [--parallel] [--watch] [--resume]
"""

import typer
from typing import Optional

run_app = typer.Typer(name="run", help="启动工作流执行")


@run_app.command()
def run(
    phase: str = typer.Option("plan", "--phase", "-p", help="执行阶段: plan, execute"),
    parallel: bool = typer.Option(False, "--parallel", help="启用并行执行"),
    watch: bool = typer.Option(False, "--watch", help="实时监控进度"),
    resume: bool = typer.Option(False, "--resume", help="从断点恢复执行"),
):
    """
    启动工作流执行

    phase: plan - 生成 PLANNING.md
    phase: execute - 执行 Sub-Agent 任务
    """
    from myagent.workflow.parser import WorkflowParser
    from myagent.workflow.dag import DAGBuilder
    from myagent.agents.supervisor import SupervisorAgent

    typer.echo(f"[run] phase={phase}, parallel={parallel}, watch={watch}, resume={resume}")

    # 检查配置文件
    import os
    if not os.path.exists("workflow.md"):
        typer.echo("❌ workflow.md 不存在，请先运行 myagent init")
        raise typer.Exit(1)

    # 解析工作流
    parser = WorkflowParser()
    workflow = parser.parse_file("workflow.md")

    # 构建 DAG
    dag = DAGBuilder(workflow).build()

    typer.echo(f"✅ 工作流解析完成: {len(dag.phases)} 个 Phase")
    for phase_obj in dag.phases:
        typer.echo(f"  - {phase_obj.name} (depends: {phase_obj.depends})")

    if resume:
        typer.echo("🔄 从断点恢复...")
        # TODO: 实现断点续跑

    if phase == "plan":
        typer.echo("📋 进入规划阶段...")
        supervisor = SupervisorAgent()
        supervisor.generate_planning()
        typer.echo("✅ PLANNING.md 已生成，等待确认...")
        typer.echo("   运行 myagent confirm 确认规划")

    elif phase == "execute":
        typer.echo("🚀 进入执行阶段...")
        # TODO: 实现 Sub-Agent 调度
        typer.echo("⚠ 执行阶段暂未实现")

    else:
        typer.echo(f"❌ 未知阶段: {phase}")
        raise typer.Exit(1)
