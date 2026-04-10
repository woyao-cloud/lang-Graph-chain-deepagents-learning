"""Tests for planner/planning_doc_generator.py module."""

from __future__ import annotations

from pathlib import Path

import pytest

from myagent.models import (
    Phase,
    PlanningDocument,
    SubTask,
    Task,
    TaskTree,
    WorkflowModel,
)
from myagent.planner.planning_doc_generator import PlanningGenerator, TaskDecomposer


class TestTaskDecomposer:
    """Tests for TaskDecomposer class."""

    def test_default_init(self):
        """Test default initialization."""
        decomposer = TaskDecomposer()
        assert decomposer is not None

    def test_decompose_creates_root(self):
        """Test that decompose creates a root subtask."""
        decomposer = TaskDecomposer()
        result = decomposer.decompose("TestTask", {})

        assert result.name == "TestTask"
        assert "TestTask" in result.description

    def test_decompose_creates_children(self):
        """Test that decompose creates child subtasks."""
        decomposer = TaskDecomposer()
        result = decomposer.decompose("TestTask", {})

        assert len(result.children) == 4
        child_names = [c.name for c in result.children]
        assert "TestTask:analyze" in child_names
        assert "TestTask:design" in child_names
        assert "TestTask:implement" in child_names
        assert "TestTask:test" in child_names

    def test_decompose_preserves_context(self):
        """Test that decompose uses context."""
        context = {"key": "value"}
        decomposer = TaskDecomposer()
        result = decomposer.decompose("Task", context)

        # Just verify it doesn't crash - context is used in real impl
        assert result is not None


class TestPlanningGeneratorInit:
    """Tests for PlanningGenerator initialization."""

    def test_default_init(self):
        """Test default initialization."""
        generator = PlanningGenerator()
        assert generator is not None
        assert generator.config is None
        assert isinstance(generator.decomposer, TaskDecomposer)

    def test_init_with_config(self):
        """Test initialization with config."""
        from myagent.config import MyAgentConfig

        config = MyAgentConfig()
        generator = PlanningGenerator(config=config)

        assert generator.config is config


class TestPlanningGeneratorGenerate:
    """Tests for PlanningGenerator.generate() method."""

    def test_generate_empty_phase(self):
        """Test generating planning for empty phase."""
        phase = Phase(name="Empty", index=1, tasks=[])
        workflow = WorkflowModel(phases=[phase])

        generator = PlanningGenerator()
        planning = generator.generate(phase, workflow)

        assert isinstance(planning, PlanningDocument)
        assert planning.title == "Planning: Empty"
        assert planning.confirmed is False

    def test_generate_with_tasks(self):
        """Test generating planning with tasks."""
        phase = Phase(name="Planning", index=1, tasks=[
            Task(name="Design", parallel=True, owner=["architect"]),
        ])
        workflow = WorkflowModel(phases=[phase])

        generator = PlanningGenerator()
        planning = generator.generate(phase, workflow)

        assert len(planning.task_tree.root.children) == 1

    def test_generate_populates_fields(self):
        """Test that generate populates all fields."""
        phase = Phase(name="Test", index=1, tasks=[
            Task(name="Task1", parallel=True, owner=["architect"]),
        ])
        workflow = WorkflowModel(phases=[phase])

        generator = PlanningGenerator()
        planning = generator.generate(phase, workflow)

        assert planning.task_tree is not None
        assert isinstance(planning.tech_stack, dict)
        assert isinstance(planning.file_structure, list)
        assert isinstance(planning.risks, list)

    def test_generate_suggests_tech_stack(self):
        """Test tech stack suggestion based on owners."""
        phase = Phase(name="Backend", index=1, tasks=[
            Task(name="API", parallel=True, owner=["backend-dev"]),
        ])
        workflow = WorkflowModel(phases=[phase])

        generator = PlanningGenerator()
        planning = generator.generate(phase, workflow)

        assert "Backend" in planning.tech_stack

    def test_generate_identifies_risks(self):
        """Test risk identification."""
        phase = Phase(name="Parallel", index=1, tasks=[
            Task(name="Task1", parallel=True, owner=["architect", "backend-dev", "frontend-dev", "qa"]),
        ])
        workflow = WorkflowModel(phases=[phase])

        generator = PlanningGenerator()
        planning = generator.generate(phase, workflow)

        # Should have risks for parallel task and many owners
        assert len(planning.risks) >= 2


class TestPlanningGeneratorGenerateMarkdown:
    """Tests for PlanningGenerator.generate_markdown() method."""

    def test_generate_markdown_basic(self):
        """Test basic markdown generation."""
        root = SubTask(name="root", description="Root task", children=[])
        task_tree = TaskTree(
            root=root,
            tech_stack={"Python": "3.11"},
            file_structure=["src/main.py"],
            api_contracts=[],
            risks=[],
        )
        planning = PlanningDocument(
            title="Test Planning",
            task_tree=task_tree,
            tech_stack=task_tree.tech_stack,
            file_structure=task_tree.file_structure,
            api_contracts=[],
            risks=[],
        )

        generator = PlanningGenerator()
        markdown = generator.generate_markdown(planning)

        assert "# Test Planning" in markdown
        assert "## 任务分解" in markdown
        assert "## 技术栈" in markdown
        assert "**Python**: 3.11" in markdown
        assert "`src/main.py`" in markdown

    def test_generate_markdown_with_api_contracts(self):
        """Test markdown generation with API contracts."""
        root = SubTask(name="root", description="Root", children=[])
        task_tree = TaskTree(
            root=root,
            tech_stack={},
            file_structure=[],
            api_contracts=[{"name": "Test API", "schema": "schema内容"}],
            risks=[],
        )
        planning = PlanningDocument(
            title="Test",
            task_tree=task_tree,
            tech_stack={},
            file_structure=[],
            api_contracts=task_tree.api_contracts,
            risks=[],
        )

        generator = PlanningGenerator()
        markdown = generator.generate_markdown(planning)

        assert "## API 契约" in markdown
        assert "### Test API" in markdown

    def test_generate_markdown_with_risks(self):
        """Test markdown generation with risks."""
        root = SubTask(name="root", description="Root", children=[])
        task_tree = TaskTree(
            root=root,
            tech_stack={},
            file_structure=[],
            api_contracts=[],
            risks=["Risk 1", "Risk 2"],
        )
        planning = PlanningDocument(
            title="Test",
            task_tree=task_tree,
            tech_stack={},
            file_structure=[],
            api_contracts=[],
            risks=task_tree.risks,
        )

        generator = PlanningGenerator()
        markdown = generator.generate_markdown(planning)

        assert "## 风险识别" in markdown
        assert "Risk 1" in markdown
        assert "Risk 2" in markdown

    def test_generate_markdown_with_checklist(self):
        """Test markdown generation includes confirmation checklist."""
        root = SubTask(name="root", description="Root", children=[])
        task_tree = TaskTree(
            root=root,
            tech_stack={},
            file_structure=[],
            api_contracts=[],
            risks=[],
        )
        planning = PlanningDocument(
            title="Test",
            task_tree=task_tree,
            tech_stack={},
            file_structure=[],
            api_contracts=[],
            risks=[],
        )

        generator = PlanningGenerator()
        markdown = generator.generate_markdown(planning)

        assert "## 确认" in markdown
        assert "- [ ] 已阅读并确认上述规划" in markdown


class TestPlanningGeneratorRenderTaskTree:
    """Tests for PlanningGenerator._render_task_tree() method."""

    def test_render_simple_tree(self):
        """Test rendering a simple task tree."""
        generator = PlanningGenerator()
        task = SubTask(
            name="Root",
            description="Root task",
            children=[
                SubTask(name="Child1", description="Child 1"),
            ],
        )

        output = generator._render_task_tree(task, 0)

        assert "Root" in output
        assert "Child1" in output

    def test_render_tree_with_grandchildren(self):
        """Test rendering tree with grandchildren."""
        generator = PlanningGenerator()
        task = SubTask(
            name="Root",
            description="Root task",
            children=[
                SubTask(
                    name="Child1",
                    description="Child 1",
                    children=[
                        SubTask(name="Grandchild", description="Grandchild task"),
                    ],
                ),
            ],
        )

        output = generator._render_task_tree(task, 0)

        assert "Root" in output
        assert "Child1" in output
        assert "Grandchild" in output


class TestPlanningGeneratorSuggestTechStack:
    """Tests for PlanningGenerator._suggest_tech_stack() method."""

    def test_suggest_for_backend_dev(self):
        """Test tech stack suggestion for backend-dev."""
        phase = Phase(name="Backend", index=1, tasks=[
            Task(name="API", owner=["backend-dev"]),
        ])
        generator = PlanningGenerator()
        stack = generator._suggest_tech_stack(phase)

        assert "Backend" in stack

    def test_suggest_for_frontend_dev(self):
        """Test tech stack suggestion for frontend-dev."""
        phase = Phase(name="Frontend", index=1, tasks=[
            Task(name="UI", owner=["frontend-dev"]),
        ])
        generator = PlanningGenerator()
        stack = generator._suggest_tech_stack(phase)

        assert "Frontend" in stack

    def test_suggest_for_qa_engineer(self):
        """Test tech stack suggestion for qa-engineer."""
        phase = Phase(name="Testing", index=1, tasks=[
            Task(name="Tests", owner=["qa-engineer"]),
        ])
        generator = PlanningGenerator()
        stack = generator._suggest_tech_stack(phase)

        assert "Testing" in stack

    def test_suggest_for_architect(self):
        """Test tech stack suggestion for architect."""
        phase = Phase(name="Architecture", index=1, tasks=[
            Task(name="Design", owner=["architect"]),
        ])
        generator = PlanningGenerator()
        stack = generator._suggest_tech_stack(phase)

        assert "Architecture" in stack

    def test_suggest_default_when_no_owner(self):
        """Test default tech stack when no specific owner."""
        phase = Phase(name="Unknown", index=1, tasks=[
            Task(name="Task", owner=[]),
        ])
        generator = PlanningGenerator()
        stack = generator._suggest_tech_stack(phase)

        assert "Language" in stack


class TestPlanningGeneratorSuggestFileStructure:
    """Tests for PlanningGenerator._suggest_file_structure() method."""

    def test_suggest_default_structure(self):
        """Test default file structure."""
        phase = Phase(name="Basic", index=1, tasks=[
            Task(name="Task", owner=[]),
        ])
        generator = PlanningGenerator()
        structure = generator._suggest_file_structure(phase)

        assert "src/" in structure
        assert "tests/" in structure
        assert "requirements.txt" in structure

    def test_suggest_extended_for_backend(self):
        """Test extended structure for backend tasks."""
        phase = Phase(name="Backend", index=1, tasks=[
            Task(name="Backend API", owner=["backend-dev"]),
        ])
        generator = PlanningGenerator()
        structure = generator._suggest_file_structure(phase)

        assert "src/api/routes.py" in structure
        assert "src/services/" in structure

    def test_suggest_extended_for_frontend(self):
        """Test extended structure for frontend tasks."""
        phase = Phase(name="Frontend", index=1, tasks=[
            Task(name="UI Components", owner=["frontend-dev"]),
        ])
        generator = PlanningGenerator()
        structure = generator._suggest_file_structure(phase)

        assert "src/ui/" in structure
        assert "src/ui/components/" in structure


class TestPlanningGeneratorIdentifyRisks:
    """Tests for PlanningGenerator._identify_risks() method."""

    def test_identifies_parallel_risk(self):
        """Test risk identification for parallel tasks."""
        phase = Phase(name="Test", index=1, tasks=[
            Task(name="ParallelTask", parallel=True, owner=["architect"]),
        ])
        generator = PlanningGenerator()
        risks = generator._identify_risks(phase)

        assert any("并行" in r for r in risks)

    def test_identifies_multi_owner_risk(self):
        """Test risk identification for multi-owner tasks."""
        phase = Phase(name="Test", index=1, tasks=[
            Task(name="MultiOwner", parallel=False, owner=["a", "b", "c"]),
        ])
        generator = PlanningGenerator()
        risks = generator._identify_risks(phase)

        assert any("协作成本" in r for r in risks)

    def test_no_risks_default(self):
        """Test default risk when no specific risks."""
        phase = Phase(name="Test", index=1, tasks=[
            Task(name="Simple", parallel=False, owner=["architect"]),
        ])
        generator = PlanningGenerator()
        risks = generator._identify_risks(phase)

        assert "无明显风险" in risks


class TestPlanningGeneratorSave:
    """Tests for PlanningGenerator.save() method."""

    def test_save_creates_file(self, temp_dir: Path):
        """Test saving planning document."""
        root = SubTask(name="root", description="Root", children=[])
        planning = PlanningDocument(
            title="Test",
            task_tree=TaskTree(root=root, tech_stack={}, file_structure=[], api_contracts=[], risks=[]),
            tech_stack={},
            file_structure=[],
            api_contracts=[],
            risks=[],
        )

        generator = PlanningGenerator()
        path = temp_dir / "planning.md"
        generator.save(planning, path)

        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "# Test" in content

    def test_save_creates_parent_dirs(self, temp_dir: Path):
        """Test that save creates parent directories."""
        root = SubTask(name="root", description="Root", children=[])
        planning = PlanningDocument(
            title="Test",
            task_tree=TaskTree(root=root, tech_stack={}, file_structure=[], api_contracts=[], risks=[]),
            tech_stack={},
            file_structure=[],
            api_contracts=[],
            risks=[],
        )

        generator = PlanningGenerator()
        path = temp_dir / "subdir" / "nested" / "planning.md"
        generator.save(planning, path)

        assert path.exists()


class TestPlanningGeneratorLoad:
    """Tests for PlanningGenerator.load() method."""

    def test_load_basic_file(self, temp_dir: Path):
        """Test loading planning document."""
        content = """# Test Planning

## 任务分解
- Task 1
- Task 2

## 确认
- [x] 已阅读并确认上述规划
"""
        path = temp_dir / "planning.md"
        path.write_text(content, encoding="utf-8")

        generator = PlanningGenerator()
        planning = generator.load(path)

        assert planning.title == "planning"
        assert planning.confirmed is True
        assert planning.path == path

    def test_load_unconfirmed_file(self, temp_dir: Path):
        """Test loading unconfirmed planning document."""
        content = """# Test Planning

## 确认
- [ ] 未确认
"""
        path = temp_dir / "unconfirmed.md"
        path.write_text(content, encoding="utf-8")

        generator = PlanningGenerator()
        planning = generator.load(path)

        assert planning.confirmed is False
