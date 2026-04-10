"""
DAG 构建器 - 将工作流转换为有向无环图
FR-WF-001.2: DAG 构建
"""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Any
from myagent.workflow.parser import Workflow, Phase, Task


@dataclass
class DAGNode:
    """DAG 节点"""
    id: str
    name: str
    node_type: str  # "phase" or "task"
    owner: List[str] = field(default_factory=list)
    parallel: bool = False
    depends: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DAG:
    """有向无环图"""

    def __init__(self):
        self.nodes: Dict[str, DAGNode] = {}
        self.phases: List[Phase] = []
        self.edges: Dict[str, List[str]] = {}  # node_id -> list of dependent node_ids

    def add_node(self, node: DAGNode):
        self.nodes[node.id] = node
        if node.id not in self.edges:
            self.edges[node.id] = []

    def add_edge(self, from_id: str, to_id: str):
        if from_id not in self.edges:
            self.edges[from_id] = []
        self.edges[from_id].append(to_id)

    def get_parallel_nodes(self) -> List[DAGNode]:
        """
        获取可并行执行的节点
        条件: 无依赖或所有依赖已完成
        """
        return [n for n in self.nodes.values() if n.parallel]

    def topological_sort(self) -> List[DAGNode]:
        """拓扑排序"""
        in_degree = {node_id: 0 for node_id in self.nodes}
        for node_id in self.nodes:
            for dependent in self.edges.get(node_id, []):
                in_degree[dependent] += 1

        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(self.nodes[node_id])
            for dependent in self.edges.get(node_id, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        return result


class DAGBuilder:
    """
    DAG 构建器
    将 Workflow 转换为 DAG
    """

    def __init__(self, workflow: Workflow):
        self.workflow = workflow

    def build(self) -> DAG:
        """
        构建 DAG
        """
        dag = DAG()
        dag.phases = self.workflow.phases

        phase_map: Dict[str, Phase] = {}
        node_id_map: Dict[str, str] = {}  # phase_name -> node_id

        # 添加 Phase 节点
        for i, phase in enumerate(self.workflow.phases):
            phase_id = f"phase_{i}"
            phase_node = DAGNode(
                id=phase_id,
                name=phase.name,
                node_type="phase",
                depends=phase.depends
            )
            dag.add_node(phase_node)
            node_id_map[phase.name] = phase_id
            phase_map[phase_id] = phase

        # 添加 Task 节点和边
        for i, phase in enumerate(self.workflow.phases):
            phase_id = f"phase_{i}"

            for j, task in enumerate(phase.tasks):
                task_id = f"task_{i}_{j}"
                task_node = DAGNode(
                    id=task_id,
                    name=task.name,
                    node_type="task",
                    owner=task.owner,
                    parallel=task.parallel,
                    depends=[phase_id]  # Task 依赖所属 Phase
                )
                dag.add_node(task_node)

                # Task 依赖 Phase
                dag.add_edge(phase_id, task_id)

        # 添加 Phase 之间的边
        for i, phase in enumerate(self.workflow.phases):
            phase_id = f"phase_{i}"
            for dep_name in phase.depends:
                dep_id = node_id_map.get(dep_name)
                if dep_id:
                    dag.add_edge(dep_id, phase_id)

        return dag
