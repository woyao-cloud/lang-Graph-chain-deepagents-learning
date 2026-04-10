"""Tests for progress tracker module."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from myagent.progress.tracker import ProgressTracker, PhaseProgress
from myagent.models import Phase, Task, PhaseStatus, TaskStatus


@pytest.fixture
def sample_phase():
    """Create a sample phase for testing."""
    return Phase(
        index=1,
        name="Test Phase",
        depends_on=[],
        tasks=[
            Task(name="task1", parallel=False, owner=["architect"]),
            Task(name="task2", parallel=True, owner=["backend-dev", "frontend-dev"]),
        ],
    )


@pytest.fixture
def tracker():
    """Create a ProgressTracker instance."""
    return ProgressTracker()


class TestProgressTrackerStartPhase:
    """Tests for ProgressTracker.start_phase()."""

    def test_start_phase_creates_phase_progress(self, tracker, sample_phase):
        """Test start_phase creates PhaseProgress entry."""
        tracker.start_phase(sample_phase)

        assert 1 in tracker.phases
        assert tracker.phases[1].phase == sample_phase
        assert tracker.phases[1].status == PhaseStatus.IN_PROGRESS

    def test_start_phase_initializes_tasks(self, tracker, sample_phase):
        """Test start_phase initializes task progress and status."""
        tracker.start_phase(sample_phase)

        progress = tracker.phases[1]
        assert progress.task_progress["task1"] == 0.0
        assert progress.task_progress["task2"] == 0.0
        assert progress.task_statuses["task1"] == TaskStatus.PENDING
        assert progress.task_statuses["task2"] == TaskStatus.PENDING

    def test_start_phase_sets_start_time(self, tracker, sample_phase):
        """Test start_phase sets start_time."""
        tracker.start_phase(sample_phase)

        assert tracker.phases[1].start_time is not None


class TestProgressTrackerUpdateTask:
    """Tests for ProgressTracker.update_task()."""

    def test_update_task_updates_progress(self, tracker, sample_phase):
        """Test update_task updates progress."""
        tracker.start_phase(sample_phase)
        tracker.update_task(1, "task1", 50.0)

        assert tracker.phases[1].task_progress["task1"] == 50.0

    def test_update_task_updates_status(self, tracker, sample_phase):
        """Test update_task updates status."""
        tracker.start_phase(sample_phase)
        tracker.update_task(1, "task1", 100.0, status=TaskStatus.COMPLETED)

        assert tracker.phases[1].task_statuses["task1"] == TaskStatus.COMPLETED

    def test_update_task_ignores_unknown_phase(self, tracker):
        """Test update_task ignores unknown phase index."""
        tracker.update_task(999, "task1", 50.0)  # No exception

    def test_update_task_ignores_unknown_task(self, tracker, sample_phase):
        """Test update_task ignores unknown task."""
        tracker.start_phase(sample_phase)
        tracker.update_task(1, "unknown-task", 50.0)  # No exception


class TestProgressTrackerCompletePhase:
    """Tests for ProgressTracker.complete_phase()."""

    def test_complete_phase_sets_status(self, tracker, sample_phase):
        """Test complete_phase sets status."""
        tracker.start_phase(sample_phase)
        tracker.complete_phase(1)

        assert tracker.phases[1].status == PhaseStatus.COMPLETED
        assert tracker.phases[1].end_time is not None

    def test_complete_phase_marks_all_tasks_complete(self, tracker, sample_phase):
        """Test complete_phase marks all tasks as 100%."""
        tracker.start_phase(sample_phase)
        tracker.complete_phase(1)

        assert tracker.phases[1].task_progress["task1"] == 100.0
        assert tracker.phases[1].task_progress["task2"] == 100.0

    def test_complete_phase_failure(self, tracker, sample_phase):
        """Test complete_phase with success=False."""
        tracker.start_phase(sample_phase)
        tracker.complete_phase(1, success=False)

        assert tracker.phases[1].status == PhaseStatus.FAILED


class TestProgressTrackerGetPhaseProgress:
    """Tests for ProgressTracker.get_phase_progress()."""

    def test_get_phase_progress_returns_progress(self, tracker, sample_phase):
        """Test get_phase_progress returns PhaseProgress."""
        tracker.start_phase(sample_phase)

        progress = tracker.get_phase_progress(1)
        assert progress is not None
        assert progress.phase == sample_phase

    def test_get_phase_progress_returns_none_for_unknown(self, tracker):
        """Test get_phase_progress returns None for unknown phase."""
        result = tracker.get_phase_progress(999)
        assert result is None


class TestProgressTrackerGetOverallProgress:
    """Tests for ProgressTracker.get_overall_progress()."""

    def test_get_overall_progress_empty(self, tracker):
        """Test get_overall_progress returns 0 for empty tracker."""
        assert tracker.get_overall_progress() == 0.0

    def test_get_overall_progress_with_phases(self, tracker, sample_phase):
        """Test get_overall_progress calculates correctly."""
        tracker.start_phase(sample_phase)
        tracker.update_task(1, "task1", 100.0)
        tracker.update_task(1, "task2", 50.0)

        progress = tracker.get_overall_progress()
        assert 0 < progress < 100  # (100 + 50) / 2 = 75

    def test_get_overall_progress_completed_phase(self, tracker, sample_phase):
        """Test get_overall_progress with completed phase."""
        tracker.start_phase(sample_phase)
        tracker.complete_phase(1)

        progress = tracker.get_overall_progress()
        assert progress == 100.0


class TestProgressTrackerGetProgressInfo:
    """Tests for ProgressTracker.get_progress_info()."""

    def test_get_progress_info_empty(self, tracker):
        """Test get_progress_info returns empty list for empty tracker."""
        assert tracker.get_progress_info() == []

    def test_get_progress_info_with_data(self, tracker, sample_phase):
        """Test get_progress_info returns ProgressInfo list."""
        tracker.start_phase(sample_phase)
        tracker.update_task(1, "task1", 50.0)

        info = tracker.get_progress_info()
        assert len(info) == 2  # 2 tasks in phase
        assert info[0].name == "Test Phase / task1"
        assert info[0].progress_percent == 50.0


class TestProgressTrackerFormatProgressBar:
    """Tests for ProgressTracker.format_progress_bar()."""

    def test_format_progress_bar_0_percent(self, tracker):
        """Test format_progress_bar with 0%."""
        bar = tracker.format_progress_bar(0, width=10)
        assert "0.0%" in bar
        assert bar.count("░") == 10

    def test_format_progress_bar_100_percent(self, tracker):
        """Test format_progress_bar with 100%."""
        bar = tracker.format_progress_bar(100, width=10)
        assert "100.0%" in bar
        assert bar.count("█") == 10

    def test_format_progress_bar_50_percent(self, tracker):
        """Test format_progress_bar with 50%."""
        bar = tracker.format_progress_bar(50, width=10)
        assert "50.0%" in bar
        assert bar.count("█") == 5
        assert bar.count("░") == 5

    def test_format_progress_bar_custom_width(self, tracker):
        """Test format_progress_bar with custom width."""
        bar = tracker.format_progress_bar(33, width=20)
        assert len(bar) > 20


class TestProgressTrackerGetSummary:
    """Tests for ProgressTracker.get_summary()."""

    def test_get_summary_empty(self, tracker):
        """Test get_summary returns summary for empty tracker."""
        summary = tracker.get_summary()
        assert "进度追踪" in summary
        assert "总体进度" in summary

    def test_get_summary_with_phases(self, tracker, sample_phase):
        """Test get_summary includes phase info."""
        tracker.start_phase(sample_phase)
        tracker.update_task(1, "task1", 75.0)

        summary = tracker.get_summary()
        assert "Test Phase" in summary
        assert "task1" in summary

    def test_get_summary_shows_status_icons(self, tracker, sample_phase):
        """Test get_summary shows status icons."""
        tracker.start_phase(sample_phase)

        summary = tracker.get_summary()
        assert "🔄" in summary  # IN_PROGRESS icon


class TestPhaseProgress:
    """Tests for PhaseProgress dataclass."""

    def test_phase_progress_default_status(self, sample_phase):
        """Test PhaseProgress default status is PENDING."""
        progress = PhaseProgress(phase=sample_phase)
        assert progress.status == PhaseStatus.PENDING

    def test_phase_progress_task_dicts(self, sample_phase):
        """Test PhaseProgress has task dicts."""
        progress = PhaseProgress(phase=sample_phase)
        assert isinstance(progress.task_progress, dict)
        assert isinstance(progress.task_statuses, dict)

    def test_phase_progress_timestamps(self, sample_phase):
        """Test PhaseProgress timestamps can be None."""
        progress = PhaseProgress(phase=sample_phase)
        assert progress.start_time is None
        assert progress.end_time is None
        assert progress.current_task is None