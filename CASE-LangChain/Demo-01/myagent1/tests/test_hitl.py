"""Tests for HITL interaction manager."""

from __future__ import annotations

import pytest
from pathlib import Path

from myagent.hitl.interaction_manager import (
    ConfirmationGate,
    DangerousOpGuard,
)


class TestConfirmationGate:
    """Tests for ConfirmationGate."""

    def test_init_default_values(self):
        """Test ConfirmationGate initialization."""
        gate = ConfirmationGate()
        assert gate._pending_confirmations == {}
        assert gate._confirmed == set()
        assert gate._rejected == set()

    def test_request_confirmation(self):
        """Test request_confirmation adds pending confirmation."""
        gate = ConfirmationGate()
        mock_doc = type('obj', (object,), {'path': Path('/planning.md')})()

        confirmation_id = gate.request_confirmation(mock_doc)

        assert confirmation_id is not None
        assert confirmation_id in gate._pending_confirmations

    def test_is_pending(self):
        """Test is_pending returns True for pending confirmations."""
        gate = ConfirmationGate()
        mock_doc = type('obj', (object,), {'path': Path('/planning.md')})()

        confirmation_id = gate.request_confirmation(mock_doc)

        assert gate.is_pending(confirmation_id) is True

    def test_approve(self):
        """Test approve marks as confirmed."""
        gate = ConfirmationGate()
        mock_doc = type('obj', (object,), {'path': Path('/planning.md')})()

        confirmation_id = gate.request_confirmation(mock_doc)
        result = gate.approve(confirmation_id)

        assert result is True
        assert gate.is_confirmed(confirmation_id) is True
        assert gate.is_pending(confirmation_id) is False

    def test_reject(self):
        """Test reject marks as rejected."""
        gate = ConfirmationGate()
        mock_doc = type('obj', (object,), {'path': Path('/planning.md')})()

        confirmation_id = gate.request_confirmation(mock_doc)
        result = gate.reject(confirmation_id)

        assert result is True
        assert gate.is_rejected(confirmation_id) is True
        assert gate.is_pending(confirmation_id) is False

    def test_approve_nonexistent(self):
        """Test approving nonexistent confirmation returns False."""
        gate = ConfirmationGate()
        result = gate.approve("nonexistent-id")
        assert result is False

    def test_reject_nonexistent(self):
        """Test rejecting nonexistent confirmation returns False."""
        gate = ConfirmationGate()
        result = gate.reject("nonexistent-id")
        assert result is False

    def test_is_confirmed_false_for_pending(self):
        """Test is_confirmed returns False for pending confirmation."""
        gate = ConfirmationGate()
        mock_doc = type('obj', (object,), {'path': Path('/planning.md')})()

        confirmation_id = gate.request_confirmation(mock_doc)

        assert gate.is_confirmed(confirmation_id) is False

    def test_is_rejected_false_for_pending(self):
        """Test is_rejected returns False for pending confirmation."""
        gate = ConfirmationGate()
        mock_doc = type('obj', (object,), {'path': Path('/planning.md')})()

        confirmation_id = gate.request_confirmation(mock_doc)

        assert gate.is_rejected(confirmation_id) is False

    def test_wait_for_confirmation_confirmed_file(self, tmp_path):
        """Test wait_for_confirmation with confirmed file."""
        gate = ConfirmationGate()
        planning_file = tmp_path / "PLANNING.md"
        planning_file.write_text("confirmed: true")

        result = gate.wait_for_confirmation(planning_file)
        assert result is True

    def test_wait_for_confirmation_unconfirmed_file(self, tmp_path):
        """Test wait_for_confirmation with unconfirmed file."""
        gate = ConfirmationGate()
        planning_file = tmp_path / "PLANNING.md"
        planning_file.write_text("Unconfirmed content")

        result = gate.wait_for_confirmation(planning_file)
        assert result is False

    def test_wait_for_confirmation_nonexistent_file(self, tmp_path):
        """Test wait_for_confirmation with nonexistent file."""
        gate = ConfirmationGate()
        result = gate.wait_for_confirmation(tmp_path / "nonexistent.md")
        assert result is False


class TestDangerousOpGuard:
    """Tests for DangerousOpGuard."""

    def test_init_default_patterns(self):
        """Test DangerousOpGuard default patterns."""
        guard = DangerousOpGuard()
        assert len(guard._patterns) > 0

    def test_init_custom_patterns(self):
        """Test DangerousOpGuard with custom patterns."""
        patterns = [(r"rm\s+-rf", "dangerous delete"), (r"drop\s+table", "drop table")]
        guard = DangerousOpGuard(custom_patterns=patterns)
        assert len(guard._patterns) == len(patterns)

    def test_is_dangerous_detects_rm_rf(self):
        """Test is_dangerous detects rm -rf."""
        guard = DangerousOpGuard()
        assert guard.is_dangerous("rm -rf /") is True

    def test_is_dangerous_detects_git_force_push(self):
        """Test is_dangerous detects git force push."""
        guard = DangerousOpGuard()
        assert guard.is_dangerous("git push --force origin main") is True

    def test_is_dangerous_allows_safe_command(self):
        """Test is_dangerous allows safe commands."""
        guard = DangerousOpGuard()
        assert guard.is_dangerous("ls -la") is False
        assert guard.is_dangerous("git status") is False

    def test_get_danger_description(self):
        """Test get_danger_description returns description."""
        guard = DangerousOpGuard()
        desc = guard.get_danger_description("rm -rf /tmp")
        assert desc is not None
        assert "rm -rf" in desc.lower() or "删除" in desc

    def test_get_danger_description_safe(self):
        """Test get_danger_description returns None for safe ops."""
        guard = DangerousOpGuard()
        desc = guard.get_danger_description("ls -la")
        assert desc is None

    def test_request_approval(self):
        """Test request_approval adds pending approval."""
        guard = DangerousOpGuard()
        op_id = guard.request_approval("rm -rf /tmp")
        assert op_id is not None
        assert op_id in guard._pending_approvals

    def test_approve(self):
        """Test approve marks operation as approved."""
        guard = DangerousOpGuard()
        op_id = guard.request_approval("rm -rf /tmp")
        result = guard.approve(op_id)

        assert result is True
        assert guard.is_approved(op_id) is True

    def test_reject(self):
        """Test reject marks operation as rejected."""
        guard = DangerousOpGuard()
        op_id = guard.request_approval("rm -rf /tmp")
        result = guard.reject(op_id)

        assert result is True
        assert guard.is_rejected(op_id) is True

    def test_approve_nonexistent(self):
        """Test approving nonexistent operation returns False."""
        guard = DangerousOpGuard()
        result = guard.approve("nonexistent-id")
        assert result is False

    def test_reject_nonexistent(self):
        """Test rejecting nonexistent operation returns False."""
        guard = DangerousOpGuard()
        result = guard.reject("nonexistent-id")
        assert result is False

    def test_get_pending(self):
        """Test get_pending returns pending approvals."""
        guard = DangerousOpGuard()
        guard.request_approval("rm -rf /tmp")
        guard.request_approval("drop database")

        pending = guard.get_pending()
        assert len(pending) == 2

    def test_case_insensitive_patterns(self):
        """Test dangerous patterns are case insensitive."""
        guard = DangerousOpGuard()
        assert guard.is_dangerous("RM -RF /") is True
        assert guard.is_dangerous("Git Push --Force origin") is True