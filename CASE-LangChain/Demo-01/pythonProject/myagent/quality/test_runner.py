"""
Test Runner - 单元测试执行
FR-QA-001.2: 单元测试
"""

import subprocess
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TestResult:
    """测试执行结果"""
    passed: bool
    framework: str
    output: str
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    duration: float = 0.0
    coverage: Optional[float] = None


class TestRunner:
    """
    测试运行器
    支持多种测试框架
    """

    # 测试框架配置
    FRAMEWORKS = {
        "python": {
            "pytest": {
                "run": ["pytest", "-v", "--tb=short"],
                "coverage": ["pytest", "-v", "--cov=.f", "--cov-report=term-missing"],
            },
            "unittest": {
                "run": ["python", "-m", "unittest", "discover", "-v"],
            }
        },
        "javascript": {
            "jest": {
                "run": ["npx", "jest", "--verbose"],
                "coverage": ["npx", "jest", "--coverage"],
            },
            "vitest": {
                "run": ["npx", "vitest", "run"],
                "coverage": ["npx", "vitest", "run", "--coverage"],
            }
        }
    }

    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.results: List[TestResult] = []

    def detect_framework(self) -> List[str]:
        """检测测试框架"""
        frameworks = []

        # Python
        if os.path.exists(os.path.join(self.project_root, "pytest.ini")):
            frameworks.append("pytest")
        if os.path.exists(os.path.join(self.project_root, "tests")):
            frameworks.append("pytest")
        if os.path.exists(os.path.join(self.project_root, "requirements.txt")):
            with open(os.path.join(self.project_root, "requirements.txt")) as f:
                content = f.read()
                if "pytest" in content:
                    frameworks.append("pytest")

        # JavaScript
        if os.path.exists(os.path.join(self.project_root, "package.json")):
            with open(os.path.join(self.project_root, "package.json")) as f:
                content = f.read()
                if "jest" in content:
                    frameworks.append("jest")
                if "vitest" in content:
                    frameworks.append("vitest")

        return list(set(frameworks))  # 去重

    def run_tests(
        self,
        framework: str,
        coverage: bool = False,
        test_path: Optional[str] = None
    ) -> TestResult:
        """
        运行测试

        Args:
            framework: 测试框架
            coverage: 是否生成覆盖率报告
            test_path: 测试路径
        """
        if framework not in self.FRAMEWORKS:
            return TestResult(
                passed=False,
                framework=framework,
                output=f"Unknown framework: {framework}"
            )

        # 构建命令
        config = self.FRAMEWORKS[framework]
        cmd_key = "coverage" if coverage else "run"
        cmd = config.get(cmd_key, config["run"]).copy()

        if test_path:
            cmd.extend(["-t", test_path])

        try:
            import time
            start_time = time.time()

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=600  # 10 分钟超时
            )

            duration = time.time() - start_time

            # 解析输出
            output = result.stdout + result.stderr
            test_result = self._parse_output(framework, output, duration)

            self.results.append(test_result)
            return test_result

        except subprocess.TimeoutExpired:
            return TestResult(
                passed=False,
                framework=framework,
                output="Test timed out (10 minutes limit)"
            )
        except FileNotFoundError:
            return TestResult(
                passed=False,
                framework=framework,
                output=f"Test framework not found: {framework}"
            )
        except Exception as e:
            return TestResult(
                passed=False,
                framework=framework,
                output=f"Error running tests: {str(e)}"
            )

    def _parse_output(self, framework: str, output: str, duration: float) -> TestResult:
        """解析测试输出"""
        tests_run = 0
        tests_passed = 0
        tests_failed = 0
        tests_skipped = 0
        coverage = None

        # pytest 格式解析
        if framework == "pytest":
            # 查找统计信息
            import re

            # 匹配 "5 passed in 1.23s" 格式
            match = re.search(r'(\d+)\s+passed\s+in\s+[\d.]+s', output)
            if match:
                tests_passed = int(match.group(1))
                tests_run = tests_passed

            # 匹配 "1 failed, 2 passed" 格式
            match = re.search(r'(\d+)\s+failed', output)
            if match:
                tests_failed = int(match.group(1))
                tests_run += tests_failed

            # 匹配覆盖率
            match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
            if match:
                coverage = float(match.group(1))

        # jest 格式解析
        elif framework in ["jest", "vitest"]:
            import re

            # 匹配 "Tests: 2 passed, 1 failed, 3 total"
            match = re.search(r'Tests:\s+(\d+)\s+passed', output)
            if match:
                tests_passed = int(match.group(1))
                tests_run = tests_passed

            match = re.search(r'(\d+)\s+failed', output)
            if match:
                tests_failed = int(match.group(1))
                tests_run += tests_failed

        passed = tests_failed == 0 and tests_run > 0

        return TestResult(
            passed=passed,
            framework=framework,
            output=output,
            tests_run=tests_run,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            tests_skipped=tests_skipped,
            duration=duration,
            coverage=coverage
        )

    def run_all(self, coverage: bool = False) -> List[TestResult]:
        """运行所有测试"""
        all_results = []
        for framework in self.detect_framework():
            result = self.run_tests(framework, coverage=coverage)
            all_results.append(result)
        return all_results

    def generate_report(self) -> str:
        """生成测试报告"""
        if not self.results:
            return "No test results available"

        lines = ["# Test Report", ""]

        total_run = sum(r.tests_run for r in self.results)
        total_passed = sum(r.tests_passed for r in self.results)
        total_failed = sum(r.tests_failed for r in self.results)

        lines.append(f"## Summary")
        lines.append(f"- Total: {total_run}")
        lines.append(f"- Passed: {total_passed}")
        lines.append(f"- Failed: {total_failed}")
        lines.append("")

        for result in self.results:
            status = "PASSED" if result.passed else "FAILED"
            lines.append(f"## {result.framework}: {status}")
            lines.append(f"- Tests: {result.tests_passed}/{result.tests_run} passed")
            lines.append(f"- Duration: {result.duration:.2f}s")
            if result.coverage is not None:
                lines.append(f"- Coverage: {result.coverage}%")
            lines.append("")

        return "\n".join(lines)


# 便捷函数
def run_tests(
    framework: str = "auto",
    coverage: bool = True,
    project_root: str = "."
) -> TestResult:
    """
    便捷测试执行函数

    Args:
        framework: 测试框架 ("pytest", "jest", "auto")
        coverage: 是否生成覆盖率
        project_root: 项目根目录

    Returns:
        测试结果
    """
    runner = TestRunner(project_root)

    if framework == "auto":
        frameworks = runner.detect_framework()
        if not frameworks:
            return TestResult(
                passed=False,
                framework="unknown",
                output="No test framework detected"
            )
        # 运行第一个检测到的框架
        return runner.run_tests(frameworks[0], coverage=coverage)
    else:
        return runner.run_tests(framework, coverage=coverage)
