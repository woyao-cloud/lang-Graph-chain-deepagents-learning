"""Simple test runner that outputs to file."""
import sys
import os

os.chdir(r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1")
sys.path.insert(0, r"D:\python-projects\langchain\CASE-LangChain\Demo-01\myagent1\src")

# Try to import all test modules to check syntax
try:
    import test_config
    import test_models
    import test_workflow_parser
    import test_workflow_dag
    import test_planning_doc_generator
    import test_deep_integration
    import test_task_runner
    import test_agent_registry

    result = "ALL TESTS LOADED SUCCESSFULLY"
except Exception as e:
    result = f"ERROR: {e}"

with open("test_check_result.txt", "w") as f:
    f.write(result + "\n")

print(result)
