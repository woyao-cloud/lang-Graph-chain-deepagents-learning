"""
Commit Generator - Commit Message 生成
FR-VCS-001.2: 提交生成
"""

import subprocess
import json
from typing import Dict, Any, Optional
from datetime import datetime


# 提交类型
COMMIT_TYPES = {
    "feat": "新功能",
    "fix": "错误修复",
    "refactor": "代码重构",
    "docs": "文档更新",
    "test": "测试相关",
    "chore": "构建/工具相关",
    "perf": "性能优化",
    "ci": "CI/CD 相关",
}


class CommitGenerator:
    """
    Commit Message 生成器
    生成符合规范的 Commit Message
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _run_git(self, args: list) -> tuple[int, str, str]:
        """执行 git 命令"""
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=self.repo_path
        )
        return result.returncode, result.stdout, result.stderr

    def generate_commit_message(
        self,
        commit_type: str,
        description: str,
        body: Optional[str] = None,
        footer: Optional[str] = None,
        issues: Optional[list] = None
    ) -> str:
        """
        生成 Commit Message

        Args:
            commit_type: 提交类型 (feat/fix/refactor/docs/test/chore/perf/ci)
            description: 简短描述
            body: 详细描述（可选）
            footer: 脚注信息（可选）
            issues: 关联的 Issue（可选）

        Returns:
            格式化的 Commit Message
        """
        lines = [f"{commit_type}: {description}"]

        if body:
            lines.append("")
            lines.append(body)

        if footer:
            lines.append("")
            lines.append(footer)

        if issues:
            lines.append("")
            for issue in issues:
                lines.append(f"Closes: #{issue}")

        return "\n".join(lines)

    def analyze_changes(self) -> Dict[str, Any]:
        """
        分析变更生成建议

        Returns:
            变更分析结果
        """
        # 获取变更的文件
        returncode, stdout, _ = self._run_git(["diff", "--stat"])
        if returncode != 0:
            return {"type": "unknown", "files": []}

        # 分析变更统计
        stats = {}
        for line in stdout.strip().split("\n"):
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    file = parts[-1]
                    stats[file] = line

        # 获取变更类型
        returncode, stdout, _ = self._run_git(["diff", "--cached", "--name-only"])
        staged_files = stdout.strip().split("\n") if stdout.strip() else []

        # 建议提交类型
        commit_type = self._suggest_commit_type(staged_files)

        return {
            "staged_files": staged_files,
            "stats": stats,
            "suggested_type": commit_type,
            "description": self._generate_description(staged_files)
        }

    def _suggest_commit_type(self, files: list) -> str:
        """建议提交类型"""
        if not files:
            return "chore"

        # 根据文件类型判断
        for file in files:
            if file.startswith("tests/") or file.endswith("_test.py"):
                return "test"
            if file.startswith("docs/") or file.endswith(".md"):
                return "docs"
            if file.endswith(".py"):
                return "feat"
            if file.endswith(".js") or file.endswith(".ts"):
                return "feat"

        return "feat"

    def _generate_description(self, files: list) -> str:
        """生成简短描述"""
        if not files:
            return "update project"

        # 简化文件路径
        descriptions = []
        for file in files[:3]:
            name = file.split("/")[-1]
            descriptions.append(name)

        if len(files) > 3:
            return f"{', '.join(descriptions)} and {len(files) - 3} more"
        return ", ".join(descriptions)

    def commit(
        self,
        message: str,
        all: bool = True
    ) -> tuple[bool, str]:
        """
        执行提交

        Args:
            message: 提交信息
            all: 是否提交所有变更

        Returns:
            (success, message)
        """
        # Stage changes
        stage_args = ["add"]
        if all:
            stage_args.append("-A")
        else:
            stage_args.append(".")

        returncode, _, stderr = self._run_git(stage_args)
        if returncode != 0:
            return False, f"Failed to stage changes: {stderr}"

        # Commit
        returncode, stdout, stderr = self._run_git(["commit", "-m", message])

        if returncode == 0:
            return True, f"Committed: {message[:50]}..."
        else:
            return False, f"Failed to commit: {stderr}"

    def amend_commit(self, message: Optional[str] = None) -> tuple[bool, str]:
        """
        修改最后一次提交

        Args:
            message: 新的提交信息（可选）

        Returns:
            (success, message)
        """
        args = ["commit", "--amend"]
        if message:
            args.extend(["-m", message])
        else:
            args.append("--no-edit")

        returncode, stdout, stderr = self._run_git(args)

        if returncode == 0:
            return True, "Commit amended"
        else:
            return False, f"Failed to amend commit: {stderr}"


# 便捷函数
def auto_commit(description: str, commit_type: str = "feat") -> tuple[bool, str]:
    """
    自动生成并执行提交

    Args:
        description: 提交描述
        commit_type: 提交类型

    Returns:
        (success, message)
    """
    generator = CommitGenerator()

    # 分析变更
    analysis = generator.analyze_changes()

    # 生成提交信息
    message = generator.generate_commit_message(
        commit_type=commit_type,
        description=description or analysis["description"]
    )

    # 执行提交
    return generator.commit(message)
