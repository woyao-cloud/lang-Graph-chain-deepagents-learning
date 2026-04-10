"""Tests for quality gate modules."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from myagent.quality.lint_checker import (
    LintChecker,
    TestRunner,
    QualityGateRunner,
)
from myagent.models import QualityGateResult


class TestLintChecker:
    """Tests for LintChecker."""

    def test_init_default_values(self):
        """Test LintChecker initialization."""
        checker = LintChecker()
        assert checker is not None

    def test_run_file_not_found(self):
        """Test run method with missing file."""
        checker = LintChecker()
        result = checker.run(Path("/nonexistent/file.py"))

        assert result.success is False
        assert "not found" in result.message.lower()

    def test_run_file_exists_pylint(self, tmp_path):
        """Test run with existing Python file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo():\n    pass\n")

        checker = LintChecker()

        # Mock subprocess.run to avoid actual lint execution
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )
            result = checker.run(test_file)

        assert result.gate_type == "lint"
        assert result.file_path == test_file

    def test_run_with_flake8(self, tmp_path):
        """Test run with flake8 linter."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo():\n    pass\n")

        checker = LintChecker()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )
            result = checker.run(test_file, linter="flake8")

        assert result.gate_type == "lint"


class TestTestRunner:
    """Tests for TestRunner."""

    def test_init_default_values(self):
        """Test TestRunner initialization."""
        runner = TestRunner()
        assert runner is not None

    def test_run_path_not_found(self):
        """Test run method with missing path."""
        runner = TestRunner()
        result = runner.run(Path("/nonexistent/path"))

        assert result.success is False
        assert "not found" in result.message.lower()

    def test_run_file_exists_pytest(self, tmp_path):
        """Test run with existing file."""
        test_file = tmp_path / "test_test.py"
        test_file.write_text("def test_foo():\n    pass\n")

        runner = TestRunner()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )
            result = runner.run(test_file)

        assert result.gate_type == "test"
        assert result.file_path == test_file

    def test_run_with_unittest(self, tmp_path):
        """Test run with unittest framework."""
        test_file = tmp_path / "test_test.py"
        test_file.write_text("import unittest\n\nclass Test(unittest.TestCase):\n    pass\n")

        runner = TestRunner()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )
            result = runner.run(test_file, framework="unittest")

        assert result.gate_type == "test"


class TestQualityGateRunner:
    """Tests for QualityGateRunner."""

    def test_init_default_values(self):
        """Test QualityGateRunner initialization."""
        runner = QualityGateRunner()
        assert runner.lint_checker is not None
        assert runner.test_runner is not None

    def test_init_with_config(self):
        """Test QualityGateRunner with config."""
        runner = QualityGateRunner(config=None)
        assert runner.config is None

    def test_run_all_no_files(self, tmp_path):
        """Test run_all with empty directory."""
        runner = QualityGateRunner()

        with patch.object(runner.lint_checker, 'run') as mock_lint:
            with patch.object(runner.test_runner, 'run') as mock_test:
                mock_lint.return_value = QualityGateResult(
                    gate_type="lint",
                    success=True,
                    file_path=Path("."),
                    message="No files",
                )
                mock_test.return_value = QualityGateResult(
                    gate_type="test",
                    success=True,
                    file_path=Path("."),
                    message="No files",
                )

                results = runner.run_all(tmp_path)

        assert len(results) >= 0

    def test_run_all_disabled_gates(self, tmp_path):
        """Test run_all with disabled gates."""
        runner = QualityGateRunner()
        results = runner.run_all(tmp_path, lint_enabled=False, test_enabled=False)
        assert results == []

    def test_run_all_with_lint_enabled(self, tmp_path):
        """Test run_all with lint enabled."""
        runner = QualityGateRunner()

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo():\n    pass\n")

        with patch.object(runner.lint_checker, 'run') as mock_lint:
            mock_lint.return_value = QualityGateResult(
                gate_type="lint",
                success=True,
                file_path=test_file,
                message="OK",
            )
            results = runner.run_all(tmp_path, lint_enabled=True, test_enabled=False)

        assert len(results) > 0
        assert any(r.gate_type == "lint" for r in results)

    def test_run_all_with_test_enabled(self, tmp_path):
        """Test run_all with test enabled."""
        runner = QualityGateRunner()

        # Create test directory with test file
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_foo.py"
        test_file.write_text("def test_foo():\n    pass\n")

        with patch.object(runner.test_runner, 'run') as mock_test:
            mock_test.return_value = QualityGateResult(
                gate_type="test",
                success=True,
                file_path=test_file,
                message="OK",
            )
            results = runner.run_all(tmp_path, lint_enabled=False, test_enabled=True)

        assert len(results) > 0
        assert any(r.gate_type == "test" for r in results)

    def test_check_all_passed_true(self):
        """Test check_all_passed returns True when all pass."""
        runner = QualityGateRunner()
        results = [
            QualityGateResult(gate_type="lint", success=True, file_path=Path("test.py")),
            QualityGateResult(gate_type="test", success=True, file_path=Path("test.py")),
        ]
        assert runner.check_all_passed(results) is True

    def test_check_all_passed_false(self):
        """Test check_all_passed returns False when any fails."""
        runner = QualityGateRunner()
        results = [
            QualityGateResult(gate_type="lint", success=True, file_path=Path("test.py")),
            QualityGateResult(gate_type="test", success=False, file_path=Path("test.py")),
        ]
        assert runner.check_all_passed(results) is False

    def test_check_all_passed_empty(self):
        """Test check_all_passed returns True for empty results."""
        runner = QualityGateRunner()
        assert runner.check_all_passed([]) is True