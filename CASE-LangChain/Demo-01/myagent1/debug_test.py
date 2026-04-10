#!/usr/bin/env python3
"""Debug test runner."""
import sys
import os
from pathlib import Path

print("DEBUG: Starting test runner", flush=True)

# Change to project dir
project_root = Path(r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1")
os.chdir(project_root)
sys.path.insert(0, str(project_root / "src"))

print(f"DEBUG: Changed to {os.getcwd()}", flush=True)

# List test files
print("DEBUG: Looking for test files...", flush=True)
tests_dir = project_root / "tests"
if tests_dir.exists():
    files = list(tests_dir.glob("test_*.py"))
    print(f"DEBUG: Found {len(files)} test files", flush=True)
    for f in files:
        print(f"  - {f.name}", flush=True)
else:
    print(f"DEBUG: Tests dir not found: {tests_dir}", flush=True)

# Write a simple log
log_path = project_root / "debug_test_log.txt"
with open(log_path, "w") as f:
    f.write("Debug log started\n")
    f.write(f"Python: {sys.executable}\n")
    f.write(f"Dir: {os.getcwd()}\n")
    f.write(f"Test files: {len(files) if tests_dir.exists() else 0}\n")

print(f"DEBUG: Log written to {log_path}", flush=True)
print("DEBUG: Done", flush=True)
