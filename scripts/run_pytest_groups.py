#!/usr/bin/env python3
"""
PyGWalker pytest grouping and execution script.

This script provides consistent test execution across local development and CI environments.
It supports multiple test groups with clear separation of concerns.

Usage:
    python scripts/run_pytest_groups.py --group core          # Run core tests
    python scripts/run_pytest_groups.py --group integration   # Run integration tests
    python scripts/run_pytest_groups.py --group all           # Run all tests
    python scripts/run_pytest_groups.py --list-groups         # List available groups
"""

import argparse
import glob
import subprocess
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).parent.parent

TEST_GROUPS = {
    "core": {
        "description": "Fast unit tests for core functionality (tests/test_*.py)",
        "test_files_glob": "tests/test_*.py",
        "marker": "not integration and not slow",
        "pytest_args": ["-v", "--tb=short", "-q"],
    },
    "integration": {
        "description": "Integration tests that may require external resources",
        "test_files_glob": "tests/test_*.py",
        "marker": "integration",
        "pytest_args": ["-v", "--tb=short", "-q"],
    },
    "slow": {
        "description": "Slow-running tests (performance, stress, etc.)",
        "test_files_glob": "tests/test_*.py",
        "marker": "slow",
        "pytest_args": ["-v", "--tb=short"],
    },
    "data-pipeline": {
        "description": "Data pipeline related tests",
        "patterns": [
            "tests/test_data_pipeline.py",
            "tests/test_data_parsers.py",
            "tests/test_spec_pipeline.py",
            "tests/test_dsl_transform.py",
        ],
        "pytest_args": ["-v", "--tb=short", "-q"],
    },
    "field-quality": {
        "description": "Field quality analysis tests",
        "patterns": [
            "tests/test_field_quality.py",
            "tests/test_field_quality_integration.py",
        ],
        "pytest_args": ["-v", "--tb=short", "-q"],
    },
    "utility": {
        "description": "Utility function tests",
        "patterns": [
            "tests/test_fname_encodings.py",
            "tests/test_format_invoke_walk_code.py",
            "tests/test_spec_persistence.py",
            "tests/test_recommendation_explainer.py",
            "tests/test_scatter_plot_sampling.py",
        ],
        "pytest_args": ["-v", "--tb=short", "-q"],
    },
    "all": {
        "description": "Run all pytest tests (tests/test_*.py)",
        "test_files_glob": "tests/test_*.py",
        "pytest_args": ["-v", "--tb=short"],
    },
}


def run_pytest(args: List[str]) -> int:
    """Run pytest with the given arguments."""
    cmd = [sys.executable, "-m", "pytest"] + args
    
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def list_groups():
    """List all available test groups."""
    print("\nAvailable test groups:\n")
    for name, config in TEST_GROUPS.items():
        print(f"  {name:20} - {config['description']}")
    print("\n")


def run_group(group_name: str) -> int:
    """Run a specific test group."""
    if group_name not in TEST_GROUPS:
        print(f"Error: Unknown test group '{group_name}'")
        list_groups()
        return 1
    
    config = TEST_GROUPS[group_name]
    args = config.get("pytest_args", ["-v", "--tb=short"])
    
    if "patterns" in config:
        args.extend(config["patterns"])
    elif "test_files_glob" in config:
        test_files = glob.glob(str(PROJECT_ROOT / config["test_files_glob"]))
        if test_files:
            args.extend(test_files)
        if "marker" in config:
            args.extend(["-k", config["marker"]])
    else:
        if "test_dir" in config:
            args.append(config["test_dir"])
        if "marker" in config:
            args.extend(["-k", config["marker"]])
    
    return run_pytest(args)


def main():
    parser = argparse.ArgumentParser(
        description="PyGWalker test runner with group support"
    )
    parser.add_argument(
        "--group",
        type=str,
        help="Test group to run (use --list-groups to see available groups)"
    )
    parser.add_argument(
        "--list-groups",
        action="store_true",
        help="List all available test groups"
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments to pass to pytest"
    )
    
    args = parser.parse_args()
    
    if args.list_groups:
        list_groups()
        return 0
    
    if args.group:
        return run_group(args.group)
    
    if args.pytest_args:
        return run_pytest(args.pytest_args)
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
