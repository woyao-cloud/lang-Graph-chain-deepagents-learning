"""VCS operations for MyAgent."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from myagent.models import VCSCommit

if TYPE_CHECKING:
    pass


class GitRunner:
    """Executes git commands."""

    def run(self, *args: str, cwd: Path | None = None) -> tuple[int, str, str]:
        """Run git command.

        Args:
            *args: Git command arguments
            cwd: Working directory

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                ["git", *args],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)

    def is_repo(self, path: Path) -> bool:
        """Check if path is a git repository.

        Args:
            path: Path to check

        Returns:
            True if git repo
        """
        code, _, _ = self.run("rev-parse", "--git-dir", cwd=path)
        return code == 0


class BranchManager:
    """Manages git branches."""

    def __init__(self):
        """Initialize branch manager."""
        self.git = GitRunner()

    def create_feature_branch(
        self,
        module_name: str,
        base_branch: str = "main",
        cwd: Path | None = None,
    ) -> str:
        """Create feature branch.

        Args:
            module_name: Module name for branch
            base_branch: Base branch to branch from
            cwd: Working directory

        Returns:
            Branch name
        """
        # Sanitize module name
        branch_name = f"feat/agent-{module_name.lower().replace(' ', '-')}"

        # Check if branch already exists
        code, stdout, _ = self.git.run("rev-parse", "--verify", branch_name, cwd=cwd)
        if code == 0:
            return branch_name

        # Create and checkout
        self.git.run("checkout", "-b", branch_name, cwd=cwd)

        return branch_name

    def get_current_branch(self, cwd: Path | None = None) -> str:
        """Get current branch name.

        Args:
            cwd: Working directory

        Returns:
            Branch name
        """
        code, stdout, _ = self.git.run("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
        return stdout.strip() if code == 0 else ""


class CommitGenerator:
    """Generates commit messages."""

    def generate(self, task_name: str, changes: list[str]) -> str:
        """Generate commit message.

        Args:
            task_name: Name of completed task
            changes: List of changes

        Returns:
            Commit message
        """
        lines = [
            f"feat: {task_name}",
            "",
            f"Task: {task_name}",
            "",
            "Changes:",
        ]

        for change in changes:
            lines.append(f"- {change}")

        return "\n".join(lines)

    def commit(
        self,
        message: str,
        cwd: Path | None = None,
    ) -> tuple[bool, str]:
        """Create git commit.

        Args:
            message: Commit message
            cwd: Working directory

        Returns:
            Tuple of (success, output)
        """
        # Stage all changes
        code, _, _ = self.git.run("add", "-A", cwd=cwd)
        if code != 0:
            return False, "Failed to stage changes"

        # Create commit
        code, stdout, stderr = self.git.run("commit", "-m", message, cwd=cwd)
        if code != 0:
            return False, stderr

        return True, stdout


class VCSManager:
    """Manages version control operations."""

    def __init__(self):
        """Initialize VCS manager."""
        self.git = GitRunner()
        self.branch_manager = BranchManager()
        self.commit_generator = CommitGenerator()

    def auto_commit(
        self,
        module_name: str,
        changes: list[str],
        cwd: Path | None = None,
    ) -> tuple[bool, str]:
        """Automatically commit changes.

        Args:
            module_name: Module name
            changes: List of changes
            cwd: Working directory

        Returns:
            Tuple of (success, message)
        """
        if not self.git.is_repo(cwd):
            return False, "Not a git repository"

        # Create feature branch
        branch = self.branch_manager.create_feature_branch(module_name, cwd=cwd)

        # Generate and create commit
        message = self.commit_generator.generate(module_name, changes)
        success, output = self.commit_generator.commit(message, cwd=cwd)

        if success:
            return True, f"Committed to {branch}: {message[:50]}..."
        return False, output

    def push_branch(self, branch: str, cwd: Path | None = None) -> tuple[bool, str]:
        """Push branch to remote.

        Args:
            branch: Branch name
            cwd: Working directory

        Returns:
            Tuple of (success, output)
        """
        code, stdout, stderr = self.git.run("push", "-u", "origin", branch, cwd=cwd)
        if code != 0:
            return False, stderr
        return True, stdout
