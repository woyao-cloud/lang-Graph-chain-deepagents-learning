"""
Backend-Dev Agent - 后端开发 Agent
精通 Python/Go/Java，负责业务逻辑、API 与数据库设计
FR-AGENT-001.1: 角色实例化
"""

from typing import Dict, Any
from deepagents.agents.roles.base import SubAgent, SubAgentConfig, register_agent


SYSTEM_PROMPT = """You are an expert backend developer. Your responsibilities include:

1. **Business Logic**: Implement clean, maintainable business logic
2. **API Development**: Design and implement RESTful APIs
3. **Database Design**: Create efficient database schemas and queries
4. **Code Quality**: Write testable, well-documented code

Your tech stack:
- Python 3.11+, FastAPI, SQLAlchemy
- Go 1.21+, Gin/Echo
- PostgreSQL, Redis

Guidelines:
- Follow SOLID principles
- Write unit tests alongside code
- Document API endpoints with OpenAPI/Swagger
- Use type hints in Python
- Keep functions small and focused
"""


@register_agent("backend-dev")
class BackendDevAgent(SubAgent):
    """
    后端开发 Agent
    专注于业务逻辑和 API 开发
    """

    def __init__(self, config: SubAgentConfig):
        super().__init__(config)
        self.system_prompt = SYSTEM_PROMPT

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行后端开发任务
        """
        from deepagents.agents.deep_agent_wrapper import create_langchain_agent
        from deepagents.agents.tools_registry import ToolsRegistry

        task_description = task_input.get("description", "")
        context = task_input.get("context", {})

        prompt = f"""
## Task: {task_description}

## Requirements:
{context.get('requirements', 'No specific requirements')}

## Tech Stack:
{context.get('tech_stack', 'Python 3.11+, FastAPI')}

## System Prompt:
{self.system_prompt}

Please implement the backend code for this task.
"""

        tools = ToolsRegistry.get_tools(self.config.tools)
        agent = create_langchain_agent(
            model=context.get("model", "openai/gpt-4o"),
            tools=tools,
            system_prompt=prompt
        )

        result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})

        return {
            "status": "success",
            "output": result,
            "agent": "backend-dev",
            "task": task_description
        }

    async def validate_output(self, output: Any) -> bool:
        """验证后端代码输出"""
        if not isinstance(output, dict):
            return False
        return output.get("status") == "success"
