"""
Frontend-Dev Agent - 前端开发 Agent
精通 Vue/React，负责 UI 组件、状态管理与路由
FR-AGENT-001.1: 角色实例化
"""

from typing import Dict, Any
from myagent.agents.roles.base import SubAgent, SubAgentConfig, register_agent


SYSTEM_PROMPT = """You are an expert frontend developer. Your responsibilities include:

1. **UI Components**: Build reusable, accessible UI components
2. **State Management**: Implement efficient state management patterns
3. **Routing**: Configure client-side routing with proper guards
4. **Performance**: Optimize for fast loading and smooth interactions

Your tech stack:
- React 18+, TypeScript, TailwindCSS
- Vue 3, Composition API, Pinia
- Next.js 14, Nuxt 3

Guidelines:
- Follow component design best practices
- Ensure mobile responsiveness
- Write component tests
- Use semantic HTML
- Keep components small and focused
"""


@register_agent("frontend-dev")
class FrontendDevAgent(SubAgent):
    """
    前端开发 Agent
    专注于 UI 组件和用户体验
    """

    def __init__(self, config: SubAgentConfig):
        super().__init__(config)
        self.system_prompt = SYSTEM_PROMPT

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行前端开发任务
        """
        from myagent.agents.deep_agent_wrapper import create_langchain_agent
        from myagent.agents.tools_registry import ToolsRegistry

        task_description = task_input.get("description", "")
        context = task_input.get("context", {})

        prompt = f"""
## Task: {task_description}

## Requirements:
{context.get('requirements', 'No specific requirements')}

## Tech Stack:
{context.get('tech_stack', 'React 18, TypeScript, TailwindCSS')}

## System Prompt:
{self.system_prompt}

Please implement the frontend code for this task.
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
            "agent": "frontend-dev",
            "task": task_description
        }

    async def validate_output(self, output: Any) -> bool:
        """验证前端代码输出"""
        if not isinstance(output, dict):
            return False
        return output.get("status") == "success"
