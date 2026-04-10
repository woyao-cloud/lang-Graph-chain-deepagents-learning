"""
Branch Manager - Git 分支管理
FR-VCS-001.1: 分支创建
"""

import subprocess
from typing import List, Optional
from pathlib import Path


class BranchManager:
    """
    Git 分支管理器
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

    def get_current_branch(self) -> Optional[str]:
        """获取当前分支"""
        returncode, stdout, _ = self._run_git(["branch", "--show-current"])
        if returncode == 0:
            return stdout.strip()
        return None

    def list_branches(self, all_branches: bool = False) -> List[str]:
        """列出分支"""
        args = ["branch"]
        if all_branches:
            args.append("-a")

        returncode, stdout, _ = self._run_git(args)
        if returncode != 0:
            return []

        branches = []
        for line in stdout.split("\n"):
            line = line.strip()
            # 移除 * 前缀（当前分支）
            if line.startswith("*"):
                line = line[1:].strip()
            if line:
                branches.append(line)

        return branches

    def create_branch(self, branch_name: str, checkout: bool = True) -> tuple[bool, str]:
        """
        创建分支

        Args:
            branch_name: 分支名称
            checkout: 是否切换到新分支

        Returns:
            (success, message)
        """
        # 检查分支是否已存在
        branches = self.list_branches()
        if branch_name in branches:
            return False, f"Branch '{branch_name}' already exists"

        # 创建分支
        if checkout:
            returncode, stdout, stderr = self._run_git(["checkout", "-b", branch_name])
        else:
            returncode, stdout, stderr = self._run_git(["branch", branch_name])

        if returncode == 0:
            return True, f"Branch '{branch_name}' created"
        else:
            return False, f"Failed to create branch: {stderr}"

    def switch_branch(self, branch_name: str) -> tuple[bool, str]:
        """
        切换分支

        Args:
            branch_name: 分支名称

        Returns:
            (success, message)
        """
        returncode, stdout, stderr = self._run_git(["checkout", branch_name])

        if returncode == 0:
            return True, f"Switched to branch '{branch_name}'"
        else:
            return False, f"Failed to switch branch: {stderr}"

    def delete_branch(self, branch_name: str, force: bool = False) -> tuple[bool, str]:
        """
        删除分支

        Args:
            branch_name: 分支名称
            force: 是否强制删除

        Returns:
            (success, message)
        """
        args = ["branch"]
        if force:
            args.append("-D")
        else:
            args.append("-d")
        args.append(branch_name)

        returncode, stdout, stderr = self._run_git(args)

        if returncode == 0:
            return True, f"Branch '{branch_name}' deleted"
        else:
            return False, f"Failed to delete branch: {stderr}"

    def get_branch_info(self, branch_name: str) -> dict:
        """
        获取分支信息

        Returns:
            分支信息字典
        """
        # 获取分支最后提交
        returncode, stdout, _ = self._run_git([
            "log", branch_name, "-1",
            "--format=%H|%an|%ae|%at|%s"
        ])

        if returncode == 0 and stdout:
            parts = stdout.strip().split("|")
            if len(parts) >= 5:
                return {
                    "name": branch_name,
                    "sha": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "timestamp": parts[3],
                    "message": parts[4]
                }

        return {"name": branch_name}


def create_feature_branch(module_name: str, prefix: str = "feat/agent") -> tuple[bool, str]:
    """
    创建 Feature 分支

    Args:
        module_name: 模块名称
        prefix: 分支前缀

    Returns:
        (success, message)
    """
    manager = BranchManager()
    branch_name = f"{prefix}-{module_name}"
    return manager.create_branch(branch_name)
