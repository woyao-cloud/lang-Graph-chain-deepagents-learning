"""
Run pytest and write results to files.
Exit code is written to a separate file.
"""
import sys
import os
from pathlib import Path

# Setup
project_root = Path(r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1")
os.chdir(project_root)
sys.path.insert(0, str(project_root / "src"))

def run():
    # Open output files
    stdout_file = open("pytest_stdout.txt", "w", encoding="utf-8")
    stderr_file = open("pytest_stderr.txt", "w", encoding="utf-8")
    result_file = open("pytest_result.txt", "w", encoding="utf-8")

    results = []

    try:
        import pytest

        results.append(f"pytest version: {pytest.__version__}")

        # Run with verbose output going to files
        exit_code = pytest.main([
            "tests/",
            "--cov=src/myagent",
            "--cov-report=term-missing",
            "-v",
            "--tb=short",
        ])

        results.append(f"exit_code: {exit_code}")

    except Exception as e:
        import traceback
        results.append(f"ERROR: {e}")
        results.append(traceback.format_exc())

    finally:
        stdout_file.close()
        stderr_file.close()

    # Write results
    result_file.write("\n".join(results))
    result_file.close()

    return results

if __name__ == "__main__":
    results = run()

    # Print to real stdout (force flush)
    for line in results:
        print(line, flush=True)
