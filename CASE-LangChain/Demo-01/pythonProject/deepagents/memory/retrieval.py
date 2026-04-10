"""
Memory Retrieval - 记忆检索
FR-EXEC-001.3: 记忆管理
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MemoryEntry:
    """
    记忆条目
    检索结果
    """
    content: str
    source: str  # "working", "short", "long"
    relevance: float = 0.0  # 0-1 相关度
    recency: float = 0.0  # 0-1 时效性
    authority: float = 0.0  # 0-1 权威性

    @property
    def final_score(self) -> float:
        """综合分数"""
        return self.relevance * 0.5 + self.recency * 0.3 + self.authority * 0.2


class MemoryRetrieval:
    """
    记忆检索器
    提供 Working/Short-term/Long-term 记忆的统一检索接口
    """

    def __init__(self):
        self._working_memory = None
        self._short_term_memory = None
        self._long_term_memory = None

    def set_working_memory(self, memory):
        """设置工作记忆"""
        self._working_memory = memory

    def set_short_term_memory(self, memory):
        """设置短期记忆"""
        self._short_term_memory = memory

    def set_long_term_memory(self, memory):
        """设置长期记忆"""
        self._long_term_memory = memory

    def semantic_search(
        self,
        query: str,
        memory_type: str = "all",
        limit: int = 5,
        threshold: float = 0.3
    ) -> List[MemoryEntry]:
        """
        语义检索

        Args:
            query: 检索查询
            memory_type: 记忆类型 ("short", "long", "all")
            limit: 返回结果数量限制
            threshold: 相似度阈值
        """
        results = []

        if memory_type in ["working", "all"]:
            results.extend(self._search_working(query))

        if memory_type in ["short", "all"]:
            results.extend(self._search_short_term(query))

        if memory_type in ["long", "all"]:
            results.extend(self._search_long_term(query))

        # 按相关度排序
        results.sort(key=lambda x: x.final_score, reverse=True)

        # 过滤低于阈值的
        results = [r for r in results if r.final_score >= threshold]

        return results[:limit]

    def _search_working(self, query: str) -> List[MemoryEntry]:
        """搜索工作记忆"""
        results = []
        if not self._working_memory:
            return results

        query_lower = query.lower()

        # 搜索消息
        for msg in self._working_memory.messages:
            if query_lower in msg.get("content", "").lower():
                results.append(MemoryEntry(
                    content=msg["content"],
                    source="working",
                    relevance=0.8,
                    recency=1.0,  # 工作记忆总是最新的
                    authority=0.5
                ))

        # 搜索任务
        if self._working_memory.current_task:
            task_desc = self._working_memory.current_task.get("description", "")
            if query_lower in task_desc.lower():
                results.append(MemoryEntry(
                    content=task_desc,
                    source="working/task",
                    relevance=0.9,
                    recency=1.0,
                    authority=0.8
                ))

        return results

    def _search_short_term(self, query: str) -> List[MemoryEntry]:
        """搜索短期记忆"""
        results = []
        if not self._short_term_memory:
            return results

        query_lower = query.lower()

        # 搜索任务记忆
        for task_mem in self._short_term_memory.task_memories:
            if query_lower in task_mem.summary.lower():
                results.append(MemoryEntry(
                    content=task_mem.summary,
                    source="short/task",
                    relevance=0.7,
                    recency=0.6,
                    authority=0.7
                ))

        # 搜索实体
        for entity in self._short_term_memory.entities:
            if query_lower in entity.description.lower():
                results.append(MemoryEntry(
                    content=f"{entity.name}: {entity.description}",
                    source="short/entity",
                    relevance=0.8,
                    recency=0.5,
                    authority=0.6
                ))

        return results

    def _search_long_term(self, query: str) -> List[MemoryEntry]:
        """搜索长期记忆"""
        results = []
        if not self._long_term_memory:
            return results

        # 使用长期记忆的语义搜索
        search_results = self._long_term_memory.semantic_search(query, limit=5)

        for sr in search_results:
            results.append(MemoryEntry(
                content=sr.get("content", ""),
                source=f"long/{sr.get('type', 'unknown')}",
                relevance=sr.get("relevance", 0.5),
                recency=0.5,  # 长期记忆的时效性需要单独计算
                authority=0.7
            ))

        return results

    def context_aware_retrieve(
        self,
        current_context: Dict[str, Any]
    ) -> List[MemoryEntry]:
        """
        上下文感知检索

        Args:
            current_context: 包含 task, files, entities 等的上下文
        """
        results = []

        task = current_context.get("task", "")
        files = current_context.get("files", [])
        entities = current_context.get("entities", [])

        # 基于任务检索
        if task:
            results.extend(self.semantic_search(task, limit=3))

        # 基于文件检索
        for file_path in files[:3]:
            file_name = file_path.split("/")[-1].split("\\")[-1]
            results.extend(self.semantic_search(file_name, memory_type="long", limit=2))

        # 基于实体检索
        for entity in entities[:3]:
            results.extend(self.semantic_search(entity, memory_type="long", limit=2))

        # 去重并排序
        seen = set()
        unique_results = []
        for r in results:
            if r.content not in seen:
                seen.add(r.content)
                unique_results.append(r)

        return unique_results[:5]
