"""CLI commands implementation for MyAgent."""

from __future__ import annotations

import sys
from pathlib import Path

from myagent import models
from myagent.config import load_config


def init_project(project_path: Path, name: str) -> None:
    """Initialize a new MyAgent project (UC-1).

    Creates:
    - project_dir/workflow.md
    - project_dir/agent.md
    - project_dir/PLANNING.md (empty)
    - project_dir/STATUS.md (empty)
    - project_dir/LOGS/ directory
    - project_dir/src/ directory
    """
    print(f"Initializing MyAgent project: {name}")

    # Create directory structure
    project_path.mkdir(parents=True, exist_ok=True)
    logs_dir = project_path / "LOGS"
    logs_dir.mkdir(exist_ok=True)
    src_dir = project_path / "src"
    src_dir.mkdir(exist_ok=True)

    # Create workflow.md from template
    workflow_template = Path(__file__).parent.parent.parent / "templates" / "workflow.md.template"
    if workflow_template.exists():
        workflow_content = workflow_template.read_text(encoding="utf-8")
    else:
        workflow_content = _default_workflow_template(name)

    workflow_file = project_path / "workflow.md"
    workflow_file.write_text(workflow_content, encoding="utf-8")

    # Create agent.md from template
    agent_template = Path(__file__).parent.parent.parent / "templates" / "agent.md.template"
    if agent_template.exists():
        agent_content = agent_template.read_text(encoding="utf-8")
    else:
        agent_content = _default_agent_template()

    agent_file = project_path / "agent.md"
    agent_file.write_text(agent_content, encoding="utf-8")

    # Create empty PLANNING.md
    planning_file = project_path / "PLANNING.md"
    planning_file.write_text("# PLANNING.md\n\n(Pending generation)\n", encoding="utf-8")

    # Create empty STATUS.md
    status_file = project_path / "STATUS.md"
    status_file.write_text("# STATUS.md\n\nProject Status: Initialized\n", encoding="utf-8")

    print(f"[OK] Project initialized: {project_path}")
    print(f"  - workflow.md")
    print(f"  - agent.md")
    print(f"  - PLANNING.md")
    print(f"  - STATUS.md")
    print(f"  - LOGS/")
    print(f"  - src/")


def run_phase(
    project_path: Path,
    phase: str,
    parallel: bool = False,
    watch: bool = False,
    resume: bool = False,
) -> None:
    """Run a workflow phase (UC-2, UC-4, UC-7).

    Args:
        project_path: Path to the project directory
        phase: "plan" or "execute"
        parallel: Enable parallel execution
        watch: Enable live progress watching
        resume: Resume from checkpoint
    """
    from myagent.workflow.parser import WorkflowParser
    from myagent.workflow.dag import DAGBuilder

    config = load_config(project_path)
    config.project_root = project_path
    config = config.resolve()

    print(f"[MyAgent] Running phase: {phase}")
    print(f"[MyAgent] Project: {project_path}")

    if not (project_path / "workflow.md").exists():
        print("ERROR: workflow.md not found. Run 'myagent init' first.")
        sys.exit(1)

    # Parse workflow
    parser = WorkflowParser()
    workflow = parser.parse(config.workflow.workflow_file)
    print(f"[MyAgent] Loaded {len(workflow.phases)} phases")

    # Build DAG
    dag_builder = DAGBuilder()
    dag = dag_builder.build(workflow)
    parallel_tasks = dag_builder.get_parallel_tasks(dag=dag)
    print(f"[MyAgent] DAG built with {len(parallel_tasks)} parallel tasks")

    if phase == "plan":
        from myagent.planner.planning_doc_generator import PlanningGenerator

        print("[MyAgent] Starting planning phase...")

        # Get first phase for planning
        first_phase = workflow.phases[0] if workflow.phases else None
        if not first_phase:
            print("ERROR: No phases defined in workflow.md")
            sys.exit(1)

        generator = PlanningGenerator(config)
        planning_doc = generator.generate(first_phase, workflow)

        # Save planning document
        planning_file = config.workflow.planning_file
        generator.save(planning_doc, planning_file)

        print(f"[MyAgent] Planning complete: {planning_file}")
        print("[MyAgent] Review PLANNING.md and run 'myagent confirm' to proceed.")

    elif phase == "execute":
        print(f"[MyAgent] Starting execution phase (parallel={parallel})...")

        if watch:
            print("[MyAgent] Press Ctrl+C to interrupt. Use 'myagent status --live' to monitor.")

        # Check if planning is confirmed
        planning_path = project_path / "PLANNING.md"
        if not planning_path.exists():
            print("ERROR: PLANNING.md not found. Run 'myagent run --phase plan' first.")
            sys.exit(1)

        from myagent.planner.planning_doc_generator import PlanningGenerator
        generator = PlanningGenerator()
        planning_doc = generator.load(planning_path)

        if not planning_doc.confirmed:
            print("ERROR: Planning not confirmed. Run 'myagent confirm --file PLANNING.md' first.")
            sys.exit(1)

        # Execute workflow using DeepAgents
        _execute_workflow(workflow, dag, config, parallel)

        print("[MyAgent] Execution complete.")


def _execute_workflow(workflow, dag, config, parallel: bool = False) -> None:
    """Execute workflow using DeepAgents.

    Args:
        workflow: Workflow model
        dag: DAG of tasks
        config: MyAgent config
        parallel: Enable parallel execution
    """
    from myagent.agents.deep_integration import AgentExecutor
    from myagent.progress.tracker import ProgressTracker

    # Initialize executor and progress tracker
    executor = AgentExecutor(
        provider=config.llm.provider,
        api_key=config.llm.api_key,
        model=config.llm.model,
    )
    tracker = ProgressTracker()

    # Get execution levels (phases that can run)
    try:
        levels = dag.get_execution_levels()
    except ValueError as e:
        print(f"[MyAgent] DAG error: {e}")
        return

    print(f"[MyAgent] Executing {len(levels)} phase levels")

    for level_idx, level in enumerate(levels):
        print(f"\n[MyAgent] Phase Level {level_idx + 1}/{len(levels)}")

        # Find phase nodes in this level
        phase_nodes = [n for n in level if dag.nodes[n].metadata.get("type") == "phase"]
        task_nodes = [n for n in level if dag.nodes[n].metadata.get("type") == "task"]

        # Execute phases (sequential)
        for phase_node_id in phase_nodes:
            phase_node = dag.nodes[phase_node_id]
            phase = phase_node.metadata["phase"]
            print(f"[MyAgent] Starting phase: {phase.name}")

            tracker.start_phase(phase)

            # Execute tasks in phase
            for task in phase.tasks:
                print(f"[MyAgent]   Executing task: {task.name} (owner: {', '.join(task.owner) or 'none'})")

                # Update progress
                tracker.update_task(phase.index, task.name, 0.0)

                # Get role
                role = task.owner[0] if task.owner else "architect"

                # Execute using DeepAgents
                try:
                    result = executor.execute_task(
                        task=f"Execute task: {task.name}",
                        role=role,
                        context={
                            "phase": phase.name,
                            "project_root": str(config.project_root),
                        }
                    )

                    if result.get("success"):
                        tracker.update_task(phase.index, task.name, 100.0)
                        print(f"[MyAgent]     SUCCESS: {task.name}")
                    else:
                        tracker.update_task(phase.index, task.name, 0.0, status="failed")
                        print(f"[MyAgent]     FAILED: {task.name} - {result.get('error', 'Unknown error')}")

                except Exception as e:
                    tracker.update_task(phase.index, task.name, 0.0, status="failed")
                    print(f"[MyAgent]     ERROR: {task.name} - {e}")

            tracker.complete_phase(phase.index)

        # Execute standalone tasks (if any)
        for task_node_id in task_nodes:
            task_node = dag.nodes[task_node_id]
            task = task_node.metadata["task"]
            phase = task_node.metadata.get("phase")

            if phase:
                continue  # Already executed with phase

            print(f"[MyAgent]   Executing standalone task: {task.name}")

            role = task.owner[0] if task.owner else "architect"

            try:
                result = executor.execute_task(
                    task=f"Execute task: {task.name}",
                    role=role,
                    context={"project_root": str(config.project_root)}
                )

                if result.get("success"):
                    print(f"[MyAgent]     SUCCESS: {task.name}")
                else:
                    print(f"[MyAgent]     FAILED: {task.name}")

            except Exception as e:
                print(f"[MyAgent]     ERROR: {task.name} - {e}")

    # Generate status report
    print(f"\n[MyAgent] Overall progress: {tracker.get_overall_progress():.1f}%")


def confirm_planning(project_path: Path, planning_file: str, revise: bool = False) -> None:
    """Confirm planning and proceed to execution (UC-3).

    Args:
        project_path: Path to the project directory
        planning_file: Path to the planning file
        revise: Whether this is a revision
    """
    from myagent.planner.planning_doc_generator import PlanningGenerator

    planning_path = project_path / planning_file

    if not planning_path.exists():
        print(f"ERROR: Planning file not found: {planning_path}")
        sys.exit(1)

    print(f"[MyAgent] Confirming planning: {planning_path}")

    # Load and validate planning
    generator = PlanningGenerator()
    planning_doc = generator.load(planning_path)

    if revise:
        print("[MyAgent] Marking as revision...")

    # Mark as confirmed
    planning_doc.confirmed = True
    generator.save(planning_doc, planning_path)

    print("[MyAgent] Planning confirmed. Ready for execution.")
    print("[MyAgent] Run 'myagent run --phase execute' to start execution.")


def show_status(project_path: Path, live: bool = False) -> None:
    """Show project status (UC-6).

    Args:
        project_path: Path to the project directory
        live: Enable live monitoring
    """
    status_file = project_path / "STATUS.md"

    if not status_file.exists():
        print("Status file not found.")
        return

    content = status_file.read_text()
    print(content)

    if live:
        print("\n[MyAgent] Live status monitoring not yet implemented.")


def show_logs(project_path: Path, agent: str, follow: bool = False) -> None:
    """Show agent logs (UC-6).

    Args:
        project_path: Path to the project directory
        agent: Agent name
        follow: Follow log output
    """
    logs_dir = project_path / "LOGS"

    if not logs_dir.exists():
        print("Logs directory not found.")
        return

    agent_log = logs_dir / f"{agent}.log"

    if not agent_log.exists():
        print(f"No logs found for agent: {agent}")
        return

    content = agent_log.read_text()
    print(f"=== Logs for {agent} ===\n")
    print(content)

    if follow:
        print("\n[MyAgent] Log following not yet implemented.")


def skip_task(project_path: Path, task: str) -> None:
    """Skip a task (UC-8).

    Args:
        project_path: Path to the project directory
        task: Task name to skip
    """
    print(f"[MyAgent] Skipping task: {task}")
    # TODO: Implement skip logic
    print("[MyAgent] Skip task not yet implemented.")


def rollback_task(project_path: Path, task: str) -> None:
    """Rollback a task (UC-8).

    Args:
        project_path: Path to the project directory
        task: Task name to rollback
    """
    print(f"[MyAgent] Rolling back task: {task}")
    # TODO: Implement rollback logic
    print("[MyAgent] Rollback task not yet implemented.")


def approve_operation(project_path: Path, operation: str) -> None:
    """Approve a dangerous operation (UC-8).

    Args:
        project_path: Path to the project directory
        operation: Operation ID to approve
    """
    print(f"[MyAgent] Approving operation: {operation}")
    # TODO: Implement approval logic
    print("[MyAgent] Approve operation not yet implemented.")


def reject_operation(project_path: Path, operation: str) -> None:
    """Reject a dangerous operation (UC-8).

    Args:
        project_path: Path to the project directory
        operation: Operation ID to reject
    """
    print(f"[MyAgent] Rejecting operation: {operation}")
    # TODO: Implement rejection logic
    print("[MyAgent] Reject operation not yet implemented.")


# Default templates

def _default_workflow_template(project_name: str) -> str:
    """Generate default workflow template."""
    return """# Workflow Configuration

## Phases

- [Phase 1] Requirements Analysis (depends: none)
  - Task: Architecture Design (parallel: false, owner: architect)

- [Phase 2] Core Module Development (depends: Phase 1)
  - Task: Module Development (parallel: true, owner: backend-dev, frontend-dev)

- [Phase 3] Integration and Testing (depends: Phase 2)
  - Task: Integration Testing (parallel: false, owner: qa-engineer)

## Rules

- Each phase output must pass automated checks (Lint/Test)
- Parallel tasks must use independent namespaces
- All changes must generate Commit Message and push to Feature Branch
"""


def _default_agent_template() -> str:
    """Generate default agent template."""
    return """# Agent Registry

## Roles

- architect: Architecture design, tech stack selection, PLANNING.md generation
- backend-dev: Python/Go/Java, business logic, API and database design
- frontend-dev: Vue/React, UI components, state management
- qa-engineer: Unit tests, integration tests, coverage validation

## Routing Rules

- Architecture Design -> architect (sequential)
- Core Module -> backend-dev + frontend-dev (parallel)
- Testing -> qa-engineer (sequential)
"""
