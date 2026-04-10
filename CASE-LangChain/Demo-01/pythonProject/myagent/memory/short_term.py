"""
Short-term Memory - 短期记忆（单日会话）
FR-EXEC-001.3: 记忆管理
"""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, date


@dataclass
class TaskMemory:
    """
    任务记忆
    已完成任务的摘要信息
    """
    task_id: str
    summary: str
    key_decisions: List[str] = field(default_factory=list)
    learnings: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)  # 文件路径列表
    completed_at: str = ""


@dataclass
class Entity:
    """
    实体信息
    存储在记忆中的人物、项目、概念等实体
    """
    name: str
    entity_type: str  # "project", "module", "file", "person", "concept"
    description: str
    aliases: List[str] = field(default_factory=list)
    last_referenced_at: str = ""


@dataclass
class ShortTermMemory:
    """
    短期记忆
    单日会话内的累积信息
    """
    session_id: str
    session_start: str = ""
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    task_memories: List[TaskMemory] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)

    # 压缩统计
    original_tokens: int = 0
    compressed_tokens: int = 0
    compression_ratio: float = 1.0
    last_compressed_at: Optional[str] = None

    # Token 统计
    token_count: int = 0
    token_limit: int = 512000  # 默认 512K tokens

    def __post_init__(self):
        if not self.session_start:
            self.session_start = datetime.now().isoformat()

    def add_task_memory(self, task_memory: TaskMemory):
        """添加任务记忆"""
        self.task_memories.append(task_memory)

    def add_entity(self, entity: Entity):
        """添加实体"""
        self.entities.append(entity)

    def find_entity(self, name: str) -> Optional[Entity]:
        """查找实体"""
        for entity in self.entities:
            if entity.name == name or name in entity.aliases:
                return entity
        return None

    def compress(self, summary_model: str = "gpt-4") -> Dict[str, Any]:
        """
        压缩短期记忆
        生成摘要并清理历史
        """
        # 计算原始 token 数
        self.original_tokens = self._estimate_tokens()

        # 生成摘要
        summary = self._generate_summary()

        # 压缩后的数据结构
        compressed = {
            "session_id": self.session_id,
            "summary": summary,
            "task_count": len(self.task_memories),
            "entity_count": len(self.entities),
            "compressed_at": datetime.now().isoformat()
        }

        self.compressed_tokens = self._estimate_tokens_summary(compressed)
        self.compression_ratio = self.compressed_tokens / max(1, self.original_tokens)
        self.last_compressed_at = datetime.now().isoformat()

        return compressed

    def _estimate_tokens(self) -> int:
        """估算 token 数量（简单估计）"""
        text = json.dumps(self.conversation_history)
        return len(text) // 4  # 粗略估计

    def _estimate_tokens_summary(self, data: Dict) -> int:
        """估算摘要 token 数量"""
        text = json.dumps(data)
        return len(text) // 4

    def _generate_summary(self) -> str:
        """生成会话摘要"""
        # 提取关键信息
        task_summaries = [tm.summary for tm in self.task_memories]
        decisions = []
        for tm in self.task_memories:
            decisions.extend(tm.key_decisions)

        summary = f"Session {self.session_id}: {len(self.task_memories)} tasks completed"
        if task_summaries:
            summary += f"\nTasks: {', '.join(task_summaries[:5])}"
        if decisions:
            summary += f"\nKey decisions: {', '.join(decisions[:3])}"

        return summary

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "session_id": self.session_id,
            "session_start": self.session_start,
            "conversation_history": self.conversation_history,
            "task_memories": [
                {
                    "task_id": tm.task_id,
                    "summary": tm.summary,
                    "key_decisions": tm.key_decisions,
                    "learnings": tm.learnings,
                    "artifacts": tm.artifacts,
                    "completed_at": tm.completed_at
                }
                for tm in self.task_memories
            ],
            "entities": [
                {
                    "name": e.name,
                    "entity_type": e.entity_type,
                    "description": e.description,
                    "aliases": e.aliases,
                    "last_referenced_at": e.last_referenced_at
                }
                for e in self.entities
            ],
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": self.compression_ratio,
            "last_compressed_at": self.last_compressed_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShortTermMemory":
        """从字典反序列化"""
        stm = cls(
            session_id=data.get("session_id", ""),
            session_start=data.get("session_start", ""),
            conversation_history=data.get("conversation_history", []),
            original_tokens=data.get("original_tokens", 0),
            compressed_tokens=data.get("compressed_tokens", 0),
            compression_ratio=data.get("compression_ratio", 1.0),
            last_compressed_at=data.get("last_compressed_at")
        )

        # 反序列化任务记忆
        for tm_data in data.get("task_memories", []):
            stm.task_memories.append(TaskMemory(
                task_id=tm_data.get("task_id", ""),
                summary=tm_data.get("summary", ""),
                key_decisions=tm_data.get("key_decisions", []),
                learnings=tm_data.get("learnings", []),
                artifacts=tm_data.get("artifacts", []),
                completed_at=tm_data.get("completed_at", "")
            ))

        # 反序列化实体
        for e_data in data.get("entities", []):
            stm.entities.append(Entity(
                name=e_data.get("name", ""),
                entity_type=e_data.get("entity_type", ""),
                description=e_data.get("description", ""),
                aliases=e_data.get("aliases", []),
                last_referenced_at=e_data.get("last_referenced_at", "")
            ))

        return stm
