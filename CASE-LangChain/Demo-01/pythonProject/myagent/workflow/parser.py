"""
工作流解析器 - 解析 workflow.md 文件
FR-WF-001: 工作流解析模块
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class Task:
    """任务定义"""
    name: str
    owner: List[str] = field(default_factory=list)
    parallel: bool = False
    depends: List[str] = field(default_factory=list)


@dataclass
class Phase:
    """阶段定义"""
    name: str
    tasks: List[Task] = field(default_factory=list)
    depends: List[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class Workflow:
    """工作流定义"""
    phases: List[Phase] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)


class WorkflowParser:
    """
    解析 workflow.md 文件
    支持 Markdown 格式的 Phase 和 Task 定义
    """

    # Phase 匹配模式: - [Phase N] 阶段名称 (depends: xxx)
    PHASE_PATTERN = re.compile(
        r'^-\s*\[Phase\s+(\d+)\]\s*(.+?)\s*(?:\((depends?:\s*([^)]+))?\))?$',
        re.MULTILINE
    )

    # Task 匹配模式: - Task: 任务名称 (parallel: true/false, owner: xxx)
    TASK_PATTERN = re.compile(
        r'^\s*-\s*Task:\s*(.+?)\s*(?:\(([^)]+)\))?$',
        re.MULTILINE
    )

    def parse_file(self, file_path: str) -> Workflow:
        """解析 workflow.md 文件"""
        content = Path(file_path).read_text(encoding="utf-8")
        return self.parse(content)

    def parse(self, content: str) -> Workflow:
        """解析工作流内容"""
        workflow = Workflow()

        # 提取 Rules 部分
        rules_match = re.search(r'## Rules\s*\n(.*?)(?:\n##|\Z)', content, re.DOTALL)
        if rules_match:
            rules_text = rules_match.group(1)
            workflow.rules = [line.strip() for line in rules_text.strip().split('\n') if line.strip().startswith('-')]

        # 提取 Phases 部分
        phases_match = re.search(r'## Phases\s*\n(.*?)(?:\n##|\Z)', content, re.DOTALL)
        if not phases_match:
            return workflow

        phases_text = phases_match.group(1)

        # 按行解析
        current_phase: Optional[Phase] = None
        for line in phases_text.split('\n'):
            # 检查 Phase
            phase_match = self.PHASE_PATTERN.match(line)
            if phase_match:
                phase_num = phase_match.group(1)
                phase_name = phase_match.group(2).strip()
                depends_str = phase_match.group(4) or ""

                depends = [d.strip() for d in depends_str.split(',') if d.strip() and d.strip() != "none"]

                current_phase = Phase(
                    name=f"[Phase {phase_num}] {phase_name}",
                    depends=depends,
                    raw_text=line
                )
                workflow.phases.append(current_phase)
                continue

            # 检查 Task
            if current_phase:
                task_match = self.TASK_PATTERN.match(line)
                if task_match:
                    task_name = task_match.group(1).strip()
                    options_str = task_match.group(2) or ""

                    # 解析 options
                    owner_list = []
                    parallel = False

                    # 解析 owner
                    owner_match = re.search(r'owner:\s*([^,)]+)', options_str)
                    if owner_match:
                        owner_str = owner_match.group(1).strip()
                        owner_list = [o.strip() for o in owner_str.split(',')]

                    # 解析 parallel
                    if 'parallel' in options_str.lower():
                        parallel_match = re.search(r'parallel:\s*(true|false)', options_str, re.IGNORECASE)
                        if parallel_match:
                            parallel = parallel_match.group(1).lower() == 'true'

                    task = Task(
                        name=task_name,
                        owner=owner_list,
                        parallel=parallel
                    )
                    current_phase.tasks.append(task)

        return workflow

    def _normalize_phase_name(self, name: str) -> str:
        """标准化 Phase 名称用于匹配"""
        # 从 "[Phase 1] 名称" 提取 "Phase 1"
        import re
        m = re.match(r'\[Phase\s+(\d+)\]\s*(.+)', name)
        if m:
            return f"Phase {m.group(1)}"
        return name

    def validate(self, workflow: Workflow) -> List[str]:
        """
        验证工作流完整性
        返回错误列表
        """
        errors = []

        # 检查是否有 Phase
        if not workflow.phases:
            errors.append("工作流至少需要一个 Phase")
            return errors

        # 建立 name -> phase 映射（支持多种格式）
        phase_names = set()
        for p in workflow.phases:
            phase_names.add(p.name)
            phase_names.add(self._normalize_phase_name(p.name))

        # 检查 Phase 依赖是否有效
        for phase in workflow.phases:
            for dep in phase.depends:
                # 标准化依赖名称
                normalized_dep = self._normalize_phase_name(dep)
                if dep not in phase_names and normalized_dep not in phase_names:
                    errors.append(f"Phase '{phase.name}' 的依赖 '{dep}' 不存在")

        # 检查循环依赖
        if self._has_cycle(workflow):
            errors.append("工作流存在循环依赖")

        return errors

    def _has_cycle(self, workflow: Workflow) -> bool:
        """检测是否存在循环依赖"""
        phase_map = {p.name: p for p in workflow.phases}
        visited = set()
        rec_stack = set()

        def dfs(name: str) -> bool:
            visited.add(name)
            rec_stack.add(name)
            phase = phase_map.get(name)
            if phase:
                for dep in phase.depends:
                    if dep not in visited:
                        if dfs(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            rec_stack.remove(name)
            return False

        for phase in workflow.phases:
            if phase.name not in visited:
                if dfs(phase.name):
                    return True
        return False
