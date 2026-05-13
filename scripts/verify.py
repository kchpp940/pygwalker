import sys
import os
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class StageStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    name: str
    status: StageStatus = StageStatus.NOT_STARTED
    duration: float = 0.0
    output: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class VerifyConfig:
    project_root: Path
    app_dir: Path
    tests_dir: Path
    skip_stages: List[str] = field(default_factory=list)
    verbose: bool = False
    stop_on_failure: bool = True


class VerifyRunner:
    def __init__(self, config: VerifyConfig):
        self.config = config
        self.results: Dict[str, StageResult] = {}
        self._total_start = time.time()

    def _run_command(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        capture_output: bool = True,
        timeout: Optional[int] = None
    ) -> Tuple[int, List[str], str]:
        cwd_str = str(cwd) if cwd else str(self.config.project_root)
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd_str,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            stdout_lines = result.stdout.strip().split("\n") if result.stdout else []
            stderr = result.stderr.strip()
            return result.returncode, stdout_lines, stderr
        except subprocess.TimeoutExpired:
            return -1, [], f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, [], str(e)

    def _print_header(self, title: str):
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")

    def _print_step(self, step: str, status: str, detail: str = ""):
        icon = "✓" if status == "PASS" else ("✗" if status == "FAIL" else "…")
        if detail:
            print(f"  {icon} [{status}] {step} - {detail}")
        else:
            print(f"  {icon} [{status}] {step}")

    def _should_skip(self, stage_name: str) -> bool:
        return stage_name in self.config.skip_stages

    def _run_stage(self, name: str, func) -> StageResult:
        result = StageResult(name=name)
        self.results[name] = result
        result.status = StageStatus.IN_PROGRESS

        if self._should_skip(name):
            result.status = StageStatus.SKIPPED
            self._print_step(name, "SKIP")
            return result

        start = time.time()
        self._print_header(f"STAGE: {name}")

        try:
            success, output, error = func()
            result.duration = time.time() - start
            result.output = output
            result.error = error

            if success:
                result.status = StageStatus.PASSED
                self._print_step(name, "PASS", f"({result.duration:.2f}s)")
            else:
                result.status = StageStatus.FAILED
                self._print_step(name, "FAIL", f"({result.duration:.2f}s)")
                if error:
                    print(f"\n    Error: {error}")
        except Exception as e:
            result.duration = time.time() - start
            result.status = StageStatus.FAILED
            result.error = str(e)
            self._print_step(name, "FAIL", f"({result.duration:.2f}s)")
            print(f"\n    Exception: {e}")

        return result

    def stage_frontend_build(self) -> Tuple[bool, List[str], Optional[str]]:
        app_dir = self.config.app_dir
        if not app_dir.exists():
            return False, [], f"App directory not found: {app_dir}"

        if self.config.verbose:
            print("  Installing dependencies...")
        returncode, _, stderr = self._run_command(["yarn"], cwd=app_dir, timeout=300)
        if returncode != 0:
            return False, [], f"yarn install failed: {stderr}"

        if self.config.verbose:
            print("  Building frontend...")
        returncode, stdout, stderr = self._run_command(["yarn", "build"], cwd=app_dir, timeout=300)

        if self.config.verbose:
            for line in stdout:
                print(f"    {line}")

        if returncode == 0:
            dist_dir = self.config.project_root / "pygwalker" / "templates" / "dist"
            if dist_dir.exists():
                return True, stdout, None
            else:
                return False, stdout, f"Build completed but dist directory not found: {dist_dir}"
        else:
            return False, stdout, stderr if stderr else "yarn build failed"

    def stage_static_architecture_check(self) -> Tuple[bool, List[str], Optional[str]]:
        all_passed = True
        all_output = []
        errors = []

        python_scripts = [
            self.config.tests_dir / "verify_return_structure.py",
            self.config.tests_dir / "verify_recommendation_explanation.py",
        ]

        for script in python_scripts:
            if not script.exists():
                if self.config.verbose:
                    print(f"    [SKIP] Python script not found: {script}")
                continue

            print(f"    Running: {script.name}")
            returncode, stdout, stderr = self._run_command(
                [sys.executable, str(script)],
                cwd=self.config.project_root,
                timeout=120
            )

            if self.config.verbose:
                for line in stdout:
                    print(f"      {line}")

            all_output.extend(stdout)

            if returncode != 0:
                all_passed = False
                error_msg = stderr if stderr else f"{script.name} failed"
                errors.append(error_msg)
                print(f"    ✗ {script.name} FAILED")
            else:
                print(f"    ✓ {script.name} PASSED")

        ts_scripts = [
            self.config.app_dir / "src" / "utils" / "verify-export-flow.ts",
            self.config.app_dir / "src" / "utils" / "verify-filter.ts",
            self.config.app_dir / "src" / "utils" / "verify-integration.ts",
        ]

        for script in ts_scripts:
            if not script.exists():
                if self.config.verbose:
                    print(f"    [SKIP] TypeScript script not found: {script}")
                continue

            js_script = script.with_suffix('.js')
            if not js_script.exists():
                compiled_script = self.config.app_dir / "tests" / f"{script.stem}.js"
                if compiled_script.exists():
                    script = compiled_script
                else:
                    if self.config.verbose:
                        print(f"    [SKIP] No compiled JS found for: {script}")
                    continue

            print(f"    Running: {script.name}")
            returncode, stdout, stderr = self._run_command(
                ["node", str(script)],
                cwd=self.config.project_root,
                timeout=120
            )

            if self.config.verbose:
                for line in stdout:
                    print(f"      {line}")

            all_output.extend(stdout)

            if returncode != 0:
                all_passed = False
                error_msg = stderr if stderr else f"{script.name} failed"
                errors.append(error_msg)
                print(f"    ✗ {script.name} FAILED")
            else:
                print(f"    ✓ {script.name} PASSED")

        js_scripts = [
            self.config.app_dir / "tests" / "verify-end-to-end.js",
            self.config.app_dir / "tests" / "verify-export-config.js",
            self.config.app_dir / "tests" / "verify-export-refactor.js",
            self.config.app_dir / "tests" / "verify-recommendation-explanation.js",
        ]

        for script in js_scripts:
            if not script.exists():
                if self.config.verbose:
                    print(f"    [SKIP] JS script not found: {script}")
                continue

            print(f"    Running: {script.name}")
            returncode, stdout, stderr = self._run_command(
                ["node", str(script)],
                cwd=self.config.project_root,
                timeout=120
            )

            if self.config.verbose:
                for line in stdout:
                    print(f"      {line}")

            all_output.extend(stdout)

            if returncode != 0:
                all_passed = False
                error_msg = stderr if stderr else f"{script.name} failed"
                errors.append(error_msg)
                print(f"    ✗ {script.name} FAILED")
            else:
                print(f"    ✓ {script.name} PASSED")

        return all_passed, all_output, "; ".join(errors) if errors else None

    def stage_python_unit_tests(self) -> Tuple[bool, List[str], Optional[str]]:
        print("  Running pytest on tests/ directory...")

        cmd = [
            sys.executable, "-m", "pytest",
            "-v",
            "--tb=short",
            "tests/"
        ]

        returncode, stdout, stderr = self._run_command(
            cmd,
            cwd=self.config.project_root,
            timeout=300
        )

        if self.config.verbose:
            for line in stdout:
                print(f"    {line}")

        if returncode == 0:
            passed_count = sum(1 for line in stdout if "PASSED" in line)
            return True, stdout, f"{passed_count} tests passed"
        else:
            failed_lines = [line for line in stdout if "FAILED" in line or "ERROR" in line]
            return False, stdout, stderr if stderr else (
                "; ".join(failed_lines) if failed_lines else "pytest failed"
            )

    def stage_data_pipeline_regression(self) -> Tuple[bool, List[str], Optional[str]]:
        all_passed = True
        all_output = []
        errors = []

        key_test_files = [
            "tests/test_spec_pipeline.py",
            "tests/test_data_parsers.py",
            "tests/test_field_quality.py",
            "tests/test_field_quality_integration.py",
        ]

        for test_file in key_test_files:
            test_path = self.config.project_root / test_file
            if not test_path.exists():
                if self.config.verbose:
                    print(f"    [SKIP] Test file not found: {test_file}")
                continue

            print(f"    Running: {test_file}")
            returncode, stdout, stderr = self._run_command(
                [sys.executable, "-m", "pytest", "-v", "--tb=short", test_file],
                cwd=self.config.project_root,
                timeout=180
            )

            if self.config.verbose:
                for line in stdout:
                    print(f"      {line}")

            all_output.extend(stdout)

            if returncode != 0:
                all_passed = False
                error_msg = stderr if stderr else f"{test_file} failed"
                errors.append(error_msg)
                print(f"    ✗ {test_file} FAILED")
            else:
                print(f"    ✓ {test_file} PASSED")

        return all_passed, all_output, "; ".join(errors) if errors else None

    def _print_summary(self):
        total_duration = time.time() - self._total_start

        print("\n" + "=" * 70)
        print("  VERIFICATION SUMMARY")
        print("=" * 70)
        print(f"\n  Total duration: {total_duration:.2f} seconds\n")

        passed = 0
        failed = 0
        skipped = 0

        for name, result in self.results.items():
            if result.status == StageStatus.PASSED:
                status_str = "✓ PASS"
                passed += 1
            elif result.status == StageStatus.FAILED:
                status_str = "✗ FAIL"
                failed += 1
            elif result.status == StageStatus.SKIPPED:
                status_str = "○ SKIP"
                skipped += 1
            else:
                status_str = "? UNKNOWN"

            print(f"  {status_str:10} {name:35} ({result.duration:.2f}s)")

        print("\n" + "-" * 70)
        print(f"  Results: {passed} passed, {failed} failed, {skipped} skipped")
        print("=" * 70)

        return failed == 0

    def run(self) -> bool:
        self._print_header("PYGWALKER VERIFICATION SUITE")
        print(f"  Project root: {self.config.project_root}")
        print(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.config.skip_stages:
            print(f"  Skipping stages: {', '.join(self.config.skip_stages)}")

        stages = [
            ("Frontend Build", self.stage_frontend_build),
            ("Static Architecture Check", self.stage_static_architecture_check),
            ("Python Unit Tests", self.stage_python_unit_tests),
            ("Data Pipeline Regression", self.stage_data_pipeline_regression),
        ]

        for name, stage_func in stages:
            result = self._run_stage(name, stage_func)

            if result.status == StageStatus.FAILED and self.config.stop_on_failure:
                print(f"\n  Stopping on failure: {name}")
                break

        return self._print_summary()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog="verify",
        description="Unified verification suite for PyGWalker"
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        default=[],
        help="Stages to skip (e.g., 'Frontend Build' 'Static Architecture Check')"
    )
    parser.add_argument(
        "--no-stop",
        action="store_true",
        help="Continue running even if a stage fails"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: skip frontend build and run only essential tests"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Path to project root (defaults to script's parent directory)"
    )

    args = parser.parse_args()

    if args.project_root:
        project_root = Path(args.project_root).resolve()
    else:
        project_root = Path(__file__).resolve().parent.parent

    skip_stages = list(args.skip)
    if args.quick:
        skip_stages.extend(["Frontend Build"])

    config = VerifyConfig(
        project_root=project_root,
        app_dir=project_root / "app",
        tests_dir=project_root / "tests",
        skip_stages=skip_stages,
        verbose=args.verbose,
        stop_on_failure=not args.no_stop
    )

    runner = VerifyRunner(config)
    success = runner.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
