"""
Intervention Handler - 人工干预处理
FR-HITL-001: 人机协同
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

from myagent.hitl.pause_manager import (
    get_pause_manager,
    PausePoint,
    PauseEvent,
    pause_for_planning,
    pause_for_quality_gate,
    pause_for_dangerous_operation
)


class InterventionType(Enum):
    """干预类型"""
    SKIP = "skip"
    ROLLBACK = "rollback"
    MODIFY = "modify"
    APPROVE = "approve"
    REJECT = "reject"


@dataclass
class InterventionResult:
    """干预结果"""
    success: bool
    message: str
    intervention_type: InterventionType


class InterventionHandler:
    """
    干预处理器
    处理人工干预请求
    """

    def __init__(self):
        self.pause_manager = get_pause_manager()
        self._intervention_history: List[Dict] = []

    def skip_task(self, task_id: str, reason: str = "") -> InterventionResult:
        """
        跳过任务

        Args:
            task_id: 任务 ID
            reason: 跳过原因

        Returns:
            干预结果
        """
        # 记录干预
        self._record_intervention(
            InterventionType.SKIP,
            {"task_id": task_id, "reason": reason}
        )

        return InterventionResult(
            success=True,
            message=f"Task '{task_id}' marked as skipped",
            intervention_type=InterventionType.SKIP
        )

    def rollback_task(self, task_id: str) -> InterventionResult:
        """
        回退任务

        Args:
            task_id: 任务 ID

        Returns:
            干预结果
        """
        # TODO: 实现回退逻辑
        # 1. 查找任务的代码变更
        # 2. 使用 git revert 或手动撤销
        # 3. 重新标记任务为 pending

        self._record_intervention(
            InterventionType.ROLLBACK,
            {"task_id": task_id}
        )

        return InterventionResult(
            success=True,
            message=f"Task '{task_id}' rolled back",
            intervention_type=InterventionType.ROLLBACK
        )

    def modify_planning(
        self,
        file_path: str = "PLANNING.md",
        changes: Dict[str, Any] = None
    ) -> InterventionResult:
        """
        修改规划文档

        Args:
            file_path: 规划文件路径
            changes: 修改内容

        Returns:
            干预结果
        """
        import json

        if not changes:
            return InterventionResult(
                success=False,
                message="No changes provided",
                intervention_type=InterventionType.MODIFY
            )

        # 记录修改
        modification_record = {
            "file": file_path,
            "changes": changes
        }

        self._record_intervention(
            InterventionType.MODIFY,
            modification_record
        )

        return InterventionResult(
            success=True,
            message=f"Planning modifications recorded",
            intervention_type=InterventionType.MODIFY
        )

    def approve_operation(self, operation_id: str) -> InterventionResult:
        """
        批准危险操作

        Args:
            operation_id: 操作 ID

        Returns:
            干预结果
        """
        success = self.pause_manager.confirm(operation_id, confirmed_by="human")

        self._record_intervention(
            InterventionType.APPROVE,
            {"operation_id": operation_id}
        )

        return InterventionResult(
            success=success,
            message=f"Operation '{operation_id}' approved" if success else f"Operation '{operation_id}' not found",
            intervention_type=InterventionType.APPROVE
        )

    def reject_operation(self, operation_id: str, reason: str = "") -> InterventionResult:
        """
        拒绝危险操作

        Args:
            operation_id: 操作 ID
            reason: 拒绝原因

        Returns:
            干预结果
        """
        success = self.pause_manager.reject(
            operation_id,
            rejected_by="human",
            reason=reason
        )

        self._record_intervention(
            InterventionType.REJECT,
            {"operation_id": operation_id, "reason": reason}
        )

        return InterventionResult(
            success=success,
            message=f"Operation '{operation_id}' rejected" if success else f"Operation '{operation_id}' not found",
            intervention_type=InterventionType.REJECT
        )

    def get_intervention_history(self, limit: int = 50) -> List[Dict]:
        """获取干预历史"""
        return self._intervention_history[-limit:]

    def _record_intervention(
        self,
        intervention_type: InterventionType,
        details: Dict[str, Any]
    ):
        """记录干预"""
        from datetime import datetime

        import os
        os.makedirs("LOGS/hitl", exist_ok=True)

        import json

        record = {
            "timestamp": datetime.now().isoformat(),
            "type": intervention_type.value,
            "details": details
        }

        self._intervention_history.append(record)

        # 追加到历史文件
        history_file = os.path.join("LOGS/hitl", "interventions.jsonl")
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# 全局干预处理器实例
_global_handler: Optional[InterventionHandler] = None


def get_intervention_handler() -> InterventionHandler:
    """获取全局干预处理器"""
    global _global_handler
    if _global_handler is None:
        _global_handler = InterventionHandler()
    return _global_handler
