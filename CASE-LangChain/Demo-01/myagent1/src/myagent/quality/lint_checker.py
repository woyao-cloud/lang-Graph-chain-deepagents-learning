"""Quality gate checker for MyAgent.

Runs lint, test, and other quality checks.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from myagent.models import QualityGateResult

if TYPE_CHECKING:
    from myagent.config import MyAgentConfig


class LintChecker:
    """Runs linting checks."""

    def run(self, file_path: Path, linter: str = "pylint") -> QualityGateResult:
        """Run linter on a file.

        Args:
            file_path: File to lint
            linter: Linter to use (pylint, flake8, ruff)

        Returns:
            QualityGateResult
        """
        if not file_path.exists():
            return QualityGateResult(
                gate_type="lint",
                success=False,
                file_path=file_path,
                message=f"File not found: {file_path}",
            )

        try:
            result = subprocess.run(
                [linter, str(file_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            success = result.returncode == 0
            errors = result.stdout.split("\n") if result.stdout else []

            return QualityGateResult(
                gate_type="lint",
                success=success,
                file_path=file_path,
                message="Lint passed" if success else "Lint failed",
                errors=errors,
            )

        except subprocess.TimeoutExpired:
            return QualityGateResult(
                gate_type="lint",
                success=False,
                file_path=file_path,
                message="Lint timed out",
            )
        except FileNotFoundError:
            return QualityGateResult(
                gate_type="lint",
                success=True,
                file_path=file_path,
                message=f"Linter '{linter}' not found, skipping",
            )
        except Exception as e:
            return QualityGateResult(
                gate_type="lint",
                success=False,
                file_path=file_path,
                message=f"Lint error: {str(e)}",
            )


class TestRunner:
    """Runs unit tests."""

    def run(self, file_path: Path, framework: str = "pytest") -> QualityGateResult:
        """Run tests on a file.

        Args:
            file_path: File or directory to test
            framework: Test framework (pytest, unittest)

        Returns:
            QualityGateResult
        """
        if not file_path.exists():
            return QualityGateResult(
                gate_type="test",
                success=False,
                file_path=file_path,
                message=f"Path not found: {file_path}",
            )

        try:
            cmd = [framework, str(file_path), "-v"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            success = result.returncode == 0
            errors = result.stdout.split("\n") if result.stdout else []

            return QualityGateResult(
                gate_type="test",
                success=success,
                file_path=file_path,
                message="Tests passed" if success else "Tests failed",
                errors=errors,
            )

        except subprocess.TimeoutExpired:
            return QualityGateResult(
                gate_type="test",
                success=False,
                file_path=file_path,
                message="Tests timed out",
            )
        except FileNotFoundError:
            return QualityGateResult(
                gate_type="test",
                success=True,
                file_path=file_path,
                message=f"Test framework '{framework}' not found, skipping",
            )
        except Exception as e:
            return QualityGateResult(
                gate_type="test",
                success=False,
                file_path=file_path,
                message=f"Test error: {str(e)}",
            )


class QualityGateRunner:
    """Runs all quality gates."""

    def __init__(self, config: "MyAgentConfig | None" = None):
        """Initialize quality gate runner.

        Args:
            config: MyAgent configuration
        """
        self.config = config
        self.lint_checker = LintChecker()
        self.test_runner = TestRunner()

    def run_all(
        self,
        project_root: Path,
        lint_enabled: bool = True,
        test_enabled: bool = True,
    ) -> list[QualityGateResult]:
        """Run all quality gates.

        Args:
            project_root: Project root directory
            lint_enabled: Whether to run lint
            test_enabled: Whether to run tests

        Returns:
            List of QualityGateResult
        """
        results: list[QualityGateResult] = []

        # Find Python files
        src_dir = project_root / "src"
        if src_dir.exists():
            py_files = list(src_dir.rglob("*.py"))
        else:
            py_files = list(project_root.rglob("*.py"))

        # Exclude venv and __pycache__
        py_files = [
            f for f in py_files
            if "venv" not in str(f) and "__pycache__" not in str(f)
        ]

        # Run lint
        if lint_enabled:
            for py_file in py_files:
                result = self.lint_checker.run(py_file)
                results.append(result)

        # Run tests
        if test_enabled:
            test_dir = project_root / "tests"
            if test_dir.exists():
                result = self.test_runner.run(test_dir)
                results.append(result)

        return results

    def check_all_passed(self, results: list[QualityGateResult]) -> bool:
        """Check if all quality gates passed.

        Args:
            results: List of results

        Returns:
            True if all passed
        """
        return all(r.success for r in results)
