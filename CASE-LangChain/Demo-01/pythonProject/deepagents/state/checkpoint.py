"""
Checkpoint - 状态快照
FR-EXEC-001.4: 状态持久化
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class WorkflowState:
    """工作流状态"""
    current_phase: str
    completed_phases: List[str] = field(default_factory=list)
    task_status: Dict[str, str] = field(default_factory=dict)  # task_id -> status


@dataclass
class AgentState:
    """Agent 运行时状态"""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    files: Dict[str, str] = field(default_factory=dict)  # path -> content hash
    todos: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SnapshotPaths:
    """快照路径"""
    src_dir: str
    logs_dir: str


@dataclass
class Checkpoint:
    """检查点快照"""
    id: str
    timestamp: str
    workflow: WorkflowState
    agent: AgentState
    snapshots: SnapshotPaths


class CheckpointManager:
    """
    检查点管理器
    管理状态快照，支持断点续跑
    """

    def __init__(self, checkpoint_dir: str = "LOGS/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        checkpoint_id: str,
        workflow_state: WorkflowState,
        agent_state: AgentState
    ) -> str:
        """
        保存检查点

        Args:
            checkpoint_id: 检查点 ID
            workflow_state: 工作流状态
            agent_state: Agent 状态

        Returns:
            检查点文件路径
        """
        # 创建快照目录
        snapshot_dir = self.checkpoint_dir / checkpoint_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # 保存工作流状态
        workflow_file = snapshot_dir / "workflow_state.json"
        with open(workflow_file, "w", encoding="utf-8") as f:
            json.dump({
                "current_phase": workflow_state.current_phase,
                "completed_phases": workflow_state.completed_phases,
                "task_status": workflow_state.task_status
            }, f, ensure_ascii=False, indent=2)

        # 保存 Agent 状态
        agent_file = snapshot_dir / "agent_state.json"
        with open(agent_file, "w", encoding="utf-8") as f:
            json.dump({
                "messages": agent_state.messages,
                "files": agent_state.files,
                "todos": agent_state.todos
            }, f, ensure_ascii=False, indent=2)

        # 保存元数据
        meta_file = snapshot_dir / "meta.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump({
                "id": checkpoint_id,
                "timestamp": datetime.now().isoformat(),
                "workflow_file": str(workflow_file),
                "agent_file": str(agent_file)
            }, f, ensure_ascii=False, indent=2)

        return str(snapshot_dir)

    def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        加载检查点

        Args:
            checkpoint_id: 检查点 ID

        Returns:
            检查点对象
        """
        snapshot_dir = self.checkpoint_dir / checkpoint_id
        if not snapshot_dir.exists():
            return None

        try:
            # 加载工作流状态
            workflow_file = snapshot_dir / "workflow_state.json"
            with open(workflow_file, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)

            workflow_state = WorkflowState(
                current_phase=workflow_data["current_phase"],
                completed_phases=workflow_data.get("completed_phases", []),
                task_status=workflow_data.get("task_status", {})
            )

            # 加载 Agent 状态
            agent_file = snapshot_dir / "agent_state.json"
            with open(agent_file, "r", encoding="utf-8") as f:
                agent_data = json.load(f)

            agent_state = AgentState(
                messages=agent_data.get("messages", []),
                files=agent_data.get("files", {}),
                todos=agent_data.get("todos", [])
            )

            return Checkpoint(
                id=checkpoint_id,
                timestamp=datetime.now().isoformat(),
                workflow=workflow_state,
                agent=agent_state,
                snapshots=SnapshotPaths(
                    src_dir="src",
                    logs_dir="LOGS"
                )
            )

        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            return None

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """
        列出所有检查点

        Returns:
            检查点列表
        """
        checkpoints = []

        for checkpoint_dir in self.checkpoint_dir.iterdir():
            if checkpoint_dir.is_dir():
                meta_file = checkpoint_dir / "meta.json"
                if meta_file.exists():
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        checkpoints.append(meta)

        # 按时间排序
        checkpoints.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return checkpoints

    def get_latest_checkpoint(self) -> Optional[str]:
        """
        获取最新检查点 ID

        Returns:
            检查点 ID
        """
        checkpoints = self.list_checkpoints()
        if checkpoints:
            return checkpoints[0].get("id")
        return None

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        删除检查点

        Args:
            checkpoint_id: 检查点 ID

        Returns:
            是否成功删除
        """
        import shutil

        snapshot_dir = self.checkpoint_dir / checkpoint_id
        if snapshot_dir.exists():
            shutil.rmtree(snapshot_dir)
            return True
        return False


# 全局检查点管理器
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """获取全局检查点管理器"""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager
