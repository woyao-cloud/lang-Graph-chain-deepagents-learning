"""
Run pytest and capture coverage.
"""
import sys
import os
from pathlib import Path

# Setup paths
project_root = Path(r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1")
os.chdir(project_root)
sys.path.insert(0, str(project_root / "src"))

# Write start marker
with open("pytest_run_started.txt", "w") as f:
    f.write("Pytest run started\n")

# Import pytest
try:
    import pytest
    with open("pytest_import.txt", "w") as f:
        f.write(f"pytest imported: {pytest.__version__}\n")
except Exception as e:
    with open("pytest_error.txt", "w") as f:
        f.write(f"Import error: {e}\n")
    sys.exit(1)

# Run pytest
result = pytest.main([
    "tests/",
    "--cov=src/myagent",
    "--cov-report=term-missing",
    "-v",
    "--tb=short",
])

# Write result
with open("pytest_result.txt", "w") as f:
    f.write(f"Exit code: {result}\n")

print(f"Pytest finished with exit code: {result}")
