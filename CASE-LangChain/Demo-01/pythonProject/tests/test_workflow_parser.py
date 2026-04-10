"""
Tests for Workflow Parser
FR-WF-001: 工作流解析模块
"""

import pytest
from pathlib import Path
import tempfile
import os

from myagent.workflow.parser import WorkflowParser, Workflow, Phase, Task


class TestWorkflowParser:
    """工作流解析器测试"""

    def test_parse_simple_workflow(self):
        """测试解析简单工作流"""
        content = """
## Phases

- [Phase 1] 需求分析 (depends: none)
  - Task: 需求调研 (owner: architect)

## Rules

- 每阶段输出必须通过自动化校验
"""
        parser = WorkflowParser()
        workflow = parser.parse(content)

        assert len(workflow.phases) == 1
        assert workflow.phases[0].name == "[Phase 1] 需求分析"
        assert len(workflow.phases[0].tasks) == 1
        assert workflow.phases[0].tasks[0].name == "需求调研"

    def test_parse_workflow_with_dependencies(self):
        """测试解析带依赖的工作流"""
        content = """
## Phases

- [Phase 1] 架构设计 (depends: none)
- [Phase 2] 开发 (depends: Phase 1)

## Rules

- 每阶段输出必须通过自动化校验
"""
        parser = WorkflowParser()
        workflow = parser.parse(content)

        assert len(workflow.phases) == 2
        assert workflow.phases[0].depends == []
        assert workflow.phases[1].depends == ["Phase 1"]

    def test_parse_parallel_tasks(self):
        """测试解析并行任务"""
        content = """
## Phases

- [Phase 1] 开发 (depends: none)
  - Task: 前端开发 (parallel: true, owner: frontend-dev)
  - Task: 后端开发 (parallel: true, owner: backend-dev)

## Rules

- 并行任务需独立命名空间
"""
        parser = WorkflowParser()
        workflow = parser.parse(content)

        assert len(workflow.phases[0].tasks) == 2
        assert workflow.phases[0].tasks[0].parallel == True
        assert workflow.phases[0].tasks[0].owner == ["frontend-dev"]
        assert workflow.phases[0].tasks[1].parallel == True
        assert workflow.phases[0].tasks[1].owner == ["backend-dev"]

    def test_validate_no_cycle(self):
        """测试无循环依赖"""
        content = """
## Phases

- [Phase 1] A (depends: none)
- [Phase 2] B (depends: Phase 1)
- [Phase 3] C (depends: Phase 2)

## Rules

- 无循环依赖
"""
        parser = WorkflowParser()
        workflow = parser.parse(content)
        errors = parser.validate(workflow)

        cycle_errors = [e for e in errors if "cycle" in e.lower()]
        assert len(cycle_errors) == 0

    def test_parse_from_file(self):
        """测试从文件解析"""
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""
## Phases

- [Phase 1] 测试 (depends: none)
  - Task: 单元测试 (owner: qa-engineer)

## Rules

- 测试必须通过
""")
            temp_path = f.name

        try:
            parser = WorkflowParser()
            workflow = parser.parse_file(temp_path)
            assert len(workflow.phases) == 1
            assert workflow.phases[0].tasks[0].name == "单元测试"
        finally:
            os.unlink(temp_path)


class TestTask:
    """Task 测试"""

    def test_task_creation(self):
        """测试 Task 创建"""
        task = Task(
            name="测试任务",
            owner=["qa-engineer"],
            parallel=True
        )
        assert task.name == "测试任务"
        assert task.owner == ["qa-engineer"]
        assert task.parallel == True


class TestPhase:
    """Phase 测试"""

    def test_phase_creation(self):
        """测试 Phase 创建"""
        phase = Phase(
            name="[Phase 1] 开发",
            depends=["Phase 0"],
            tasks=[
                Task(name="任务1", owner=["backend-dev"], parallel=True)
            ]
        )
        assert phase.name == "[Phase 1] 开发"
        assert phase.depends == ["Phase 0"]
        assert len(phase.tasks) == 1
