"""
Supervisor Agent - 主 Agent 实现
负责任务规划、Sub-Agent 调度
"""

from typing import Optional, List, Dict, Any
import os


class SupervisorAgent:
    """
    主 Agent（Supervisor）
    - 解析 workflow.md 和 agent.md
    - 生成 PLANNING.md
    - 调度 Sub-Agent 执行
    """

    def __init__(self):
        self.workflow = None
        self.agent_config = None

    def generate_planning(self) -> str:
        """
        生成 PLANNING.md
        基于 workflow.md 拆解任务，生成开发规划
        """
        from myagent.workflow.parser import WorkflowParser

        if not os.path.exists("workflow.md"):
            raise FileNotFoundError("workflow.md not found")

        parser = WorkflowParser()
        self.workflow = parser.parse_file("workflow.md")

        # 生成 PLANNING.md 内容
        planning_content = self._build_planning_md()

        # 写入文件
        with open("PLANNING.md", "w", encoding="utf-8") as f:
            f.write(planning_content)

        return planning_content

    def _build_planning_md(self) -> str:
        """构建 PLANNING.md 内容"""
        lines = [
            "# PLANNING.md - 开发规划",
            "",
            "## 任务拆解",
            "",
        ]

        for phase in self.workflow.phases:
            lines.append(f"### {phase.name}")
            for task in phase.tasks:
                lines.append(f"- **{task.name}**")
                lines.append(f"  - Owner: {', '.join(task.owner) or 'TBD'}")
                lines.append(f"  - Parallel: {'是' if task.parallel else '否'}")
                lines.append(f"  - 状态: 待确认")
                lines.append("")

        lines.extend([
            "## 技术栈",
            "",
            "- 语言: Python 3.11+ / TypeScript",
            "- 框架: FastAPI / React",
            "- 数据库: PostgreSQL",
            "- 工具: Git, Docker",
            "",
            "## 文件结构",
            "",
            "```",
            "src/",
            "├── api/          # API 接口",
            "├── models/       # 数据模型",
            "├── services/     # 业务逻辑",
            "└── tests/        # 测试用例",
            "```",
            "",
            "## 接口契约",
            "",
            "（待定义）",
            "",
            "## 风险与预案",
            "",
            "（待识别）",
            "",
            "---\n",
            f"生成时间: {self._get_timestamp()}",
        ])

        return "\n".join(lines)

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
