"""DeepAgents integration for MyAgent.

Provides integration with DeepAgents framework for task execution.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

try:
    from deepagents import create_deep_agent
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    DEEPAGENTS_AVAILABLE = True
except ImportError:
    DEEPAGENTS_AVAILABLE = False
    create_deep_agent = None

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import BaseMessage


def require_deepagents() -> None:
    """Check if DeepAgents is available, raise ImportError if not.

    Raises:
        ImportError: If deepagents or langchain dependencies are not installed
    """
    if not DEEPAGENTS_AVAILABLE:
        raise ImportError(
            "deepagents or langchain dependencies are not installed. "
            "Install with: pip install deepagents langchain-anthropic langchain-openai"
        )


class LLMProvider:
    """LLM provider abstraction."""

    @staticmethod
    def create(provider: str = "anthropic", **kwargs) -> "BaseChatModel | None":
        """Create LLM instance.

        Args:
            provider: Provider name (anthropic, openai, ollama)
            **kwargs: Additional arguments

        Returns:
            LLM instance or None
        """
        if not DEEPAGENTS_AVAILABLE:
            return None

        provider = provider.lower()

        if provider == "anthropic":
            api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
            model = kwargs.get("model", "claude-sonnet-4-6")
            if not api_key:
                return None
            return ChatAnthropic(model=model, anthropic_api_key=api_key)

        elif provider == "openai":
            api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
            model = kwargs.get("model", "gpt-4")
            if not api_key:
                return None
            return ChatOpenAI(model=model, api_key=api_key)

        elif provider == "ollama":
            # Ollama local model
            model = kwargs.get("model", "llama2")
            base_url = kwargs.get("base_url", "http://localhost:11434")
            return ChatOpenAI(
                model=model,
                openai_api_base=f"{base_url}/v1",
                api_key="ollama",  # Ollama doesn't need real API key
            )

        return None


class DeepAgentFactory:
    """Factory for creating DeepAgents."""

    ROLE_PROMPTS = {
        "architect": """You are an expert software architect.
Your role is to design system architecture, select technology stacks, and define API contracts.
You generate detailed PLANNING.md documents.

Be concise and technical. Focus on:
- Clean Architecture principles
- API-first design
- Scalability considerations
- Technology stack recommendations""",

        "backend-dev": """You are an expert backend developer.
Your role is to implement business logic, APIs, and database designs.
You write clean, maintainable code following best practices.

Be concise and technical. Focus on:
- Business logic implementation
- API endpoint design
- Database schema
- Error handling""",

        "frontend-dev": """You are an expert frontend developer.
Your role is to implement UI components, state management, and user interfaces.
You write clean, maintainable code following best practices.

Be concise and technical. Focus on:
- Component architecture
- State management
- User experience
- Responsive design""",

        "qa-engineer": """You are an expert QA engineer.
Your role is to create test plans, write test cases, and ensure code quality.
You write comprehensive tests and identify potential issues.

Be thorough. Focus on:
- Test coverage
- Edge cases
- Integration testing
- Quality gates""",
    }

    def __init__(self, llm: "BaseChatModel | None" = None):
        """Initialize DeepAgent factory.

        Args:
            llm: Optional LLM instance
        """
        self.llm = llm
        self._agents: dict[str, Any] = {}

    def create_agent(
        self,
        role: str,
        tools: list | None = None,
        interrupt_on: dict | None = None,
    ) -> Any | None:
        """Create a DeepAgent for a role.

        Args:
            role: Role name (architect, backend-dev, etc.)
            tools: Optional tools list
            interrupt_on: Optional interrupt config

        Returns:
            DeepAgent instance or None
        """
        require_deepagents()

        if role in self._agents:
            return self._agents[role]

        system_prompt = self.ROLE_PROMPTS.get(role, f"You are a {role} agent.")

        try:
            agent = create_deep_agent(
                model=self.llm,
                system_prompt=system_prompt,
                tools=tools or [],
                interrupt_on=interrupt_on,
            )
            self._agents[role] = agent
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent '{role}': {e}")
            return None

    def get_default_tools(self) -> list:
        """Get default tools for agents.

        Returns:
            List of tools
        """
        if not DEEPAGENTS_AVAILABLE:
            return []

        # Return empty list - DeepAgents provides built-in tools
        return []


class MockAgent:
    """Mock agent for testing without LLM."""

    def __init__(self, role: str, response: str = ""):
        """Initialize mock agent.

        Args:
            role: Agent role
            response: Mock response
        """
        self.role = role
        self.response = response or f"[Mock {role}] Task completed"

    def invoke(self, input_data: dict) -> dict:
        """Invoke mock agent.

        Args:
            input_data: Input data

        Returns:
            Mock response
        """
        return {
            "messages": [
                {"role": "assistant", "content": self.response}
            ]
        }


class AgentExecutor:
    """Executes tasks using DeepAgents."""

    def __init__(
        self,
        provider: str = "anthropic",
        api_key: str | None = None,
        model: str | None = None,
    ):
        """Initialize agent executor.

        Args:
            provider: LLM provider
            api_key: API key
            model: Model name
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.factory = DeepAgentFactory()
        self._llm = None

    def _get_llm(self) -> "BaseChatModel | None":
        """Get or create LLM instance.

        Returns:
            LLM instance
        """
        if self._llm is None:
            self._llm = LLMProvider.create(
                provider=self.provider,
                api_key=self.api_key,
                model=self.model,
            )
        return self._llm

    def execute_task(
        self,
        task: str,
        role: str = "architect",
        context: dict | None = None,
    ) -> dict[str, Any]:
        """Execute a task using DeepAgents.

        Args:
            task: Task description
            role: Agent role to use
            context: Optional context

        Returns:
            Execution result
        """
        if not DEEPAGENTS_AVAILABLE:
            return self._mock_execute(task, role, context)

        llm = self._get_llm()
        if llm is None:
            return self._mock_execute(task, role, context)

        try:
            agent = self.factory.create_agent(
                role=role,
                tools=self.factory.get_default_tools(),
            )

            if agent is None:
                return self._mock_execute(task, role, context)

            # Build input
            from langchain_core.messages import HumanMessage

            input_data = {
                "messages": [HumanMessage(content=task)],
            }
            if context:
                input_data.update(context)

            # Execute
            result = agent.invoke(input_data)

            return {
                "success": True,
                "result": result,
                "role": role,
                "task": task,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "role": role,
                "task": task,
            }

    def _mock_execute(
        self,
        task: str,
        role: str,
        context: dict | None,
    ) -> dict[str, Any]:
        """Mock execution when DeepAgents is not available.

        Args:
            task: Task description
            role: Agent role
            context: Optional context

        Returns:
            Mock result
        """
        return {
            "success": True,
            "result": {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"[Mock {role}] Completed: {task[:50]}..."
                    }
                ]
            },
            "role": role,
            "task": task,
            "mock": True,
        }
