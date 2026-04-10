"""
Git Operations Tools - Git 操作工具
FR-EXEC-001.2: 工具调用
"""

import subprocess
from typing import List, Optional
from pathlib import Path

from langchain.tools import tool


class GitOperations:
    """
    Git 操作工具集
    提供安全的 Git 操作功能
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _run_git(self, args: List[str]) -> tuple[int, str, str]:
        """执行 git 命令"""
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=self.repo_path
        )
        return result.returncode, result.stdout, result.stderr

    def status(self) -> str:
        """获取 git 状态"""
        returncode, stdout, stderr = self._run_git(["status", "--short"])
        if returncode != 0:
            return f"Error: {stderr}"
        return stdout or "No changes"

    def branch_list(self) -> List[str]:
        """列出所有分支"""
        returncode, stdout, stderr = self._run_git(["branch", "-a"])
        if returncode != 0:
            return []
        return [line.strip() for line in stdout.split("\n") if line.strip()]

    def create_branch(self, branch_name: str) -> str:
        """创建新分支"""
        returncode, stdout, stderr = self._run_git(["checkout", "-b", branch_name])
        if returncode != 0:
            return f"Error: {stderr}"
        return f"Branch created: {branch_name}"

    def commit(self, message: str) -> str:
        """提交更改"""
        # Stage all changes
        returncode, _, stderr = self._run_git(["add", "-A"])
        if returncode != 0:
            return f"Error staging: {stderr}"

        # Commit
        returncode, stdout, stderr = self._run_git(["commit", "-m", message])
        if returncode != 0:
            return f"Error committing: {stderr}"
        return stdout or f"Committed: {message[:50]}..."

    def log(self, limit: int = 10) -> str:
        """获取提交日志"""
        returncode, stdout, stderr = self._run_git(["log", f"--oneline", f"-{limit}"])
        if returncode != 0:
            return f"Error: {stderr}"
        return stdout or "No commits"


# LangChain Tools
@tool
def git_status() -> str:
    """Get the current git status (short format)."""
    return GitOperations().status()


@tool
def git_branch_list() -> str:
    """List all git branches."""
    branches = GitOperations().branch_list()
    return "\n".join(branches) if branches else "No branches"


@tool
def git_create_branch(branch_name: str) -> str:
    """Create a new git branch.

    Args:
        branch_name: The name of the branch to create.
    """
    return GitOperations().create_branch(branch_name)


@tool
def git_commit(message: str) -> str:
    """Commit all changes with a message.

    Args:
        message: The commit message.
    """
    return GitOperations().commit(message)


@tool
def git_log(limit: int = 10) -> str:
    """Get recent git commit history.

    Args:
        limit: Number of commits to show.
    """
    return GitOperations().log(limit)
