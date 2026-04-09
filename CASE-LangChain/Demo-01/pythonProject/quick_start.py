import os

from langchain.tools import tool
from langchain.chat_models import init_chat_model

api_key = os.getenv("OPENAI_API_KEY", "sk-723b202be3804cd89fef3970bc92675f")
api_base = os.getenv("OPENAI_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

model = init_chat_model(
    api_key=api_key,
    base_url=api_base,    # 指向 DashScope 的 OpenAI 兼容 URL
    model_provider="qwen-max",     # 或 "qwen-turbo" / 您有权限的模型名
    temperature=0,
)


# Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a / b


# Augment the LLM with tools
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)