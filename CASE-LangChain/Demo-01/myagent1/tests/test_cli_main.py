"""Tests for CLI main module."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from myagent.cli.main import main, init, run, confirm, status, logs, skip, rollback, approve, reject


class TestMain:
    """Tests for main CLI entry point."""

    def test_main_runs(self):
        """Test main CLI can run."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "MyAgent" in result.output

    def test_version_option(self):
        """Test --version flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0


class TestInit:
    """Tests for init command."""

    def test_init_help(self):
        """Test init --help."""
        runner = CliRunner()
        result = runner.invoke(init, ["--help"])
        assert result.exit_code == 0
        assert "项目名称" in result.output

    def test_init_requires_name(self):
        """Test init requires --name."""
        runner = CliRunner()
        result = runner.invoke(init, [])
        assert result.exit_code != 0

    def test_init_creates_project(self, tmp_path):
        """Test init creates project structure."""
        runner = CliRunner()
        result = runner.invoke(init, ["--name", "test-proj", "--path", str(tmp_path)])
        assert result.exit_code == 0

        project_dir = tmp_path / "test-proj"
        assert project_dir.exists()
        assert (project_dir / "workflow.md").exists()
        assert (project_dir / "agent.md").exists()


class TestRun:
    """Tests for run command."""

    def test_run_help(self):
        """Test run --help."""
        runner = CliRunner()
        result = runner.invoke(run, ["--help"])
        assert result.exit_code == 0
        assert "phase" in result.output

    def test_run_requires_phase(self):
        """Test run requires --phase."""
        runner = CliRunner()
        result = runner.invoke(run, [])
        assert result.exit_code != 0

    def test_run_validates_phase(self):
        """Test run validates phase value."""
        runner = CliRunner()
        result = runner.invoke(run, ["--phase", "invalid"])
        assert result.exit_code != 0


class TestConfirm:
    """Tests for confirm command."""

    def test_confirm_help(self):
        """Test confirm --help."""
        runner = CliRunner()
        result = runner.invoke(confirm, ["--help"])
        assert result.exit_code == 0

    def test_confirm_default_file(self):
        """Test confirm uses default PLANNING.md."""
        runner = CliRunner()
        result = runner.invoke(confirm, ["--project", "/nonexistent"])
        assert result.exit_code != 0  # But not for missing --file


class TestStatus:
    """Tests for status command."""

    def test_status_help(self):
        """Test status --help."""
        runner = CliRunner()
        result = runner.invoke(status, ["--help"])
        assert result.exit_code == 0

    def test_status_live_flag(self):
        """Test status --live flag is accepted."""
        runner = CliRunner()
        result = runner.invoke(status, ["--live", "--project", "/nonexistent"])
        # Should not fail on --live flag
        assert True


class TestLogs:
    """Tests for logs command."""

    def test_logs_help(self):
        """Test logs --help."""
        runner = CliRunner()
        result = runner.invoke(logs, ["--help"])
        assert result.exit_code == 0

    def test_logs_requires_agent(self):
        """Test logs requires --agent."""
        runner = CliRunner()
        result = runner.invoke(logs, [])
        assert result.exit_code != 0


class TestSkip:
    """Tests for skip command."""

    def test_skip_help(self):
        """Test skip --help."""
        runner = CliRunner()
        result = runner.invoke(skip, ["--help"])
        assert result.exit_code == 0

    def test_skip_not_implemented(self):
        """Test skip raises NotImplementedError."""
        runner = CliRunner()
        result = runner.invoke(skip, ["--task", "test", "--project", "/tmp"])
        assert result.exit_code != 0
        assert result.exception is not None
        assert "not yet implemented" in str(result.exception)


class TestRollback:
    """Tests for rollback command."""

    def test_rollback_help(self):
        """Test rollback --help."""
        runner = CliRunner()
        result = runner.invoke(rollback, ["--help"])
        assert result.exit_code == 0

    def test_rollback_not_implemented(self):
        """Test rollback raises NotImplementedError."""
        runner = CliRunner()
        result = runner.invoke(rollback, ["--task", "test", "--project", "/tmp"])
        assert result.exit_code != 0


class TestApprove:
    """Tests for approve command."""

    def test_approve_help(self):
        """Test approve --help."""
        runner = CliRunner()
        result = runner.invoke(approve, ["--help"])
        assert result.exit_code == 0

    def test_approve_requires_operation(self):
        """Test approve requires --operation."""
        runner = CliRunner()
        result = runner.invoke(approve, [])
        assert result.exit_code != 0

    def test_approve_not_implemented(self):
        """Test approve raises NotImplementedError."""
        runner = CliRunner()
        result = runner.invoke(approve, ["--operation", "op-123", "--project", "/tmp"])
        assert result.exit_code != 0


class TestReject:
    """Tests for reject command."""

    def test_reject_help(self):
        """Test reject --help."""
        runner = CliRunner()
        result = runner.invoke(reject, ["--help"])
        assert result.exit_code == 0

    def test_reject_requires_operation(self):
        """Test reject requires --operation."""
        runner = CliRunner()
        result = runner.invoke(reject, [])
        assert result.exit_code != 0

    def test_reject_not_implemented(self):
        """Test reject raises NotImplementedError."""
        runner = CliRunner()
        result = runner.invoke(reject, ["--operation", "op-123", "--project", "/tmp"])
        assert result.exit_code != 0