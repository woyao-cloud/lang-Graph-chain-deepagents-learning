"""Log manager for MyAgent.

Manages LOGS directory and agent execution logs.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from myagent.models import ExecutionResult

if TYPE_CHECKING:
    pass


class LogManager:
    """Manages execution logs for agents."""

    def __init__(self, logs_dir: Path):
        """Initialize log manager.

        Args:
            logs_dir: Directory for logs
        """
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.agent_logs_dir = logs_dir / "agents"
        self.agent_logs_dir.mkdir(exist_ok=True)

    def log_agent_execution(
        self,
        agent_name: str,
        task_name: str,
        input_data: dict[str, Any],
        output: str,
        result: ExecutionResult | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Log agent execution.

        Args:
            agent_name: Agent name
            task_name: Task name
            input_data: Input data
            output: Output
            result: Execution result
            metadata: Additional metadata

        Returns:
            Path to log file
        """
        timestamp = datetime.now().isoformat()
        log_id = f"{agent_name}_{task_name}_{int(time.time())}"

        log_data = {
            "log_id": log_id,
            "timestamp": timestamp,
            "agent_name": agent_name,
            "task_name": task_name,
            "input": input_data,
            "output": output,
            "result": asdict(result) if result else None,
            "metadata": metadata or {},
        }

        # Write JSON log
        log_file = self.agent_logs_dir / f"{agent_name}_{task_name}.json"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")

        # Also write human-readable log
        human_log = self.agent_logs_dir / f"{agent_name}_{task_name}.log"
        with open(human_log, "a", encoding="utf-8") as f:
            f.write(f"{'=' * 60}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Agent: {agent_name}\n")
            f.write(f"Task: {task_name}\n")
            f.write(f"Status: {result.success if result else 'unknown'}\n")
            if result:
                f.write(f"Duration: {result.duration_seconds:.2f}s\n")
            f.write(f"{'-' * 60}\n")
            f.write(f"Output:\n{output}\n")
            f.write("\n")

        return log_file

    def get_agent_logs(self, agent_name: str) -> list[dict[str, Any]]:
        """Get all logs for an agent.

        Args:
            agent_name: Agent name

        Returns:
            List of log entries
        """
        logs: list[dict[str, Any]] = []
        log_files = self.agent_logs_dir.glob(f"{agent_name}_*.json")

        for log_file in log_files:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

        return logs

    def tail_logs(
        self,
        agent_name: str,
        task_name: str | None = None,
        lines: int = 50,
    ) -> str:
        """Tail agent logs.

        Args:
            agent_name: Agent name
            task_name: Optional task name filter
            lines: Number of lines to return

        Returns:
            Log content
        """
        if task_name:
            log_file = self.agent_logs_dir / f"{agent_name}_{task_name}.log"
            if log_file.exists():
                content = log_file.read_text(encoding="utf-8")
                return "\n".join(content.split("\n")[-lines:])

        # Combine all logs for agent
        log_file = self.agent_logs_dir / f"{agent_name}.log"
        if log_file.exists():
            content = log_file.read_text(encoding="utf-8")
            return "\n".join(content.split("\n")[-lines:])

        return ""

    def get_logs_summary(self) -> dict[str, Any]:
        """Get summary of all logs.

        Returns:
            Summary dict
        """
        summary = {
            "total_logs": 0,
            "agents": {},
            "last_updated": None,
        }

        for log_file in self.agent_logs_dir.glob("*.json"):
            # Parse filename
            parts = log_file.stem.split("_")
            if len(parts) >= 2:
                agent_name = parts[0]
                task_name = "_".join(parts[1:])

                if agent_name not in summary["agents"]:
                    summary["agents"][agent_name] = {
                        "task_count": 0,
                        "last_task": None,
                    }

                summary["agents"][agent_name]["task_count"] += 1
                summary["agents"][agent_name]["last_task"] = task_name
                summary["total_logs"] += 1

                # Get last updated time
                mtime = log_file.stat().st_mtime
                if summary["last_updated"] is None or mtime > summary["last_updated"]:
                    summary["last_updated"] = mtime

        return summary
