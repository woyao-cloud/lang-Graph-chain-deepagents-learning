"""Tests for workflow/dag.py module."""

from __future__ import annotations

import pytest

from myagent.models import (
    Phase,
    Task,
    TaskStatus,
    WorkflowModel,
)
from myagent.workflow.dag import DAG, DAGBuilder, DAGNode


class TestDAGNode:
    """Tests for DAGNode dataclass."""

    def test_default_init(self):
        """Test default initialization."""
        node = DAGNode(id="test-id", name="Test Node")

        assert node.id == "test-id"
        assert node.name == "Test Node"
        assert node.dependencies == []
        assert node.dependents == []
        assert node.metadata == {}

    def test_with_dependencies(self):
        """Test node with dependencies."""
        node = DAGNode(
            id="node-1",
            name="Node 1",
            dependencies=["dep-1", "dep-2"],
            dependents=["child-1"],
            metadata={"type": "phase"},
        )

        assert len(node.dependencies) == 2
        assert len(node.dependents) == 1
        assert node.metadata["type"] == "phase"

    def test_metadata_dict(self):
        """Test metadata as dictionary."""
        node = DAGNode(
            id="test",
            name="Test",
            metadata={"key": "value", "count": 42},
        )

        assert node.metadata["key"] == "value"
        assert node.metadata["count"] == 42


class TestDAGInit:
    """Tests for DAG initialization."""

    def test_default_init(self):
        """Test default DAG initialization."""
        dag = DAG()

        assert dag.nodes == {}

    def test_nodes_dict(self):
        """Test that nodes is a dictionary."""
        dag = DAG()
        assert isinstance(dag.nodes, dict)


class TestDAGAddNode:
    """Tests for DAG.add_node() method."""

    def test_add_single_node(self):
        """Test adding a single node."""
        dag = DAG()
        node = DAGNode(id="node-1", name="Node 1")

        dag.add_node(node)

        assert "node-1" in dag.nodes
        assert dag.nodes["node-1"] is node

    def test_add_multiple_nodes(self):
        """Test adding multiple nodes."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))
        dag.add_node(DAGNode(id="node-2", name="Node 2"))

        assert len(dag.nodes) == 2
        assert "node-1" in dag.nodes
        assert "node-2" in dag.nodes

    def test_add_node_replaces_existing(self):
        """Test that adding node with same ID replaces existing."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))
        dag.add_node(DAGNode(id="node-1", name="Node 1 Updated"))

        assert dag.nodes["node-1"].name == "Node 1 Updated"


class TestDAGAddEdge:
    """Tests for DAG.add_edge() method."""

    def test_add_edge_basic(self):
        """Test adding a basic edge."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))
        dag.add_node(DAGNode(id="node-2", name="Node 2"))

        dag.add_edge("node-1", "node-2")

        assert "node-2" in dag.nodes["node-1"].dependents
        assert "node-1" in dag.nodes["node-2"].dependencies

    def test_add_edge_source_not_found(self):
        """Test adding edge with nonexistent source raises ValueError."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))

        with pytest.raises(ValueError) as exc_info:
            dag.add_edge("nonexistent", "node-1")

        assert "not found" in str(exc_info.value)

    def test_add_edge_target_not_found(self):
        """Test adding edge with nonexistent target raises ValueError."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))

        with pytest.raises(ValueError) as exc_info:
            dag.add_edge("node-1", "nonexistent")

        assert "not found" in str(exc_info.value)

    def test_add_edge_circular_safe(self):
        """Test that edges don't automatically create cycles."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))
        dag.add_node(DAGNode(id="node-2", name="Node 2"))
        dag.add_node(DAGNode(id="node-3", name="Node 3"))

        # A -> B -> C is fine
        dag.add_edge("node-1", "node-2")
        dag.add_edge("node-2", "node-3")

        assert len(dag.nodes["node-1"].dependents) == 1
        assert len(dag.nodes["node-3"].dependencies) == 1


class TestDAGGetParallelTasks:
    """Tests for DAG.get_parallel_tasks() method."""

    def test_get_parallel_tasks_empty(self):
        """Test getting parallel tasks from empty DAG."""
        dag = DAG()
        parallel = dag.get_parallel_tasks()

        assert parallel == []

    def test_get_parallel_tasks_no_dependencies(self):
        """Test getting parallel tasks when nodes have no dependencies."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))
        dag.add_node(DAGNode(id="node-2", name="Node 2"))

        parallel = dag.get_parallel_tasks()

        assert len(parallel) == 2
        assert "node-1" in parallel
        assert "node-2" in parallel

    def test_get_parallel_tasks_with_dependencies(self):
        """Test getting parallel tasks when some have dependencies."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))
        dag.add_node(DAGNode(id="node-2", name="Node 2"))
        dag.add_node(DAGNode(id="node-3", name="Node 3"))
        dag.add_edge("node-1", "node-3")

        parallel = dag.get_parallel_tasks()

        assert len(parallel) == 2
        assert "node-1" in parallel
        assert "node-2" in parallel
        assert "node-3" not in parallel


class TestDAGTopologicalSort:
    """Tests for DAG.topological_sort() method."""

    def test_topological_sort_empty(self):
        """Test topological sort on empty DAG."""
        dag = DAG()
        sorted_nodes = dag.topological_sort()

        assert sorted_nodes == []

    def test_topological_sort_single_node(self):
        """Test topological sort with single node."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))

        sorted_nodes = dag.topological_sort()

        assert sorted_nodes == ["node-1"]

    def test_topological_sort_linear(self):
        """Test topological sort on linear graph."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))
        dag.add_node(DAGNode(id="node-2", name="Node 2"))
        dag.add_node(DAGNode(id="node-3", name="Node 3"))
        dag.add_edge("node-1", "node-2")
        dag.add_edge("node-2", "node-3")

        sorted_nodes = dag.topological_sort()

        # node-1 must come before node-2, node-2 before node-3
        assert sorted_nodes.index("node-1") < sorted_nodes.index("node-2")
        assert sorted_nodes.index("node-2") < sorted_nodes.index("node-3")

    def test_topological_sort_parallel(self):
        """Test topological sort on parallel graph."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))
        dag.add_node(DAGNode(id="node-2", name="Node 2"))
        dag.add_node(DAGNode(id="node-3", name="Node 3"))
        dag.add_edge("node-1", "node-3")
        dag.add_edge("node-2", "node-3")

        sorted_nodes = dag.topological_sort()

        # node-1 and node-2 must come before node-3
        assert sorted_nodes.index("node-3") > sorted_nodes.index("node-1")
        assert sorted_nodes.index("node-3") > sorted_nodes.index("node-2")

    def test_topological_sort_with_cycle(self):
        """Test that topological sort detects cycle."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))
        dag.add_node(DAGNode(id="node-2", name="Node 2"))
        dag.add_edge("node-1", "node-2")
        dag.add_edge("node-2", "node-1")  # Cycle

        with pytest.raises(ValueError) as exc_info:
            dag.topological_sort()

        assert "Cycle" in str(exc_info.value)


class TestDAGGetExecutionLevels:
    """Tests for DAG.get_execution_levels() method."""

    def test_execution_levels_empty(self):
        """Test execution levels on empty DAG."""
        dag = DAG()
        levels = dag.get_execution_levels()

        assert levels == []

    def test_execution_levels_single_level(self):
        """Test execution levels with single level."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))

        levels = dag.get_execution_levels()

        assert len(levels) == 1
        assert levels[0] == ["node-1"]

    def test_execution_levels_multiple_levels(self):
        """Test execution levels with multiple levels."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))
        dag.add_node(DAGNode(id="node-2", name="Node 2"))
        dag.add_node(DAGNode(id="node-3", name="Node 3"))
        dag.add_edge("node-1", "node-3")
        dag.add_edge("node-2", "node-3")

        levels = dag.get_execution_levels()

        assert len(levels) == 2
        assert set(levels[0]) == {"node-1", "node-2"}
        assert levels[1] == ["node-3"]

    def test_execution_levels_with_cycle(self):
        """Test execution levels detects cycle."""
        dag = DAG()
        dag.add_node(DAGNode(id="node-1", name="Node 1"))
        dag.add_node(DAGNode(id="node-2", name="Node 2"))
        dag.add_edge("node-1", "node-2")
        dag.add_edge("node-2", "node-1")

        with pytest.raises(ValueError) as exc_info:
            dag.get_execution_levels()

        assert "Cycle" in str(exc_info.value)


class TestDAGBuilderBuild:
    """Tests for DAGBuilder.build() method."""

    def test_build_empty_workflow(self):
        """Test building DAG from empty workflow."""
        workflow = WorkflowModel(phases=[])
        builder = DAGBuilder()
        dag = builder.build(workflow)

        assert len(dag.nodes) == 0

    def test_build_single_phase(self):
        """Test building DAG with single phase."""
        workflow = WorkflowModel(phases=[
            Phase(name="Planning", index=1),
        ])
        builder = DAGBuilder()
        dag = builder.build(workflow)

        assert len(dag.nodes) == 1
        assert "phase:1" in dag.nodes

    def test_build_with_dependencies(self):
        """Test building DAG with phase dependencies."""
        workflow = WorkflowModel(phases=[
            Phase(name="Planning", index=1, depends_on=[]),
            Phase(name="Implementation", index=2, depends_on=["Planning"]),
        ])
        builder = DAGBuilder()
        dag = builder.build(workflow)

        assert len(dag.nodes) == 2
        assert "phase:1" in dag.nodes
        assert "phase:2" in dag.nodes

    def test_build_with_tasks(self):
        """Test building DAG with tasks."""
        workflow = WorkflowModel(phases=[
            Phase(name="Planning", index=1, tasks=[
                Task(name="Design", parallel=True, owner=["architect"]),
            ]),
        ])
        builder = DAGBuilder()
        dag = builder.build(workflow)

        # Should have phase node and task node
        assert len(dag.nodes) == 2
        assert "phase:1" in dag.nodes
        assert "task:1:Design" in dag.nodes

    def test_build_task_edges(self):
        """Test that tasks are connected to their phase."""
        workflow = WorkflowModel(phases=[
            Phase(name="Planning", index=1, tasks=[
                Task(name="Design", parallel=True, owner=["architect"]),
            ]),
        ])
        builder = DAGBuilder()
        dag = builder.build(workflow)

        phase_node = dag.nodes["phase:1"]
        task_node = dag.nodes["task:1:Design"]

        # Phase should have task as dependent
        assert "task:1:Design" in phase_node.dependents
        # Task should have phase as dependency
        assert "phase:1" in task_node.dependencies

    def test_build_sequential_tasks(self):
        """Test that sequential tasks have dependencies."""
        workflow = WorkflowModel(phases=[
            Phase(name="Implementation", index=1, tasks=[
                Task(name="Task1", parallel=False, owner=["backend-dev"]),
                Task(name="Task2", parallel=False, owner=["backend-dev"]),
            ]),
        ])
        builder = DAGBuilder()
        dag = builder.build(workflow)

        task1 = dag.nodes["task:1:Task1"]
        task2 = dag.nodes["task:1:Task2"]

        # Task2 should depend on Task1 (sequential)
        assert "task:1:Task2" in task1.dependents
        assert "task:1:Task1" in task2.dependencies


class TestDAGBuilderFindPhaseId:
    """Tests for DAGBuilder._find_phase_id() method."""

    def test_find_by_index(self):
        """Test finding phase ID by index."""
        workflow = WorkflowModel(phases=[
            Phase(name="Planning", index=1),
        ])
        builder = DAGBuilder()

        phase_id = builder._find_phase_id(workflow, "1")

        assert phase_id == "phase:1"

    def test_find_by_name(self):
        """Test finding phase ID by name."""
        workflow = WorkflowModel(phases=[
            Phase(name="Planning", index=1),
        ])
        builder = DAGBuilder()

        phase_id = builder._find_phase_id(workflow, "Planning")

        assert phase_id == "phase:1"

    def test_find_by_name_with_prefix(self):
        """Test finding phase ID with 'Phase ' prefix."""
        workflow = WorkflowModel(phases=[
            Phase(name="Planning", index=1),
        ])
        builder = DAGBuilder()

        phase_id = builder._find_phase_id(workflow, "Phase 1")

        assert phase_id == "phase:1"

    def test_find_not_found(self):
        """Test finding non-existent phase returns None."""
        workflow = WorkflowModel(phases=[
            Phase(name="Planning", index=1),
        ])
        builder = DAGBuilder()

        phase_id = builder._find_phase_id(workflow, "NonExistent")

        assert phase_id is None


class TestDAGBuilderGetParallelTasks:
    """Tests for DAGBuilder.get_parallel_tasks() method."""

    def test_get_parallel_tasks_empty(self):
        """Test getting parallel tasks from empty workflow."""
        builder = DAGBuilder()

        parallel = builder.get_parallel_tasks(workflow=WorkflowModel(phases=[]))

        assert parallel == []

    def test_get_parallel_tasks_with_dag(self):
        """Test getting parallel tasks with pre-built DAG."""
        workflow = WorkflowModel(phases=[
            Phase(name="Planning", index=1, tasks=[
                Task(name="Design", parallel=True, owner=["architect"]),
                Task(name="Spec", parallel=False, owner=["architect"]),
            ]),
        ])
        builder = DAGBuilder()
        dag = builder.build(workflow)

        parallel = builder.get_parallel_tasks(dag=dag)

        assert len(parallel) == 1
        assert parallel[0].name == "Design"

    def test_get_parallel_tasks_requires_dag_or_workflow(self):
        """Test that method requires either dag or workflow."""
        builder = DAGBuilder()

        with pytest.raises(ValueError) as exc_info:
            builder.get_parallel_tasks()

        assert "Either dag or workflow must be provided" in str(exc_info.value)


class TestDAGBuilderGetExecutionOrder:
    """Tests for DAGBuilder.get_execution_order() method."""

    def test_execution_order_empty(self):
        """Test getting execution order from empty workflow."""
        builder = DAGBuilder()
        order = builder.get_execution_order(WorkflowModel(phases=[]))

        assert order == []

    def test_execution_order_linear(self):
        """Test getting execution order on linear workflow."""
        workflow = WorkflowModel(phases=[
            Phase(name="Planning", index=1),
            Phase(name="Implementation", index=2, depends_on=["Planning"]),
            Phase(name="Testing", index=3, depends_on=["Implementation"]),
        ])
        builder = DAGBuilder()
        order = builder.get_execution_order(workflow)

        # Verify correct order
        phase_indices = [int(o.replace("phase:", "")) for o in order]
        assert phase_indices == [1, 2, 3]

    def test_execution_order_parallel_start(self):
        """Test getting execution order with parallel phases."""
        workflow = WorkflowModel(phases=[
            Phase(name="Planning", index=1, depends_on=[]),
            Phase(name="Backend", index=2, depends_on=["Planning"]),
            Phase(name="Frontend", index=3, depends_on=["Planning"]),
            Phase(name="Final", index=4, depends_on=["Backend", "Frontend"]),
        ])
        builder = DAGBuilder()
        order = builder.get_execution_order(workflow)

        # Phase 1 should come before 2, 3, 4
        # Phases 2 and 3 should come before 4
        phase_1_idx = order.index("phase:1")
        phase_2_idx = order.index("phase:2")
        phase_3_idx = order.index("phase:3")
        phase_4_idx = order.index("phase:4")

        assert phase_1_idx < phase_2_idx
        assert phase_1_idx < phase_3_idx
        assert phase_2_idx < phase_4_idx
        assert phase_3_idx < phase_4_idx
