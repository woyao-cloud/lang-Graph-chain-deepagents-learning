"""
Integration Tests - 端到端测试
"""

import pytest
import tempfile
import os
import shutil


class TestProjectInit:
    """项目初始化测试"""

    @pytest.mark.skip(reason="Click/Typer version compatibility issue")
    def test_init_creates_workflow_and_agent_files(self):
        """测试初始化创建 workflow 和 agent 文件"""
        pass  # Skipped due to Click/Typer version issues


class TestDAGBuilder:
    """DAG 构建器测试"""

    def test_build_dag_from_workflow(self):
        """测试从工作流构建 DAG"""
        from deepagents.workflow.parser import WorkflowParser
        from deepagents.workflow.dag import DAGBuilder

        content = """
## Phases

- [Phase 1] 设计 (depends: none)
  - Task: 架构设计 (owner: architect)
- [Phase 2] 开发 (depends: Phase 1)
  - Task: 前端开发 (parallel: true, owner: frontend-dev)
  - Task: 后端开发 (parallel: true, owner: backend-dev)

## Rules

- 并行执行无依赖任务
"""
        parser = WorkflowParser()
        workflow = parser.parse(content)

        dag = DAGBuilder(workflow).build()

        assert len(dag.nodes) == 5  # 2 phases + 3 tasks
        assert len(dag.phases) == 2

    def test_topological_sort(self):
        """测试拓扑排序"""
        from deepagents.workflow.parser import WorkflowParser
        from deepagents.workflow.dag import DAGBuilder

        content = """
## Phases

- [Phase 1] A (depends: none)
- [Phase 2] B (depends: Phase 1)
- [Phase 3] C (depends: Phase 2)

## Rules

- 顺序执行
"""
        parser = WorkflowParser()
        workflow = parser.parse(content)

        dag = DAGBuilder(workflow).build()
        sorted_nodes = dag.topological_sort()

        # 验证顺序正确
        phase_order = [n.name for n in sorted_nodes if n.node_type == "phase"]
        assert phase_order.index("[Phase 1] A") < phase_order.index("[Phase 2] B")
        assert phase_order.index("[Phase 2] B") < phase_order.index("[Phase 3] C")


class TestProgressTracker:
    """进度追踪器测试"""

    def test_track_phase_progress(self):
        """测试阶段进度追踪"""
        from deepagents.state.progress import ProgressTracker

        tracker = ProgressTracker("test_project")
        tracker.set_total_phases(3)

        assert tracker._progress.total_phases == 3

    def test_track_task_progress(self):
        """测试任务进度追踪"""
        from deepagents.state.progress import ProgressTracker

        tracker = ProgressTracker("test_project")
        tracker.start_task("task1", "任务1", "backend-dev", "Phase 1")

        assert tracker._progress.phases["Phase 1"].tasks["task1"].status == "running"


class TestCheckpointManager:
    """检查点管理器测试"""

    def test_save_and_load_checkpoint(self):
        """测试保存和加载检查点"""
        from deepagents.state.checkpoint import CheckpointManager, WorkflowState, AgentState

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(tmpdir)

            workflow_state = WorkflowState(
                current_phase="Phase 2",
                completed_phases=["Phase 1"],
                task_status={"task1": "completed"}
            )

            agent_state = AgentState(
                messages=[{"role": "user", "content": "test"}],
                files={},
                todos=[]
            )

            checkpoint_path = manager.save_checkpoint(
                "test_checkpoint",
                workflow_state,
                agent_state
            )

            assert os.path.exists(checkpoint_path)

            loaded = manager.load_checkpoint("test_checkpoint")
            assert loaded is not None
            assert loaded.workflow.current_phase == "Phase 2"
