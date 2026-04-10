#!/usr/bin/env python
"""Test script for myagent flow."""

import sys
import os
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Remove old test project
test_project = os.path.join(os.path.dirname(__file__), 'test-project')
if os.path.exists(test_project):
    shutil.rmtree(test_project)

print("=== Step 1: init ===")
from myagent.cli.commands import init_project
from pathlib import Path

project_path = Path(test_project)
init_project(project_path, 'test-project')

# Test plan
print("\n=== Step 2: plan ===")
from myagent.cli.commands import run_phase
run_phase(project_path, 'plan')

# Confirm
print("\n=== Step 3: confirm ===")
from myagent.cli.commands import confirm_planning
confirm_planning(project_path, 'PLANNING.md')

# Test execute
print("\n=== Step 4: execute ===")
run_phase(project_path, 'execute')

print("\n[DONE] All steps completed!")
