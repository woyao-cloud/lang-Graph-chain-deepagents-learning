"""Comprehensive test runner with file output."""
import sys
import os
from pathlib import Path

log_lines = []

def log(msg):
    log_lines.append(msg)

log("=" * 70)
log("MyAgent Test Suite Runner")
log("=" * 70)

# Setup paths
project_root = Path(r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1")
os.chdir(project_root)
sys.path.insert(0, str(project_root / "src"))

log(f"Project root: {project_root}")
log(f"Python: {sys.executable}")
log(f"Working dir: {os.getcwd()}")

# List test files
log("\nTest files found:")
test_files = list((project_root / "tests").glob("test_*.py"))
for tf in sorted(test_files):
    log(f"  - {tf.name}")

# Try pytest
log("\nRunning pytest...")
try:
    import pytest
    log(f"pytest version: {pytest.__version__}")

    exit_code = pytest.main([
        str(project_root / "tests"),
        "--cov=src/myagent",
        "--cov-report=term-missing",
        "-v",
        "--tb=short",
        "--no-header",
    ])

    log(f"\nPytest exit code: {exit_code}")

    if exit_code == 0:
        log("All tests PASSED!")
    else:
        log(f"Some tests FAILED (exit code: {exit_code})")

except Exception as e:
    log(f"Pytest error: {e}")
    import traceback
    log(traceback.format_exc())

# Write log
log_file = project_root / "pytest_test_log.txt"
with open(log_file, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

print(f"Log written to {log_file}")
print(f"Total log lines: {len(log_lines)}")
print("First 20 lines:")
for line in log_lines[:20]:
    print(line)
