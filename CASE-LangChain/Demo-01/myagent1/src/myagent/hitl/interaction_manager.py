"""Human-in-the-loop confirmation gate for MyAgent.

Manages pause points for human confirmation before proceeding.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myagent.models import PlanningDocument


class ConfirmationGate:
    """Manages confirmation gates for human approval."""

    def __init__(self):
        """Initialize confirmation gate."""
        self._pending_confirmations: dict[str, str] = {}
        self._confirmed: set[str] = set()
        self._rejected: set[str] = set()

    def request_confirmation(
        self,
        document: "PlanningDocument",
        reason: str = "Please review and confirm the planning document",
    ) -> str:
        """Request confirmation for a planning document.

        Args:
            document: PlanningDocument to confirm
            reason: Reason for confirmation request

        Returns:
            Confirmation ID
        """
        confirmation_id = f"confirm_{document.path.stem}_{len(self._pending_confirmations)}"
        self._pending_confirmations[confirmation_id] = reason
        return confirmation_id

    def is_pending(self, confirmation_id: str) -> bool:
        """Check if confirmation is pending.

        Args:
            confirmation_id: Confirmation ID

        Returns:
            True if pending
        """
        return confirmation_id in self._pending_confirmations

    def is_confirmed(self, confirmation_id: str) -> bool:
        """Check if confirmation was approved.

        Args:
            confirmation_id: Confirmation ID

        Returns:
            True if confirmed
        """
        return confirmation_id in self._confirmed

    def is_rejected(self, confirmation_id: str) -> bool:
        """Check if confirmation was rejected.

        Args:
            confirmation_id: Confirmation ID

        Returns:
            True if rejected
        """
        return confirmation_id in self._rejected

    def approve(self, confirmation_id: str) -> bool:
        """Approve a pending confirmation.

        Args:
            confirmation_id: Confirmation ID

        Returns:
            True if approved
        """
        if confirmation_id in self._pending_confirmations:
            self._confirmed.add(confirmation_id)
            self._pending_confirmations.pop(confirmation_id, None)
            return True
        return False

    def reject(self, confirmation_id: str) -> bool:
        """Reject a pending confirmation.

        Args:
            confirmation_id: Confirmation ID

        Returns:
            True if rejected
        """
        if confirmation_id in self._pending_confirmations:
            self._rejected.add(confirmation_id)
            self._pending_confirmations.pop(confirmation_id, None)
            return True
        return False

    def wait_for_confirmation(
        self,
        document_path: Path,
        timeout_seconds: float | None = None,
    ) -> bool:
        """Wait for human confirmation on a document.

        This is a blocking call that waits for user to confirm.

        Args:
            document_path: Path to planning document
            timeout_seconds: Optional timeout

        Returns:
            True if confirmed, False if rejected or timeout
        """
        # Check if already confirmed in file
        if self._is_document_confirmed(document_path):
            return True

        # In real implementation, this would use a proper async waiting mechanism
        # For now, we just check the file
        return self._is_document_confirmed(document_path)

    def _is_document_confirmed(self, path: Path) -> bool:
        """Check if document has been confirmed.

        Args:
            path: Document path

        Returns:
            True if confirmed
        """
        if not path.exists():
            return False

        content = path.read_text(encoding="utf-8", errors="ignore")

        # Check for confirmation markers
        patterns = [
            r"\- \[x\]\s*已阅读并确认",
            r"\- \[X\]\s*已阅读并确认",
            r"confirmed:\s*true",
            r"status:\s*approved",
        ]

        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False


class DangerousOpGuard:
    """Guards against dangerous operations requiring human approval."""

    # Default dangerous patterns
    DEFAULT_DANGEROUS_PATTERNS = [
        (r"rm\s+-rf", "rm -rf 删除目录"),
        (r"rm\s+-r", "rm -r 删除目录"),
        (r"git\s+push\s+--force", "强制推送 git"),
        (r"sudo\s+", "sudo 提权命令"),
        (r"chmod\s+777", "777 权限设置"),
        (r"drop\s+database", "删除数据库"),
        (r"delete\s+--force", "强制删除"),
        (r">\s*/dev/sd", "直接写入设备"),
    ]

    def __init__(self, custom_patterns: list[tuple[str, str]] | None = None):
        """Initialize dangerous operation guard.

        Args:
            custom_patterns: Custom dangerous patterns [(regex, description)]
        """
        patterns = custom_patterns or self.DEFAULT_DANGEROUS_PATTERNS
        self._patterns = [(re.compile(p, re.IGNORECASE), desc) for p, desc in patterns]
        self._pending_approvals: dict[str, str] = {}
        self._approved: set[str] = set()
        self._rejected: set[str] = set()

    def is_dangerous(self, operation: str) -> bool:
        """Check if operation is dangerous.

        Args:
            operation: Operation string

        Returns:
            True if dangerous
        """
        for pattern, _ in self._patterns:
            if pattern.search(operation):
                return True
        return False

    def get_danger_description(self, operation: str) -> str | None:
        """Get description of why operation is dangerous.

        Args:
            operation: Operation string

        Returns:
            Description or None if not dangerous
        """
        for pattern, desc in self._patterns:
            if pattern.search(operation):
                return desc
        return None

    def request_approval(self, operation: str, operation_id: str | None = None) -> str:
        """Request approval for dangerous operation.

        Args:
            operation: Operation string
            operation_id: Optional operation ID

        Returns:
            Approval ID
        """
        if not operation_id:
            operation_id = f"op_{len(self._pending_approvals)}"

        desc = self.get_danger_description(operation)
        self._pending_approvals[operation_id] = f"{operation} ({desc})"

        return operation_id

    def approve(self, operation_id: str) -> bool:
        """Approve dangerous operation.

        Args:
            operation_id: Operation ID

        Returns:
            True if approved
        """
        if operation_id in self._pending_approvals:
            self._approved.add(operation_id)
            self._pending_approvals.pop(operation_id, None)
            return True
        return False

    def reject(self, operation_id: str) -> bool:
        """Reject dangerous operation.

        Args:
            operation_id: Operation ID

        Returns:
            True if rejected
        """
        if operation_id in self._pending_approvals:
            self._rejected.add(operation_id)
            self._pending_approvals.pop(operation_id, None)
            return True
        return False

    def is_approved(self, operation_id: str) -> bool:
        """Check if operation was approved.

        Args:
            operation_id: Operation ID

        Returns:
            True if approved
        """
        return operation_id in self._approved

    def is_rejected(self, operation_id: str) -> bool:
        """Check if operation was rejected.

        Args:
            operation_id: Operation ID

        Returns:
            True if rejected
        """
        return operation_id in self._rejected

    def get_pending(self) -> dict[str, str]:
        """Get pending approvals.

        Returns:
            Dict of operation_id -> operation description
        """
        return self._pending_approvals.copy()
