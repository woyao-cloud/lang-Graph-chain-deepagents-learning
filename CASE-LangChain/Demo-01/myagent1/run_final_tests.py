#!/usr/bin/env python3
"""Final test runner - writes detailed output to file."""
import sys
import os
from pathlib import Path
import traceback as tb

# Setup
PROJECT_ROOT = Path(r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1")
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT / "src"))

LOG = []

def log(msg):
    LOG.append(str(msg))

log("=" * 70)
log("MYAGENT TEST RUNNER")
log("=" * 70)
log(f"Project: {PROJECT_ROOT}")
log(f"Python: {sys.executable}")
log(f"CWD: {os.getcwd()}")

# List test files
log("\nTest files:")
test_dir = PROJECT_ROOT / "tests"
test_files = sorted(test_dir.glob("test_*.py")) if test_dir.exists() else []
log(f"  Found {len(test_files)} test files")
for f in test_files:
    log(f"  - {f.name}")

# Run pytest
log("\nRunning pytest...")
try:
    import pytest
    log(f"  pytest version: {pytest.__version__}")

    # Run
    result = pytest.main([
        "tests/",
        "--cov=src/myagent",
        "--cov-report=term-missing",
        "-v",
        "--tb=short",
    ])

    log(f"\nPytest exit code: {result}")

    if result == 0:
        log("ALL TESTS PASSED")
    else:
        log(f"TESTS FAILED (code {result})")

except Exception as e:
    log(f"ERROR: {e}")
    log(tb.format_exc())

# Write log
log_file = PROJECT_ROOT / "test_run_log.txt"
with open(log_file, "w", encoding="utf-8") as f:
    f.write("\n".join(LOG))

# Print summary
print(f"\nLog written to: {log_file}")
print(f"Total lines: {len(LOG)}")
