#!/usr/bin/env python3
"""
PyGWalker pytest grouping and execution script.

This script provides consistent test execution across local development and CI environments.
It supports multiple test groups with clear separation of concerns.

Usage:
    python scripts/run_pytest_groups.py --group core          # Run core tests
    python scripts/run_pytest_groups.py --group integration   # Run integration tests
    python scripts/run_pytest_groups.py --group static-checks # Run static checks
    python scripts/run_pytest_groups.py --group all           # Run all tests
    python scripts/run_pytest_groups.py --list-groups         # List available groups
"""

import argparse
import glob
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
APP_DIR = PROJECT_ROOT / "app"

TEST_GROUPS = {
    "core": {
        "description": "Fast unit tests for core functionality (tests/unit/test_*.py, excludes optional deps)",
        "type": "pytest",
        "test_dir": "tests/unit",
        "exclude_patterns": ["tests/unit/test_dsl_transform.py"],
        "pytest_args": ["-v", "--tb=short", "-q"],
    },
    "integration": {
        "description": "Integration tests (tests/integration/, excludes optional deps)",
        "type": "pytest",
        "test_dir": "tests/integration",
        "exclude_patterns": ["tests/integration/test_data_parsers.py"],
        "include_patterns": [
            "tests/integration/test_data_pipeline.py",
            "tests/integration/test_field_quality_integration.py",
            "tests/integration/test_spec_pipeline.py",
            "tests/integration/test_spec_persistence.py",
            "tests/integration/test_recommendation_explainer.py",
            "tests/integration/test_format_invoke_walk_code.py",
        ],
        "pytest_args": ["-v", "--tb=short", "-q"],
    },
    "optional-deps": {
        "description": "Tests requiring optional dependencies (mini-racer, duckdb-engine)",
        "type": "pytest",
        "patterns": [
            "tests/unit/test_dsl_transform.py",
            "tests/integration/test_data_parsers.py",
        ],
        "pytest_args": ["-v", "--tb=short"],
    },
    "static-checks": {
        "description": "Static code analysis (TypeScript type check + Python linting)",
        "type": "custom",
        "commands": [
            {
                "name": "TypeScript Type Check",
                "cmd": ["yarn", "typecheck"],
                "cwd": str(APP_DIR),
            },
            {
                "name": "Python Lint",
                "cmd": [sys.executable, "-m", "pylint", "pygwalker/", "--rcfile=.pylintrc", "--output-format=parseable", "--reports=n"],
                "cwd": str(PROJECT_ROOT),
                "continue_on_error": True,
            },
        ],
    },
    "slow": {
        "description": "Slow-running tests (performance, stress, etc.)",
        "type": "pytest",
        "marker": "slow",
        "pytest_args": ["-v", "--tb=short"],
    },
    "data-pipeline": {
        "description": "Data pipeline related tests",
        "type": "pytest",
        "patterns": [
            "tests/integration/test_data_pipeline.py",
            "tests/integration/test_data_parsers.py",
            "tests/integration/test_spec_pipeline.py",
            "tests/unit/test_dsl_transform.py",
        ],
        "pytest_args": ["-v", "--tb=short", "-q"],
    },
    "field-quality": {
        "description": "Field quality analysis tests",
        "type": "pytest",
        "patterns": [
            "tests/unit/test_field_quality.py",
            "tests/integration/test_field_quality_integration.py",
        ],
        "pytest_args": ["-v", "--tb=short", "-q"],
    },
    "utility": {
        "description": "Utility function tests",
        "type": "pytest",
        "patterns": [
            "tests/unit/test_fname_encodings.py",
            "tests/integration/test_format_invoke_walk_code.py",
            "tests/integration/test_spec_persistence.py",
            "tests/integration/test_recommendation_explainer.py",
            "tests/unit/test_scatter_plot_sampling.py",
        ],
        "pytest_args": ["-v", "--tb=short", "-q"],
    },
    "all": {
        "description": "Run all pytest tests (tests/unit/ and tests/integration/)",
        "type": "pytest",
        "patterns": ["tests/unit", "tests/integration"],
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


def run_command(cmd: List[str], cwd: str = None, name: str = None) -> int:
    """Run a single command and return its exit code."""
    if name:
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print(f"{'='*60}")
    
    print(f"Command: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    print()
    
    result = subprocess.run(cmd, cwd=cwd or str(PROJECT_ROOT))
    return result.returncode


def run_custom_commands(commands: List[Dict[str, Any]]) -> int:
    """Run a list of custom commands."""
    overall_exit_code = 0
    
    for cmd_config in commands:
        name = cmd_config.get("name", "Custom command")
        cmd = cmd_config["cmd"]
        cwd = cmd_config.get("cwd")
        continue_on_error = cmd_config.get("continue_on_error", False)
        
        exit_code = run_command(cmd, cwd, name)
        
        if exit_code != 0:
            overall_exit_code = exit_code
            if not continue_on_error:
                print(f"\n❌ {name} failed with exit code {exit_code}")
                return overall_exit_code
            else:
                print(f"\n⚠️  {name} failed (continuing due to continue_on_error)")
        else:
            print(f"\n✅ {name} passed")
    
    return overall_exit_code


def run_group(group_name: str) -> int:
    """Run a specific test group."""
    if group_name not in TEST_GROUPS:
        print(f"Error: Unknown test group '{group_name}'")
        list_groups()
        return 1
    
    config = TEST_GROUPS[group_name]
    group_type = config.get("type", "pytest")
    
    if group_type == "custom":
        return run_custom_commands(config["commands"])
    
    args = config.get("pytest_args", ["-v", "--tb=short"])
    
    if "patterns" in config:
        args.extend(config["patterns"])
    elif "include_patterns" in config:
        args.extend(config["include_patterns"])
    elif "test_files_glob" in config:
        test_files = glob.glob(str(PROJECT_ROOT / config["test_files_glob"]))
        exclude_patterns = config.get("exclude_patterns", [])
        exclude_files = []
        for pattern in exclude_patterns:
            exclude_files.extend(glob.glob(str(PROJECT_ROOT / pattern)))
        exclude_set = set(exclude_files)
        filtered_files = [f for f in test_files if f not in exclude_set]
        if filtered_files:
            args.extend([f.replace(str(PROJECT_ROOT) + "/", "") for f in filtered_files])
        if "marker" in config:
            args.extend(["-k", config["marker"]])
    else:
        if "test_dir" in config:
            exclude_patterns = config.get("exclude_patterns", [])
            if exclude_patterns:
                test_files = glob.glob(str(PROJECT_ROOT / config["test_dir"] / "*.py"))
                exclude_files = []
                for pattern in exclude_patterns:
                    exclude_files.extend(glob.glob(str(PROJECT_ROOT / pattern)))
                exclude_set = set(exclude_files)
                filtered_files = [f for f in test_files if f not in exclude_set]
                args.extend([f.replace(str(PROJECT_ROOT) + "/", "") for f in filtered_files])
            else:
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
