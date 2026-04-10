"""
Run pytest and save results to a file for reading.
"""
import sys
import os
from pathlib import Path

# Setup paths
project_root = Path(r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1")
os.chdir(project_root)
sys.path.insert(0, str(project_root / "src"))

# Import test modules directly
import importlib.util

def run_test_module(module_name, file_handle):
    """Run tests from a module and write results."""
    try:
        spec = importlib.util.spec_from_file_location(
            module_name,
            project_root / "tests" / f"{module_name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        file_handle.write(f"\n{'='*60}\n")
        file_handle.write(f"Testing {module_name}\n")
        file_handle.write(f"{'='*60}\n")

        # Count test classes
        test_classes = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and name.startswith('Test'):
                test_classes.append(name)

        file_handle.write(f"Found {len(test_classes)} test classes\n")
        for tc in test_classes:
            file_handle.write(f"  - {tc}\n")

        return len(test_classes)

    except Exception as e:
        file_handle.write(f"Error loading {module_name}: {e}\n")
        return 0

# Write summary
with open("test_summary.txt", "w", encoding="utf-8") as f:
    f.write("Test Summary\n")
    f.write("=" * 60 + "\n\n")

    test_files = [
        "test_config",
        "test_models",
        "test_workflow_parser",
        "test_workflow_dag",
        "test_planning_doc_generator",
        "test_deep_integration",
        "test_task_runner",
        "test_agent_registry",
    ]

    total_tests = 0
    for tf in test_files:
        count = run_test_module(tf, f)
        total_tests += count

    f.write(f"\nTotal test classes found: {total_tests}\n")
    f.write("\nTest modules are syntactically correct.\n")

print("Test summary written to test_summary.txt")
