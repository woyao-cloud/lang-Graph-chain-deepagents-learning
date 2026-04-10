"""
Linter - 代码风格检查
FR-QA-001.1: Lint 检查
"""

import subprocess
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LintResult:
    """Lint 检查结果"""
    passed: bool
    tool: str
    output: str
    error_count: int = 0
    warning_count: int = 0
    file_count: int = 0


class Linter:
    """
    代码 Lint 检查器
    支持多种语言的 Linter
    """

    # Linter 配置
    LINTERS = {
        "python": {
            "ruff": ["ruff", "check", "."],
            "pylint": ["pylint", "."],
            "flake8": ["flake8", "."],
            "black": ["black", "--check", "."],
        },
        "javascript": {
            "eslint": ["npx", "eslint", "."],
        },
        "typescript": {
            "eslint": ["npx", "eslint", "."],
            "tslint": ["npx", "tslint", "-c", "tslint.json", "**/*.ts"],
        },
    }

    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.results: List[LintResult] = []

    def detect_language(self) -> List[str]:
        """检测项目语言"""
        languages = []
        if os.path.exists(os.path.join(self.project_root, "package.json")):
            languages.append("javascript")
        if os.path.exists(os.path.join(self.project_root, "requirements.txt")):
            languages.append("python")
        if os.path.exists(os.path.join(self.project_root, "pyproject.toml")):
            languages.append("python")
        if os.path.exists(os.path.join(self.project_root, "go.mod")):
            languages.append("go")
        return languages

    def run_lint(
        self,
        language: str,
        tool: Optional[str] = None
    ) -> List[LintResult]:
        """
        运行 Lint 检查

        Args:
            language: 编程语言
            tool: 指定工具（可选）

        Returns:
            Lint 结果列表
        """
        results = []

        if language not in self.LINTERS:
            return [LintResult(
                passed=False,
                tool="unknown",
                output=f"No linters configured for {language}"
            )]

        linters = self.LINTERS[language]

        if tool:
            if tool not in linters:
                return [LintResult(
                    passed=False,
                    tool=tool,
                    output=f"Unknown linter: {tool}"
                )]
            linters = {tool: linters[tool]}

        for tool_name, cmd in linters.items():
            result = self._run_command(cmd, tool_name)
            results.append(result)

        self.results.extend(results)
        return results

    def _run_command(self, cmd: List[str], tool_name: str) -> LintResult:
        """执行 Lint 命令"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300
            )

            output = result.stdout + result.stderr

            # 解析输出
            error_count = output.count("error")
            warning_count = output.count("warning")

            # 判断是否通过
            passed = result.returncode == 0

            return LintResult(
                passed=passed,
                tool=tool_name,
                output=output,
                error_count=error_count,
                warning_count=warning_count
            )

        except subprocess.TimeoutExpired:
            return LintResult(
                passed=False,
                tool=tool_name,
                output="Lint check timed out (5 minutes limit)"
            )
        except FileNotFoundError:
            return LintResult(
                passed=False,
                tool=tool_name,
                output=f"Linter not found: {cmd[0]}"
            )
        except Exception as e:
            return LintResult(
                passed=False,
                tool=tool_name,
                output=f"Error running linter: {str(e)}"
            )

    def check_all(self) -> List[LintResult]:
        """检查所有语言"""
        all_results = []
        for lang in self.detect_language():
            all_results.extend(self.run_lint(lang))
        return all_results

    def generate_report(self) -> str:
        """生成 Lint 报告"""
        if not self.results:
            return "No lint results available"

        lines = ["# Lint Report", ""]

        for result in self.results:
            status = "PASSED" if result.passed else "FAILED"
            lines.append(f"## {result.tool}: {status}")
            lines.append(f"- Errors: {result.error_count}")
            lines.append(f"- Warnings: {result.warning_count}")
            if result.output:
                lines.append("")
                lines.append("```")
                lines.append(result.output[:1000])  # 限制输出长度
                lines.append("```")
            lines.append("")

        return "\n".join(lines)


# 便捷函数
def lint_check(language: str = "auto", tool: Optional[str] = None, project_root: str = ".") -> LintResult:
    """
    便捷 Lint 检查函数

    Args:
        language: 编程语言 ("python", "javascript", "auto")
        tool: 指定工具
        project_root: 项目根目录

    Returns:
        合并的 Lint 结果
    """
    if language == "auto":
        linter = Linter(project_root)
        languages = linter.detect_language()
        results = linter.check_all()
    else:
        linter = Linter(project_root)
        results = linter.run_lint(language, tool)

    # 合并结果
    all_passed = all(r.passed for r in results)
    total_errors = sum(r.error_count for r in results)
    total_warnings = sum(r.warning_count for r in results)
    all_output = "\n".join(r.output for r in results if r.output)

    return LintResult(
        passed=all_passed,
        tool="all",
        output=all_output,
        error_count=total_errors,
        warning_count=total_warnings
    )
