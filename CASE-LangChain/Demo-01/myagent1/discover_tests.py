"""Simple test discovery and run."""
import sys
import os
from pathlib import Path
import traceback

# Setup paths
project_root = Path(r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1")
os.chdir(project_root)
sys.path.insert(0, str(project_root / "src"))

def main():
    results = []

    results.append("=" * 60)
    results.append("TEST RUNNER RESULTS")
    results.append("=" * 60)

    # Discover tests
    import pytest
    results.append(f"\npytest version: {pytest.__version__}")

    # Collect tests only (don't run)
    try:
        exit_code = pytest.main([
            "tests/",
            "--collect-only",
            "-q",
        ])
        results.append(f"\nCollection exit code: {exit_code}")
    except Exception as e:
        results.append(f"\nCollection error: {e}")
        results.append(traceback.format_exc())

    # Write to file
    output_file = project_root / "test_discovery.txt"
    with open(output_file, "w") as f:
        f.write("\n".join(results))

    print(f"Results written to: {output_file}")
    print("\n".join(results))

if __name__ == "__main__":
    main()
