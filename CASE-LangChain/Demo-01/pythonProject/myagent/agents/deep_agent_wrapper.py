"""
Deep Agent Wrapper - 使用 myagent 框架创建 LangChain Agent
"""

from typing import List, Optional
from langchain_core.language_models.chat_models import BaseChatModel

from myagent import create_deep_agent


def create_langchain_agent(
    model: str | BaseChatModel,
    tools: List,
    system_prompt: str,
    checkpointer=None,
    **kwargs
):
    """
    使用 myagent 框架创建 Agent

    Args:
        model: 模型名称或预配置的 ChatModel 实例
        tools: 工具列表
        system_prompt: 系统提示词
        checkpointer: 可选的检查点保存器（用于断点续跑）
        **kwargs: 其他参数传递给 create_deep_agent

    Returns:
        配置好的 Agent 图
    """
    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        **kwargs
    )
