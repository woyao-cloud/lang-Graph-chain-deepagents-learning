"""Run tests and capture coverage."""
import sys
import os
from pathlib import Path
import io

# Change to project dir
os.chdir(r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1")

# Add src to path
sys.path.insert(0, r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1\src")

# Capture stdout/stderr
old_stdout = sys.stdout
old_stderr = sys.stderr

output = io.StringIO()
sys.stdout = output
sys.stderr = output

try:
    import pytest
    result = pytest.main([
        "tests/",
        "--cov=src/myagent",
        "--cov-report=term-missing",
        "-v",
        "--tb=short",
    ])
except SystemExit as e:
    result = e.code

# Restore and write
sys.stdout = old_stdout
sys.stderr = old_stderr

content = output.getvalue()
output.close()

# Write to file
with open("test_results.log", "w", encoding="utf-8") as f:
    f.write(content)
    f.write(f"\n\nEXIT CODE: {result}\n")

# Also print to console
print(content)
print(f"Tests finished with exit code: {result}")
