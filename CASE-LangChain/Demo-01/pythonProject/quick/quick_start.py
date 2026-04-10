import os
from typing import List

from langchain.tools import tool
from langchain.chat_models import init_chat_model

# Configuration (environment-overridable)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = "ollama"
#os.getenv("MODEL_NAME", "minimax-m2.7:cloud")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))


def create_model():
    """Initialize and return a chat model backed by Ollama."""
    return init_chat_model(
        MODEL_NAME,
        provider="ollama",
        base_url=OLLAMA_URL,
        temperature=TEMPERATURE,
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
def get_tools() -> List:
    return [add, multiply, divide]


def main() -> None:
    model = create_model()
    tools = get_tools()
    model_with_tools = model.bind_tools(tools)

    print(f"Initialized model '{MODEL_NAME}' via Ollama at {OLLAMA_URL}")
    print("Registered tools:", [t.name for t in tools])


if __name__ == "__main__":
    main()