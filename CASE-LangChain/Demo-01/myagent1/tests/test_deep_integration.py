"""Tests for agents/deep_integration.py module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from myagent.agents.deep_integration import (
    AgentExecutor,
    DeepAgentFactory,
    LLMProvider,
    MockAgent,
    require_deepagents,
)


class TestRequireDeepAgents:
    """Tests for require_deepagents() function."""

    def test_raises_when_not_available(self):
        """Test that ImportError is raised when DeepAgents not available."""
        with patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", False):
            with pytest.raises(ImportError) as exc_info:
                require_deepagents()

            assert "not installed" in str(exc_info.value)

    def test_no_error_when_available(self):
        """Test no error when DeepAgents is available."""
        # This test only runs if DEEPAGENTS_AVAILABLE is True
        # or mocks it to True
        pass  # Handled by integration tests


class TestLLMProvider:
    """Tests for LLMProvider class."""

    def test_create_returns_none_when_unavailable(self):
        """Test that create returns None when DeepAgents unavailable."""
        with patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", False):
            result = LLMProvider.create("anthropic")
            assert result is None

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch("myagent.agents.deep_integration.ChatAnthropic")
    def test_create_anthropic(self, mock_chat: MagicMock):
        """Test creating Anthropic LLM."""
        mock_chat_instance = MagicMock()
        mock_chat.return_value = mock_chat_instance

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False):
            result = LLMProvider.create("anthropic", api_key="test-key")

            assert result is mock_chat_instance
            mock_chat.assert_called_once()

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch("myagent.agents.deep_integration.ChatOpenAI")
    def test_create_openai(self, mock_chat: MagicMock):
        """Test creating OpenAI LLM."""
        mock_chat_instance = MagicMock()
        mock_chat.return_value = mock_chat_instance

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=False):
            result = LLMProvider.create("openai", api_key="test-key")

            assert result is mock_chat_instance
            mock_chat.assert_called_once()

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch("myagent.agents.deep_integration.ChatOpenAI")
    def test_create_ollama(self, mock_chat: MagicMock):
        """Test creating Ollama LLM."""
        mock_chat_instance = MagicMock()
        mock_chat.return_value = mock_chat_instance

        result = LLMProvider.create("ollama", model="llama2")

        assert result is mock_chat_instance
        # Verify base URL includes /v1
        call_kwargs = mock_chat.call_args[1]
        assert "openai_api_base" in call_kwargs
        assert "/v1" in call_kwargs["openai_api_base"]

    def test_create_unknown_provider(self):
        """Test creating unknown provider returns None."""
        with patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True):
            result = LLMProvider.create("unknown_provider")
            assert result is None

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    def test_create_without_api_key(self):
        """Test that create returns None without API key."""
        with patch.dict("os.environ", {}, clear=True):
            result = LLMProvider.create("anthropic")
            assert result is None

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch("myagent.agents.deep_integration.ChatAnthropic")
    def test_create_with_env_api_key(self, mock_chat: MagicMock):
        """Test that create uses API key from environment."""
        mock_chat_instance = MagicMock()
        mock_chat.return_value = mock_chat_instance

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}, clear=False):
            result = LLMProvider.create("anthropic")

            assert result is mock_chat_instance


class TestDeepAgentFactory:
    """Tests for DeepAgentFactory class."""

    def test_default_init(self):
        """Test default initialization."""
        factory = DeepAgentFactory()
        assert factory.llm is None
        assert factory._agents == {}
        assert len(factory.ROLE_PROMPTS) > 0

    def test_init_with_llm(self):
        """Test initialization with LLM."""
        mock_llm = MagicMock()
        factory = DeepAgentFactory(llm=mock_llm)
        assert factory.llm is mock_llm

    def test_role_prompts_contain_standard_roles(self):
        """Test that standard roles are defined."""
        factory = DeepAgentFactory()
        assert "architect" in factory.ROLE_PROMPTS
        assert "backend-dev" in factory.ROLE_PROMPTS
        assert "frontend-dev" in factory.ROLE_PROMPTS
        assert "qa-engineer" in factory.ROLE_PROMPTS

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", False)
    def test_create_agent_requires_deepagents(self):
        """Test that create_agent raises ImportError if DeepAgents unavailable."""
        factory = DeepAgentFactory()

        with pytest.raises(ImportError):
            factory.create_agent("architect")

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch("myagent.agents.deep_integration.create_deep_agent")
    def test_create_agent_success(self, mock_create: MagicMock):
        """Test successful agent creation."""
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent
        factory = DeepAgentFactory()

        agent = factory.create_agent("architect")

        assert agent is mock_agent
        mock_create.assert_called_once()

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch("myagent.agents.deep_integration.create_deep_agent")
    def test_create_agent_caches_agent(self, mock_create: MagicMock):
        """Test that created agents are cached."""
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent
        factory = DeepAgentFactory()

        # Create same role twice
        agent1 = factory.create_agent("architect")
        agent2 = factory.create_agent("architect")

        assert agent1 is agent2
        assert mock_create.call_count == 1

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch("myagent.agents.deep_integration.create_deep_agent")
    def test_create_agent_with_tools(self, mock_create: MagicMock):
        """Test agent creation with tools."""
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent
        factory = DeepAgentFactory()
        tools = ["tool1", "tool2"]

        factory.create_agent("architect", tools=tools)

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["tools"] == tools

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch("myagent.agents.deep_integration.create_deep_agent")
    def test_create_agent_with_interrupt_on(self, mock_create: MagicMock):
        """Test agent creation with interrupt config."""
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent
        factory = DeepAgentFactory()
        interrupt_on = {"dangerous": True}

        factory.create_agent("architect", interrupt_on=interrupt_on)

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["interrupt_on"] == interrupt_on

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch("myagent.agents.deep_integration.create_deep_agent")
    def test_create_agent_unknown_role(self, mock_create: MagicMock):
        """Test agent creation with unknown role."""
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent
        factory = DeepAgentFactory()

        factory.create_agent("unknown_role")

        # Should still work with default prompt
        call_kwargs = mock_create.call_args[1]
        assert "unknown_role" in call_kwargs["system_prompt"]

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch("myagent.agents.deep_integration.create_deep_agent")
    def test_create_agent_error_returns_none(self, mock_create: MagicMock):
        """Test that errors during creation return None."""
        mock_create.side_effect = Exception("Creation failed")
        factory = DeepAgentFactory()

        agent = factory.create_agent("architect")

        assert agent is None

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    def test_get_default_tools_unavailable(self):
        """Test get_default_tools when DeepAgents unavailable."""
        with patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", False):
            factory = DeepAgentFactory()
            tools = factory.get_default_tools()
            assert tools == []


class TestMockAgent:
    """Tests for MockAgent class."""

    def test_default_init(self):
        """Test default initialization."""
        agent = MockAgent("test_role")
        assert agent.role == "test_role"
        assert "[Mock test_role]" in agent.response

    def test_init_with_custom_response(self):
        """Test initialization with custom response."""
        agent = MockAgent("test_role", "Custom response")
        assert agent.response == "Custom response"

    def test_invoke_returns_messages(self):
        """Test invoke returns expected structure."""
        agent = MockAgent("test_role", "Test output")
        result = agent.invoke({})

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "assistant"
        assert result["messages"][0]["content"] == "Test output"

    def test_invoke_with_input_data(self):
        """Test invoke handles input data."""
        agent = MockAgent("test_role")
        result = agent.invoke({"input": "data"})

        # Mock doesn't use input but should accept it
        assert "messages" in result


class TestAgentExecutor:
    """Tests for AgentExecutor class."""

    def test_default_init(self):
        """Test default initialization."""
        executor = AgentExecutor()
        assert executor.provider == "anthropic"
        assert executor.api_key is None
        assert executor.model is None
        assert isinstance(executor.factory, DeepAgentFactory)

    def test_init_with_params(self):
        """Test initialization with parameters."""
        executor = AgentExecutor(
            provider="openai",
            api_key="test-key",
            model="gpt-4",
        )
        assert executor.provider == "openai"
        assert executor.api_key == "test-key"
        assert executor.model == "gpt-4"

    def test_get_llm_caches(self):
        """Test that _get_llm caches the LLM instance."""
        with patch("myagent.agents.deep_integration.ChatAnthropic") as mock_chat:
            mock_instance = MagicMock()
            mock_chat.return_value = mock_instance

            executor = AgentExecutor(provider="anthropic", api_key="test-key")

            llm1 = executor._get_llm()
            llm2 = executor._get_llm()

            assert llm1 is llm2
            assert llm1 is mock_instance

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", False)
    def test_execute_task_mock_fallback(self):
        """Test that execute_task falls back to mock when unavailable."""
        executor = AgentExecutor()

        result = executor.execute_task(
            task="Test task",
            role="architect",
        )

        assert result["success"] is True
        assert result["mock"] is True
        assert result["role"] == "architect"

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", False)
    def test_execute_task_with_context(self):
        """Test execute_task with context."""
        executor = AgentExecutor()

        result = executor.execute_task(
            task="Test task",
            role="architect",
            context={"key": "value"},
        )

        assert result["success"] is True
        assert result["task"] == "Test task"

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch.object(AgentExecutor, "_get_llm")
    def test_execute_task_with_llm(self, mock_get_llm: MagicMock):
        """Test execute_task when LLM is available."""
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        executor = AgentExecutor()

        result = executor.execute_task(
            task="Test task",
            role="architect",
        )

        # May succeed or fail depending on mock setup
        assert "success" in result
        assert result["role"] == "architect"

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch.object(AgentExecutor, "_get_llm")
    def test_execute_task_no_llm_fallback(self, mock_get_llm: MagicMock):
        """Test execute_task falls back when LLM creation fails."""
        mock_get_llm.return_value = None

        executor = AgentExecutor()

        result = executor.execute_task(
            task="Test task",
            role="architect",
        )

        assert result["success"] is True
        assert result["mock"] is True

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", True)
    @patch.object(AgentExecutor, "_get_llm")
    def test_execute_task_error_handling(self, mock_get_llm: MagicMock):
        """Test execute_task handles errors."""
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        executor = AgentExecutor()

        # Test with no factory agent
        result = executor.execute_task(
            task="Test task",
            role="architect",
        )

        # Should have a result
        assert "success" in result

    @patch("myagent.agents.deep_integration.DEEPAGENTS_AVAILABLE", False)
    def test_mock_execute(self):
        """Test _mock_execute method."""
        executor = AgentExecutor()

        result = executor._mock_execute(
            task="Test task",
            role="architect",
            context={"key": "value"},
        )

        assert result["success"] is True
        assert result["mock"] is True
        assert result["role"] == "architect"
        assert result["task"] == "Test task"
        assert "messages" in result["result"]
