"""
Direct pytest runner with explicit output capture.
"""
import sys
import os
from pathlib import Path
import io

# Setup
project_root = Path(r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1")
os.chdir(project_root)
sys.path.insert(0, str(project_root / "src"))

# Capture stdout
class TeeOutput:
    def __init__(self, original, file):
        self.original = original
        self.file = file
        self.line_count = 0

    def write(self, data):
        self.file.write(data)
        if '\n' in data:
            self.line_count += data.count('\n')
        return self.original.write(data)

    def flush(self):
        self.file.flush()
        return self.original.flush()

# Open log file
log_path = project_root / "pytest_verbose_log.txt"
with open(log_path, "w", buffering=1) as log_file:
    log_file.write("=" * 70 + "\n")
    log_file.write("PYTEST VERBOSE LOG\n")
    log_file.write("=" * 70 + "\n")

    # Redirect stdout
    old_stdout = sys.stdout
    sys.stdout = TeeOutput(old_stdout, log_file)

    old_stderr = sys.stderr
    sys.stderr = TeeOutput(old_stderr, log_file)

    log_file.write("Starting pytest...\n")

    try:
        import pytest
        log_file.write(f"pytest version: {pytest.__version__}\n")

        # Run
        result = pytest.main([
            "tests/",
            "--cov=src/myagent",
            "--cov-report=term-missing",
            "-v",
            "--tb=short",
        ])

        log_file.write(f"\nPytest exit code: {result}\n")

    except Exception as e:
        import traceback
        log_file.write(f"Error: {e}\n")
        log_file.write(traceback.format_exc())

    # Restore stdout
    sys.stdout = old_stdout
    sys.stderr = old_stderr

# Print summary
with open(log_path, "r") as f:
    content = f.read()

print("=" * 70)
print("PYTEST VERBOSE LOG - SUMMARY")
print("=" * 70)
print(f"Log file: {log_path}")
print(f"Log size: {len(content)} bytes")
print(f"Lines: {content.count(chr(10))}")
print()
print("Log content:")
print("-" * 70)
print(content[:5000])
if len(content) > 5000:
    print("..." f"({len(content)-5000} more bytes)")
print("-" * 70)
