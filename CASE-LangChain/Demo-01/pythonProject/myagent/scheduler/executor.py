"""
并行/串行执行器
FR-AGENT-001.3: 并行调度
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import time


@dataclass
class ExecutionResult:
    """执行结果"""
    task_id: str
    agent_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    duration: float = 0.0
    token_usage: int = 0


class Executor:
    """
    执行器
    负责并行/串行执行 Sub-Agent 任务
    """

    def __init__(self, max_parallel: int = 3):
        self.max_parallel = max_parallel
        self._results: Dict[str, ExecutionResult] = {}

    async def execute_parallel(
        self,
        tasks: List[Dict],
        agent_factory: Callable,
        progress_callback: Optional[Callable] = None
    ) -> List[ExecutionResult]:
        """
        并行执行多个任务
        """
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def execute_with_semaphore(task: Dict) -> ExecutionResult:
            async with semaphore:
                return await self._execute_single(task, agent_factory)

        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ExecutionResult(
                    task_id=tasks[i].get("id", f"task_{i}"),
                    agent_id=tasks[i].get("agent", "unknown"),
                    success=False,
                    output=None,
                    error=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results

    async def execute_sequential(
        self,
        tasks: List[Dict],
        agent_factory: Callable,
        progress_callback: Optional[Callable] = None
    ) -> List[ExecutionResult]:
        """
        串行执行多个任务
        """
        results = []

        for i, task in enumerate(tasks):
            result = await self._execute_single(task, agent_factory)
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, len(tasks), task.get("id"))

        return results

    async def _execute_single(
        self,
        task: Dict,
        agent_factory: Callable
    ) -> ExecutionResult:
        """
        执行单个任务
        """
        start_time = time.time()
        task_id = task.get("id", "unknown")
        agent_id = task.get("agent", "unknown")

        try:
            # 获取或创建 Agent 实例
            agent = agent_factory(agent_id)

            # 执行任务
            output = await agent.execute(task.get("input", {}))

            duration = time.time() - start_time

            return ExecutionResult(
                task_id=task_id,
                agent_id=agent_id,
                success=True,
                output=output,
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                task_id=task_id,
                agent_id=agent_id,
                success=False,
                output=None,
                error=str(e),
                duration=duration
            )

    def get_results(self) -> Dict[str, ExecutionResult]:
        return self._results


class ContextIsolation:
    """
    上下文隔离器
    确保每个 Sub-Agent 运行在独立的上下文中
    """

    # 排除的状态键
    EXCLUDED_STATE_KEYS = [
        "messages",
        "todos",
        "structuredResponse",
        "skillsMetadata",
        "memoryContents",
    ]

    @classmethod
    def filter_state_for_subagent(cls, parent_state: Dict, task_id: str) -> Dict:
        """
        为 Sub-Agent 过滤父状态
        只保留任务相关的信息
        """
        filtered = {
            "task_id": task_id,
            # 保留文件状态（只读）
            "files": parent_state.get("files", {}),
            # 保留配置
            "config": parent_state.get("config", {}),
        }

        return filtered

    @classmethod
    def create_subagent_context(cls, task_description: str, parent_state: Dict) -> Dict:
        """
        为 Sub-Agent 创建独立的执行上下文
        """
        context = cls.filter_state_for_subagent(parent_state, task_description)
        # 添加任务描述作为新的 messages
        context["messages"] = [{"role": "user", "content": task_description}]
        return context
