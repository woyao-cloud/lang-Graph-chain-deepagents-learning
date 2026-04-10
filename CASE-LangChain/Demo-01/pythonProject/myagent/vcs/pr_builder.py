"""
PR Builder - Pull Request 生成
FR-VCS-001.3: PR 生成
"""

import subprocess
from typing import Dict, Any, List, Optional


class PRBuilder:
    """
    Pull Request 构建器
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self._remote_url = self._get_remote_url()

    def _run_git(self, args: List[str]) -> tuple[int, str, str]:
        """执行 git 命令"""
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=self.repo_path
        )
        return result.returncode, result.stdout, result.stderr

    def _get_remote_url(self) -> str:
        """获取远程仓库 URL"""
        returncode, stdout, _ = self._run_git(["remote", "get-url", "origin"])
        if returncode == 0:
            return stdout.strip()
        return ""

    def get_repo_info(self) -> Dict[str, str]:
        """获取仓库信息"""
        info = {}

        # 从远程 URL 提取 owner/repo
        # 支持格式:
        # - https://github.com/owner/repo.git
        # - git@github.com:owner/repo.git
        if self._remote_url:
            if "github.com" in self._remote_url:
                if "@" in self._remote_url:
                    # SSH 格式
                    parts = self._remote_url.split(":")
                    if len(parts) >= 2:
                        repo_part = parts[1].replace(".git", "")
                        info["owner"], info["repo"] = repo_part.split("/")
                else:
                    # HTTPS 格式
                    parts = self._remote_url.replace(".git", "").split("/")
                    if len(parts) >= 2:
                        info["owner"] = parts[-2]
                        info["repo"] = parts[-1]

        info["url"] = self._remote_url
        return info

    def create_pr_body(
        self,
        title: str,
        description: str,
        changes: List[str] = None,
        testing: List[str] = None,
        notes: List[str] = None
    ) -> str:
        """
        生成 PR 描述

        Args:
            title: PR 标题
            description: PR 描述
            changes: 变更列表
            testing: 测试说明
            notes: 其他说明

        Returns:
            PR 描述内容
        """
        lines = [
            f"## {title}",
            "",
            description,
            ""
        ]

        if changes:
            lines.append("## Changes")
            for change in changes:
                lines.append(f"- {change}")
            lines.append("")

        if testing:
            lines.append("## Testing")
            for test in testing:
                lines.append(f"- {test}")
            lines.append("")

        if notes:
            lines.append("## Notes")
            for note in notes:
                lines.append(f"- {note}")
            lines.append("")

        return "\n".join(lines)

    def generate_pr_markdown(
        self,
        source_branch: str,
        target_branch: str = "main",
        title: Optional[str] = None,
        description: Optional[str] = None,
        changes: List[str] = None
    ) -> str:
        """
        生成 PR Markdown 文件

        Returns:
            PR Markdown 内容
        """
        repo_info = self.get_repo_info()

        pr_title = title or f"feat: changes from {source_branch}"

        lines = [
            f"# Pull Request: {pr_title}",
            "",
            f"**From:** `{source_branch}`",
            f"**To:** `{target_branch}`",
            f"**Repository:** {repo_info.get('owner', 'owner')}/{repo_info.get('repo', 'repo')}",
            "",
            "---",
            ""
        ]

        if description:
            lines.append(description)
            lines.append("")
            lines.append("---")
            lines.append("")

        if changes:
            lines.append("## Changes")
            for change in changes:
                lines.append(f"- {change}")
            lines.append("")

        lines.append("## Checklist")
        lines.append("- [ ] Tests added/updated")
        lines.append("- [ ] Documentation updated")
        lines.append("- [ ] Code follows project style")

        return "\n".join(lines)

    def save_pr_draft(self, output_path: str = "PR.md", **kwargs):
        """
        保存 PR 草稿

        Args:
            output_path: 输出文件路径
            **kwargs: 传递给 generate_pr_markdown 的参数
        """
        content = self.generate_pr_markdown(**kwargs)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    def get_git_diff(self, from_branch: str, to_branch: str) -> str:
        """
        获取分支差异

        Returns:
            差异内容
        """
        returncode, stdout, stderr = self._run_git([
            "diff", f"{from_branch}...{to_branch}"
        ])

        if returncode == 0:
            return stdout
        return stderr


def create_pr_draft(
    module_name: str,
    source_branch: str,
    output_path: str = "PR.md"
) -> str:
    """
    创建 PR 草稿

    Args:
        module_name: 模块名称
        source_branch: 源分支
        output_path: 输出路径

    Returns:
        输出文件路径
    """
    builder = PRBuilder()

    pr_content = builder.generate_pr_markdown(
        source_branch=source_branch,
        title=f"feat({module_name}): add {module_name} module"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(pr_content)

    return output_path
