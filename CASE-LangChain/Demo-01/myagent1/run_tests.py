#!/usr/bin/env python
"""Run tests and write results to file."""
import sys
import os
from pathlib import Path

# Setup paths
project_root = Path("D:/python-projects/langchain/CASE-LangChain/Demo-01/myagent1")
sys.path.insert(0, str(project_root / "src"))

os.chdir(project_root)

# Run tests using pytest API
import pytest

args = [
    "tests/",
    "--cov=src/myagent",
    "--cov-report=term-missing",
    "-v",
    "--tb=short",
]

# Write results to file
with open("test_results.log", "w", encoding="utf-8") as f:
    # Capture the exit code
    exit_code = pytest.main(args, plugins=[])
    f.write(f"Exit code: {exit_code}\n")

print(f"Tests completed with exit code: {exit_code}")
