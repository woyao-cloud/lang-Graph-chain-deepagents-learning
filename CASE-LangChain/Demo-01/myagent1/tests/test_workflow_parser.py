"""Tests for workflow/parser.py module."""

from __future__ import annotations

from pathlib import Path

import pytest

from myagent.models import PhaseStatus, Task, TaskStatus, WorkflowModel
from myagent.workflow.parser import WorkflowParser


class TestWorkflowParserInit:
    """Tests for WorkflowParser initialization."""

    def test_default_init(self):
        """Test default initialization."""
        parser = WorkflowParser()
        assert parser is not None
        assert hasattr(parser, "PHASE_PATTERN")
        assert hasattr(parser, "TASK_PATTERN")
        assert hasattr(parser, "RULE_PATTERN")

    def test_patterns_are_compiled(self):
        """Test that regex patterns are compiled."""
        parser = WorkflowParser()
        assert parser.PHASE_PATTERN is not None
        assert parser.TASK_PATTERN is not None
        assert parser.RULE_PATTERN is not None


class TestWorkflowParserParse:
    """Tests for WorkflowParser.parse() method."""

    def test_parse_file_not_found(self, nonexistent_file: Path):
        """Test parsing a nonexistent file raises FileNotFoundError."""
        parser = WorkflowParser()
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.parse(nonexistent_file)
        assert "not found" in str(exc_info.value)

    def test_parse_valid_workflow(self, workflow_file: Path):
        """Test parsing a valid workflow file."""
        parser = WorkflowParser()
        workflow = parser.parse(workflow_file)

        assert isinstance(workflow, WorkflowModel)
        assert len(workflow.phases) == 3
        assert len(workflow.rules) == 2

    def test_parse_returns_workflow_model(self, workflow_file: Path):
        """Test that parse returns a WorkflowModel."""
        parser = WorkflowParser()
        workflow = parser.parse(workflow_file)

        assert hasattr(workflow, "phases")
        assert hasattr(workflow, "rules")
        assert hasattr(workflow, "raw_content")


class TestWorkflowParserParseContent:
    """Tests for WorkflowParser.parse_content() method."""

    def test_parse_content_empty(self):
        """Test parsing empty content."""
        parser = WorkflowParser()
        workflow = parser.parse_content("")

        assert workflow.phases == []
        assert workflow.rules == []
        assert workflow.raw_content == ""

    def test_parse_content_simple_phase(self):
        """Test parsing content with a simple phase."""
        content = """
- [Phase 1] Test Phase (depends: none)
  - Task: Test task (parallel: true, owner: architect)
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)

        assert len(workflow.phases) == 1
        phase = workflow.phases[0]
        assert phase.name == "Test Phase"
        assert phase.index == 1
        assert 'none' in phase.depends_on
        assert len(phase.tasks) == 1

    def test_parse_content_phase_with_dependency(self):
        """Test parsing phase with dependency."""
        content = """
- [Phase 2] Implementation (depends: Planning)
  - Task: Implement API (parallel: false, owner: backend-dev)
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)

        assert len(workflow.phases) == 1
        phase = workflow.phases[0]
        assert phase.depends_on == ["Planning"]

    def test_parse_content_multiple_dependencies(self):
        """Test parsing phase with multiple dependencies."""
        content = """
- [Phase 3] Final (depends: Phase 1, Phase 2)
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)

        assert len(workflow.phases) == 1
        assert workflow.phases[0].depends_on == ["Phase 1", "Phase 2"]

    def test_parse_content_tasks(self):
        """Test parsing tasks within a phase."""
        content = """
- [Phase 1] Planning (depends: none)
  - Task: Create spec (parallel: true, owner: architect)
  - Task: Create design (parallel: false, owner: architect)
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)

        phase = workflow.phases[0]
        assert len(phase.tasks) == 2

        task1 = phase.tasks[0]
        assert task1.name == "Create spec"
        assert task1.parallel is True
        assert task1.owner == ["architect"]

        task2 = phase.tasks[1]
        assert task2.name == "Create design"
        assert task2.parallel is False
        assert task2.owner == ["architect"]

    def test_parse_content_multiple_owners(self):
        """Test parsing task with multiple owners."""
        content = """
- [Phase 1] Planning (depends: none)
  - Task: Design system (parallel: true, owner: architect, backend-dev)
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)

        task = workflow.phases[0].tasks[0]
        assert task.owner == ["architect", "backend-dev"]

    def test_parse_content_rules_section(self):
        """Test parsing rules section."""
        content = """
## Rules
- Follow clean architecture
- Write tests first
- Use type hints
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)

        assert len(workflow.rules) == 3
        assert "Follow clean architecture" in workflow.rules
        assert "Write tests first" in workflow.rules
        assert "Use type hints" in workflow.rules

    def test_parse_content_rules_before_phases(self):
        """Test parsing rules section that comes before phases."""
        content = """
## Rules
- Rule 1
- Rule 2

- [Phase 1] Planning (depends: none)
  - Task: Task 1 (parallel: true, owner: architect)
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)

        assert len(workflow.rules) == 2
        assert len(workflow.phases) == 1

    def test_parse_content_preserves_raw_content(self):
        """Test that raw content is preserved."""
        content = "## Rules\n- Test rule\n"
        parser = WorkflowParser()
        workflow = parser.parse_content(content)

        assert workflow.raw_content == content


class TestWorkflowParserExtractPhases:
    """Tests for WorkflowParser.extract_phases() method."""

    def test_extract_phases(self):
        """Test extracting phases from content."""
        content = """
- [Phase 1] Planning (depends: none)
- [Phase 2] Implementation (depends: Planning)
"""
        parser = WorkflowParser()
        phases = parser.extract_phases(content)

        assert len(phases) == 2
        assert phases[0].name == "Planning"
        assert phases[1].name == "Implementation"

    def test_extract_phases_returns_list(self):
        """Test that extract_phases returns a list."""
        parser = WorkflowParser()
        phases = parser.extract_phases("")

        assert isinstance(phases, list)


class TestWorkflowParserExtractTasks:
    """Tests for WorkflowParser.extract_tasks() method."""

    def test_extract_tasks(self):
        """Test extracting tasks from a phase."""
        content = """
- [Phase 1] Planning (depends: none)
  - Task: Task 1 (parallel: true, owner: architect)
  - Task: Task 2 (parallel: false, owner: backend-dev)
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)
        phase = workflow.phases[0]

        tasks = parser.extract_tasks(phase)

        assert len(tasks) == 2
        assert tasks[0].name == "Task 1"
        assert tasks[1].name == "Task 2"


class TestWorkflowParserValidate:
    """Tests for WorkflowParser.validate() method."""

    def test_validate_empty_workflow(self):
        """Test validating empty workflow."""
        workflow = WorkflowModel(phases=[], rules=[])
        parser = WorkflowParser()
        errors = parser.validate(workflow)

        assert errors == []

    def test_validate_valid_workflow(self):
        """Test validating a valid workflow."""
        content = """
- [Phase 1] Planning (depends: none)
- [Phase 2] Implementation (depends: Planning)
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)
        errors = parser.validate(workflow)

        assert errors == []

    def test_validate_duplicate_phase_indices(self):
        """Test detecting duplicate phase indices."""
        from myagent.models import Phase

        workflow = WorkflowModel(phases=[
            Phase(name="Phase 1", index=1),
            Phase(name="Phase 2", index=1),  # Duplicate
        ])
        parser = WorkflowParser()
        errors = parser.validate(workflow)

        assert "Duplicate phase indices" in errors[0]

    def test_validate_nonexistent_dependency(self):
        """Test detecting nonexistent phase dependency."""
        content = """
- [Phase 1] Planning (depends: none)
- [Phase 2] Implementation (depends: NonExistentPhase)
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)
        errors = parser.validate(workflow)

        assert any("non-existent" in e for e in errors)

    def test_validate_valid_dependency_name(self):
        """Test that valid dependency names don't cause errors."""
        content = """
- [Phase 1] Planning (depends: none)
- [Phase 2] Implementation (depends: Planning)
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)
        errors = parser.validate(workflow)

        assert not any("non-existent" in e for e in errors)

    def test_validate_dependency_with_none(self):
        """Test that 'none' dependency is valid."""
        from myagent.models import Phase

        workflow = WorkflowModel(phases=[
            Phase(name="Phase 1", index=1, depends_on=["none"]),
        ])
        parser = WorkflowParser()
        errors = parser.validate(workflow)

        assert errors == []


class TestWorkflowParserHasCycle:
    """Tests for WorkflowParser._has_cycle() method."""

    def test_no_cycle_linear(self):
        """Test no cycle in linear workflow."""
        content = """
- [Phase 1] Planning (depends: none)
- [Phase 2] Implementation (depends: Planning)
- [Phase 3] Testing (depends: Implementation)
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)
        has_cycle = parser._has_cycle(workflow)

        assert has_cycle is False

    def test_no_cycle_parallel_starts(self):
        """Test no cycle when phases start in parallel."""
        content = """
- [Phase 1] Planning (depends: none)
- [Phase 2] Implementation (depends: none)
- [Phase 3] Final (depends: Planning, Implementation)
"""
        parser = WorkflowParser()
        workflow = parser.parse_content(content)
        has_cycle = parser._has_cycle(workflow)

        assert has_cycle is False

    def test_cycle_detected(self):
        """Test cycle detection."""
        from myagent.models import Phase, PhaseStatus

        # Manually create workflow with cycle
        workflow = WorkflowModel(phases=[
            Phase(name="Phase 1", index=1, depends_on=["Phase 3"]),
            Phase(name="Phase 2", index=2, depends_on=["Phase 1"]),
            Phase(name="Phase 3", index=3, depends_on=["Phase 2"]),
        ])
        parser = WorkflowParser()
        has_cycle = parser._has_cycle(workflow)

        assert has_cycle is True

    def test_cycle_simple_self_reference(self):
        """Test detecting simple self-reference cycle."""
        from myagent.models import Phase

        workflow = WorkflowModel(phases=[
            Phase(name="Phase 1", index=1, depends_on=["Phase 1"]),
        ])
        parser = WorkflowParser()
        has_cycle = parser._has_cycle(workflow)

        assert has_cycle is True
