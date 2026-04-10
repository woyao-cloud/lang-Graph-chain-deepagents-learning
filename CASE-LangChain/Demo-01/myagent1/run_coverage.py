"""Run tests and capture coverage."""
import sys
import os
from pathlib import Path

# Change to project dir
os.chdir(r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1")

# Add src to path
sys.path.insert(0, r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1\src")

import pytest

result = pytest.main([
    "tests/",
    "--cov=src/myagent",
    "--cov-report=term-missing",
    "-v",
    "--tb=short",
])

# Write exit code to file
with open("exit_code.txt", "w") as f:
    f.write(f"Exit code: {result}\n")
