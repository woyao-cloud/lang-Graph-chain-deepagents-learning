"""
Quality Reporter - 质量报告生成
FR-QA-001: 质量门禁
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

from deepagents.quality.linter import LintResult
from deepagents.quality.test_runner import TestResult


@dataclass
class QualityReport:
    """质量报告"""
    timestamp: str
    project_path: str
    overall_passed: bool
    lint_results: List[Dict]
    test_results: List[Dict]
    blockers: List[str]
    recommendations: List[str]


class QualityReporter:
    """
    质量报告生成器
    汇总 Lint 和 Test 结果，生成统一报告
    """

    def __init__(self, project_path: str = "."):
        self.project_path = project_path
        self.lint_results: List[LintResult] = []
        self.test_results: List[TestResult] = []
        self.report: QualityReport = None

    def add_lint_result(self, result: LintResult):
        """添加 Lint 结果"""
        self.lint_results.append(result)

    def add_test_result(self, result: TestResult):
        """添加测试结果"""
        self.test_results.append(result)

    def generate_report(self) -> QualityReport:
        """生成质量报告"""
        # 汇总结果
        lint_passed = all(r.passed for r in self.lint_results)
        test_passed = all(r.passed for r in self.test_results)
        overall_passed = lint_passed and test_passed

        # 识别阻塞项
        blockers = []
        for result in self.lint_results:
            if not result.passed:
                blockers.append(f"Lint failed ({result.tool}): {result.error_count} errors")
        for result in self.test_results:
            if not result.passed:
                blockers.append(f"Test failed ({result.framework}): {result.tests_failed} failures")

        # 生成建议
        recommendations = []
        if not lint_passed:
            recommendations.append("Fix lint errors before proceeding")
        if not test_passed:
            recommendations.append("Ensure all tests pass before proceeding")
        if not self.lint_results:
            recommendations.append("Consider adding lint checks")
        if not self.test_results:
            recommendations.append("Consider adding unit tests")

        self.report = QualityReport(
            timestamp=datetime.now().isoformat(),
            project_path=self.project_path,
            overall_passed=overall_passed,
            lint_results=[self._lint_to_dict(r) for r in self.lint_results],
            test_results=[self._test_to_dict(r) for r in self.test_results],
            blockers=blockers,
            recommendations=recommendations
        )

        return self.report

    def save_report(self, format: str = "md"):
        """保存报告"""
        if not self.report:
            self.generate_report()

        os.makedirs("LOGS/quality", exist_ok=True)

        if format == "json":
            report_file = os.path.join("LOGS/quality", "quality_report.json")
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.report), f, ensure_ascii=False, indent=2)

        elif format == "md":
            report_file = os.path.join("LOGS/quality", "quality_report.md")
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(self._generate_markdown())

        return report_file

    def _lint_to_dict(self, result: LintResult) -> Dict:
        return {
            "tool": result.tool,
            "passed": result.passed,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "output_preview": result.output[:500] if result.output else ""
        }

    def _test_to_dict(self, result: TestResult) -> Dict:
        return {
            "framework": result.framework,
            "passed": result.passed,
            "tests_run": result.tests_run,
            "tests_passed": result.tests_passed,
            "tests_failed": result.tests_failed,
            "duration": result.duration,
            "coverage": result.coverage
        }

    def _generate_markdown(self) -> str:
        """生成 Markdown 格式报告"""
        if not self.report:
            return ""

        lines = [
            "# Quality Report",
            "",
            f"**Timestamp:** {self.report.timestamp}",
            f"**Project:** {self.report.project_path}",
            f"**Status:** {'PASSED' if self.report.overall_passed else 'FAILED'}",
            "",
            "---",
            "",
            "## Summary",
            "",
        ]

        # Lint 汇总
        total_lint_errors = sum(r.error_count for r in self.lint_results)
        total_lint_warnings = sum(r.warning_count for r in self.lint_results)
        lines.append(f"- **Lint:** {total_lint_errors} errors, {total_lint_warnings} warnings")

        # Test 汇总
        total_test_run = sum(r.tests_run for r in self.test_results)
        total_test_passed = sum(r.tests_passed for r in self.test_results)
        lines.append(f"- **Tests:** {total_test_passed}/{total_test_run} passed")

        if self.report.blockers:
            lines.append("")
            lines.append("## Blockers")
            for blocker in self.report.blockers:
                lines.append(f"- {blocker}")

        if self.report.recommendations:
            lines.append("")
            lines.append("## Recommendations")
            for rec in self.report.recommendations:
                lines.append(f"- {rec}")

        lines.append("")
        lines.append("---")
        lines.append("*Generated by DeepAgents*")

        return "\n".join(lines)

    def check_quality_gate(self) -> tuple[bool, str]:
        """
        检查质量门禁

        Returns:
            (passed, message)
        """
        if not self.report:
            self.generate_report()

        if self.report.overall_passed:
            return True, "All quality checks passed"

        blocker_count = len(self.report.blockers)
        return False, f"Quality gate failed with {blocker_count} blocker(s)"
