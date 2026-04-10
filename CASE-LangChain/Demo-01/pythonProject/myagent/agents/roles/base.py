"""
Base Sub-Agent - 所有 Sub-Agent 的基类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SubAgentConfig:
    """Sub-Agent 配置"""
    name: str
    description: str
    tools: List[str]
    model: str = "openai/gpt-4o"
    system_prompt_template: str = ""


class SubAgent(ABC):
    """
    Sub-Agent 基类
    定义 Agent 的通用接口
    """

    def __init__(self, config: SubAgentConfig):
        self.config = config
        self._agent = None

    @abstractmethod
    async def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        返回执行结果
        """
        pass

    @abstractmethod
    async def validate_output(self, output: Any) -> bool:
        """
        验证输出是否有效
        """
        pass

    def get_tools(self) -> List[str]:
        """获取 Agent 使用的工具列表"""
        return self.config.tools

    def get_system_prompt(self, task_context: Dict) -> str:
        """获取系统提示词"""
        return self.config.system_prompt_template.format(**task_context)


class AgentFactory:
    """
    Agent 工厂
    根据配置创建 Agent 实例
    """

    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, agent_class: type):
        """注册 Agent 类"""
        cls._registry[name] = agent_class

    @classmethod
    def create(cls, name: str, config: SubAgentConfig) -> SubAgent:
        """创建 Agent 实例"""
        if name not in cls._registry:
            raise ValueError(f"Unknown agent type: {name}")
        return cls._registry[name](config)

    @classmethod
    def list_agents(cls) -> List[str]:
        """列出所有注册的 Agent"""
        return list(cls._registry.keys())


def register_agent(name: str):
    """Agent 注册装饰器"""
    def decorator(cls: type):
        AgentFactory.register(name, cls)
        return cls
    return decorator
