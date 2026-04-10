"""
Working Memory - 工作记忆（单次对话）
FR-EXEC-001.3: 记忆管理
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorkingMemory:
    """
    工作记忆
    单次对话内的上下文信息
    """
    messages: List[Dict[str, str]] = field(default_factory=list)
    current_task: Optional[Dict[str, Any]] = None
    files: Dict[str, str] = field(default_factory=dict)  # path -> content
    todos: List[Dict[str, Any]] = field(default_factory=list)
    skills_metadata: Dict[str, Any] = field(default_factory=dict)

    # Token 统计
    token_count: int = 0
    token_limit: int = 128000  # 默认 128K tokens

    def add_message(self, role: str, content: str):
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def set_task(self, task_id: str, description: str, progress: float = 0.0):
        """设置当前任务"""
        self.current_task = {
            "id": task_id,
            "description": description,
            "progress": progress,
            "started_at": datetime.now().isoformat()
        }

    def update_progress(self, progress: float):
        """更新任务进度"""
        if self.current_task:
            self.current_task["progress"] = progress

    def add_todo(self, title: str, status: str = "pending", **kwargs):
        """添加 Todo"""
        self.todos.append({
            "title": title,
            "status": status,
            "created_at": datetime.now().isoformat(),
            **kwargs
        })

    def complete_todo(self, title: str):
        """完成 Todo"""
        for todo in self.todos:
            if todo["title"] == title:
                todo["status"] = "completed"
                todo["completed_at"] = datetime.now().isoformat()

    def get_token_usage(self) -> Dict[str, int]:
        """获取 Token 使用情况"""
        return {
            "used": self.token_count,
            "limit": self.token_limit,
            "remaining": self.token_limit - self.token_count
        }

    def is_near_limit(self, threshold: float = 0.8) -> bool:
        """是否接近 Token 限制"""
        return self.token_count >= self.token_limit * threshold

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "messages": self.messages,
            "current_task": self.current_task,
            "files": self.files,
            "todos": self.todos,
            "skills_metadata": self.skills_metadata,
            "token_count": self.token_count,
            "token_limit": self.token_limit
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkingMemory":
        """从字典反序列化"""
        return cls(
            messages=data.get("messages", []),
            current_task=data.get("current_task"),
            files=data.get("files", {}),
            todos=data.get("todos", []),
            skills_metadata=data.get("skills_metadata", {}),
            token_count=data.get("token_count", 0),
            token_limit=data.get("token_limit", 128000)
        )
