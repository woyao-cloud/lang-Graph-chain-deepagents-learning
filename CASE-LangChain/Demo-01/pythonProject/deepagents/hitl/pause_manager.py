"""
Pause Manager - 暂停点管理器
FR-HITL-001: 人机协同
"""

import os
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


class PausePoint(Enum):
    """暂停点类型"""
    PLANNING_CONFIRM = "planning_confirm"  # 规划确认
    QUALITY_GATE_FAILED = "quality_gate_failed"  # 质量门禁失败
    DANGEROUS_OPERATION = "dangerous_operation"  # 危险操作
    TASK_COMPLETION = "task_completion"  # 任务完成
    MANUAL_INTERVENTION = "manual_intervention"  # 手动干预


class PauseStatus(Enum):
    """暂停状态"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    SKIPPED = "skipped"


@dataclass
class PauseEvent:
    """暂停事件"""
    event_id: str
    pause_type: PausePoint
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    status: PauseStatus = PauseStatus.PENDING
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class PauseManager:
    """
    暂停点管理器
    管理所有需要人工确认的暂停点
    """

    def __init__(self, pause_dir: str = "LOGS/hitl"):
        self.pause_dir = pause_dir
        self._events: Dict[str, PauseEvent] = {}
        self._callbacks: Dict[PausePoint, List[Callable]] = {}

        # 确保目录存在
        os.makedirs(pause_dir, exist_ok=True)

        # 加载已有的暂停事件
        self._load_events()

    def _load_events(self):
        """加载已有的暂停事件"""
        import json

        events_file = os.path.join(self.pause_dir, "pause_events.json")
        if os.path.exists(events_file):
            try:
                with open(events_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for event_data in data.values():
                        self._events[event_data["event_id"]] = PauseEvent(
                            event_id=event_data["event_id"],
                            pause_type=PausePoint(event_data["pause_type"]),
                            message=event_data["message"],
                            details=event_data.get("details", {}),
                            created_at=event_data.get("created_at", ""),
                            status=PauseStatus(event_data.get("status", "pending")),
                            resolved_at=event_data.get("resolved_at"),
                            resolved_by=event_data.get("resolved_by")
                        )
            except Exception:
                pass

    def _save_events(self):
        """保存暂停事件"""
        import json

        events_file = os.path.join(self.pause_dir, "pause_events.json")
        data = {}
        for event_id, event in self._events.items():
            data[event_id] = {
                "event_id": event.event_id,
                "pause_type": event.pause_type.value,
                "message": event.message,
                "details": event.details,
                "created_at": event.created_at,
                "status": event.status.value,
                "resolved_at": event.resolved_at,
                "resolved_by": event.resolved_by
            }

        with open(events_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def register_callback(self, pause_type: PausePoint, callback: Callable):
        """注册暂停回调"""
        if pause_type not in self._callbacks:
            self._callbacks[pause_type] = []
        self._callbacks[pause_type].append(callback)

    def create_pause(
        self,
        pause_type: PausePoint,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建暂停点

        Args:
            pause_type: 暂停类型
            message: 暂停消息
            details: 详细信息

        Returns:
            事件 ID
        """
        import uuid

        event_id = str(uuid.uuid4())[:8]

        event = PauseEvent(
            event_id=event_id,
            pause_type=pause_type,
            message=message,
            details=details or {}
        )

        self._events[event_id] = event
        self._save_events()

        # 记录日志
        self._log_pause(event)

        return event_id

    def confirm(
        self,
        event_id: str,
        confirmed_by: str = "human"
    ) -> bool:
        """
        确认暂停点

        Returns:
            是否成功确认
        """
        event = self._events.get(event_id)
        if not event:
            return False

        event.status = PauseStatus.CONFIRMED
        event.resolved_at = datetime.now().isoformat()
        event.resolved_by = confirmed_by

        self._save_events()

        # 触发回调
        self._trigger_callbacks(event)

        return True

    def reject(
        self,
        event_id: str,
        rejected_by: str = "human",
        reason: str = ""
    ) -> bool:
        """
        拒绝暂停点

        Returns:
            是否成功拒绝
        """
        event = self._events.get(event_id)
        if not event:
            return False

        event.status = PauseStatus.REJECTED
        event.resolved_at = datetime.now().isoformat()
        event.resolved_by = rejected_by
        event.details["rejection_reason"] = reason

        self._save_events()

        return True

    def skip(self, event_id: str) -> bool:
        """跳过暂停点"""
        event = self._events.get(event_id)
        if not event:
            return False

        event.status = PauseStatus.SKIPPED
        event.resolved_at = datetime.now().isoformat()

        self._save_events()

        return True

    def get_pending_pauses(self) -> List[PauseEvent]:
        """获取所有待处理的暂停"""
        return [
            e for e in self._events.values()
            if e.status == PauseStatus.PENDING
        ]

    def is_blocked(self) -> bool:
        """检查是否有待处理的暂停"""
        pending = self.get_pending_pauses()
        return len(pending) > 0

    def _trigger_callbacks(self, event: PauseEvent):
        """触发暂停回调"""
        callbacks = self._callbacks.get(event.pause_type, [])
        for callback in callbacks:
            try:
                callback(event)
            except Exception:
                pass

    def _log_pause(self, event: PauseEvent):
        """记录暂停日志"""
        import json

        log_file = os.path.join(
            self.pause_dir,
            f"pause_{event.pause_type.value}_{event.event_id}.json"
        )

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump({
                "event_id": event.event_id,
                "type": event.pause_type.value,
                "message": event.message,
                "details": event.details,
                "created_at": event.created_at
            }, f, ensure_ascii=False, indent=2)


# 全局暂停管理器实例
_global_pause_manager: Optional[PauseManager] = None


def get_pause_manager() -> PauseManager:
    """获取全局暂停管理器"""
    global _global_pause_manager
    if _global_pause_manager is None:
        _global_pause_manager = PauseManager()
    return _global_pause_manager


def pause_for_planning(phase_name: str) -> str:
    """为规划阶段创建暂停"""
    manager = get_pause_manager()
    return manager.create_pause(
        PausePoint.PLANNING_CONFIRM,
        f"Planning phase '{phase_name}' requires confirmation",
        {"phase": phase_name}
    )


def pause_for_quality_gate(failures: List[str]) -> str:
    """为质量门禁失败创建暂停"""
    manager = get_pause_manager()
    return manager.create_pause(
        PausePoint.QUALITY_GATE_FAILED,
        f"Quality gate failed with {len(failures)} issues",
        {"failures": failures}
    )


def pause_for_dangerous_operation(operation: str, command: str) -> str:
    """为危险操作创建暂停"""
    manager = get_pause_manager()
    return manager.create_pause(
        PausePoint.DANGEROUS_OPERATION,
        f"Dangerous operation requires confirmation: {operation}",
        {"operation": operation, "command": command}
    )
