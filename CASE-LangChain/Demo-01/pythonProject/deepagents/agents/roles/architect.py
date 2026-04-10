"""
Architect Agent - 架构师 Agent
负责任务：架构设计、技术选型、PLANNING.md 生成、接口契约定义
FR-AGENT-001.1: 角色实例化
"""

from typing import Dict, Any, List
from deepagents.agents.roles.base import SubAgent, SubAgentConfig, register_agent
from deepagents.agents.tools_registry import ToolsRegistry


SYSTEM_PROMPT = """You are an expert software architect. Your responsibilities include:

1. **Architecture Design**: Create scalable, maintainable system architectures
2. **Technology Selection**: Recommend appropriate tech stacks based on requirements
3. **Interface Contracts**: Define clear API schemas and data models
4. **Risk Assessment**: Identify potential risks and mitigation strategies

When designing an architecture:
- Consider scalability, reliability, and security
- Balance between simplicity and flexibility
- Document all key decisions with rationale

Output format should be clean markdown with:
- Architecture diagrams (using text/mermaid)
- Component descriptions
- Data flow descriptions
- API contracts
- Technology recommendations with alternatives considered
"""


@register_agent("architect")
class ArchitectAgent(SubAgent):
    """
    架构师 Agent
    专注于系统架构和技术决策
    """

    def __init__(self, config: SubAgentConfig):
        super().__init__(config)
        self.system_prompt = SYSTEM_PROMPT

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行架构设计任务
        """
        from deepagents.agents.deep_agent_wrapper import create_langchain_agent

        task_description = task_input.get("description", "")
        context = task_input.get("context", {})

        # 构建 prompt
        prompt = f"""
## Task: {task_description}

## Context:
{context.get('requirements', 'No specific requirements provided')}

## System Prompt:
{self.system_prompt}

Please design the architecture for this task.
"""

        # 使用 deepagents 创建 Agent
        tools = ToolsRegistry.get_tools(self.config.tools)
        agent = create_langchain_agent(
            model=context.get("model", "openai/gpt-4o"),
            tools=tools,
            system_prompt=prompt
        )

        # 执行
        result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})

        return {
            "status": "success",
            "output": result,
            "agent": "architect",
            "task": task_description
        }

    async def validate_output(self, output: Any) -> bool:
        """
        验证架构设计输出
        """
        if not isinstance(output, dict):
            return False

        # 检查必要的字段
        required_fields = ["architecture", "components"]
        return all(field in output for field in required_fields)
