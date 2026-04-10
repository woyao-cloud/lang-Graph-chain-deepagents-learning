"""
QA-Engineer Agent - QA 测试 Agent
负责单元测试、集成测试用例生成与覆盖率校验
FR-AGENT-001.1: 角色实例化
"""

from typing import Dict, Any
from myagent.agents.roles.base import SubAgent, SubAgentConfig, register_agent


SYSTEM_PROMPT = """You are an expert QA engineer. Your responsibilities include:

1. **Test Planning**: Design comprehensive test strategies
2. **Test Cases**: Write clear, executable test cases
3. **Coverage**: Ensure adequate test coverage
4. **Automation**: Automate repetitive testing tasks

Your expertise:
- pytest, unittest for Python
- Jest, Vitest for JavaScript/TypeScript
- Integration testing
- E2E testing with Playwright

Guidelines:
- Write tests before or alongside code (TDD)
- Aim for 80%+ code coverage
- Test edge cases and error conditions
- Keep tests independent and idempotent
- Use descriptive test names
"""


@register_agent("qa-engineer")
class QAEngineerAgent(SubAgent):
    """
    QA 测试 Agent
    专注于测试和质量保证
    """

    def __init__(self, config: SubAgentConfig):
        super().__init__(config)
        self.system_prompt = SYSTEM_PROMPT

    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 QA 测试任务
        """
        from myagent.agents.deep_agent_wrapper import create_langchain_agent
        from myagent.agents.tools_registry import ToolsRegistry

        task_description = task_input.get("description", "")
        context = task_input.get("context", {})

        prompt = f"""
## Task: {task_description}

## Code to Test:
{context.get('code', 'No code provided')}

## Tech Stack:
{context.get('tech_stack', 'Python/pytest or JavaScript/Jest')}

## System Prompt:
{self.system_prompt}

Please generate test cases for this task.
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
            "agent": "qa-engineer",
            "task": task_description
        }

    async def validate_output(self, output: Any) -> bool:
        """验证测试用例输出"""
        if not isinstance(output, dict):
            return False
        return output.get("status") == "success"
