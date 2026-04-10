"""
Command Execution Tools - 命令执行工具
FR-EXEC-001.2: 工具调用
NF-SEC-002: 命令白名单
"""

import subprocess
import shlex
from typing import List, Dict, Optional

from langchain.tools import tool


# 安全命令白名单
SAFE_COMMANDS = {
    # Python
    "python", "python3", "pip", "pip3", "pytest", "black", "ruff", "mypy",
    # JavaScript/Node
    "npm", "npx", "node", "yarn", "pnpm",
    # Git
    "git",
    # Shell
    "ls", "dir", "cat", "type", "mkdir", "rm", "cp", "mv", "find",
    # Docker
    "docker", "docker-compose",
    # Build
    "make", "cmake", "gcc", "g++",
    # Go
    "go", "gofmt",
    # Rust
    "cargo", "rustc",
}

# 危险命令（需要二次确认）
DANGEROUS_COMMANDS = {
    "rm -rf", "sudo", "chmod 777", "git push --force",
    "git push origin --delete", "shutdown", "reboot",
}

# 命令别名映射
COMMAND_ALIASES = {
    "rm": "rm -i",  # 交互式删除
    "del": "del /p",  # Windows 交互式删除
}


class CommandWhitelist:
    """
    命令白名单验证器
    """

    @classmethod
    def is_allowed(cls, command: str) -> tuple[bool, bool]:
        """
        检查命令是否允许执行

        Returns:
            (is_allowed, needs_confirmation)
        """
        # 检查是否是危险命令
        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in command:
                return False, True

        # 解析命令
        parts = shlex.split(command)
        if not parts:
            return False, False

        base_cmd = parts[0]

        # 检查白名单
        is_allowed = base_cmd in SAFE_COMMANDS

        # 检查是否有任何别名匹配
        for alias, replacement in COMMAND_ALIASES.items():
            if base_cmd == alias:
                return True, False

        return is_allowed, False

    @classmethod
    def sanitize_command(cls, command: str) -> str:
        """规范化命令"""
        parts = shlex.split(command)
        if not parts:
            return command

        base_cmd = parts[0]

        # 应用别名
        if base_cmd in COMMAND_ALIASES:
            parts[0] = COMMAND_ALIASES[base_cmd]

        return " ".join(parts)


@tool
def execute(command: str, cwd: str = ".") -> str:
    """Execute a shell command (whitelist only).

    Args:
        command: The command to execute.
        cwd: The working directory.
    """
    import os

    # 验证命令
    is_allowed, needs_confirmation = CommandWhitelist.is_allowed(command)

    if not is_allowed and not needs_confirmation:
        return f"Error: Command not in whitelist: {command[:50]}..."

    if needs_confirmation:
        return f"Error: Dangerous command requires confirmation: {command[:50]}..."

    # 规范化命令
    command = CommandWhitelist.sanitize_command(command)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=300  # 5分钟超时
        )

        output = result.stdout + result.stderr
        if result.returncode != 0:
            output = f"[Exit code: {result.returncode}]\n{output}"

        return output or "Command executed (no output)"

    except subprocess.TimeoutExpired:
        return "Error: Command timed out (5 minutes limit)"
    except Exception as e:
        return f"Error: {str(e)}"


class CommandRecorder:
    """
    命令执行记录器
    记录所有执行的命令（用于审计）
    """

    def __init__(self, log_dir: str = "LOGS/commands"):
        self.log_dir = log_dir
        self.history: List[Dict] = []

    def record(self, command: str, output: str, return_code: int):
        """记录命令执行"""
        import json
        from datetime import datetime

        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "return_code": return_code,
            "output_length": len(output),
        }

        self.history.append(entry)

        # 写入日志文件
        import os
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = os.path.join(self.log_dir, f"commands_{datetime.now().strftime('%Y%m%d')}.jsonl")

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_history(self, limit: int = 100) -> List[Dict]:
        """获取历史记录"""
        return self.history[-limit:]
