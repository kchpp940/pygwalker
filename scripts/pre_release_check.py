import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class CheckStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus = CheckStatus.NOT_STARTED
    message: str = ""
    details: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ReleaseCheckConfig:
    project_root: Path
    pygwalker_dir: Path
    templates_dir: Path
    dist_dir: Path
    app_dir: Path
    pyproject_path: Path
    verbose: bool = False
    strict: bool = False
    skip_import: bool = False


class ReleaseChecker:
    def __init__(self, config: ReleaseCheckConfig):
        self.config = config
        self.results: Dict[str, CheckResult] = {}
        self.all_passed = True

    def _print_header(self, title: str):
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")

    def _print_step(self, name: str, status: str, detail: str = ""):
        icon = "✓" if status == "PASS" else ("✗" if status == "FAIL" else "○")
        if detail:
            print(f"  {icon} [{status}] {name} - {detail}")
        else:
            print(f"  {icon} [{status}] {name}")

    def _print_details(self, details: List[str], indent: str = "    "):
        for d in details:
            print(f"{indent}{d}")

    def _add_result(self, name: str, passed: bool, message: str = "", details: List[str] = None, error: str = None):
        status = CheckStatus.PASSED if passed else CheckStatus.FAILED
        result = CheckResult(
            name=name,
            status=status,
            message=message,
            details=details or [],
            error=error
        )
        self.results[name] = result
        if not passed:
            self.all_passed = False
        self._print_step(name, "PASS" if passed else "FAIL", message)
        if details:
            self._print_details(details)
        if error:
            print(f"    ERROR: {error}")

    def check_template_files(self) -> bool:
        print("\n  Checking template files...")
        
        required_templates = [
            "index.html",
            "jupyter_iframe_message.html", 
            "pygwalker_iframe.html",
            "pygwalker_main_page.html",
        ]
        
        missing = []
        for template in required_templates:
            path = self.config.templates_dir / template
            if not path.exists():
                missing.append(template)
        
        if missing:
            self._add_result(
                "Template Files",
                False,
                f"Missing {len(missing)} template files",
                [],
                f"Missing templates: {', '.join(missing)}"
            )
            return False
        
        if self.config.verbose:
            details = [f"Found: {t}" for t in required_templates]
            self._add_result(
                "Template Files",
                True,
                f"All {len(required_templates)} template files present",
                details
            )
        else:
            self._add_result(
                "Template Files",
                True,
                f"All {len(required_templates)} template files present"
            )
        return True

    def check_version_consistency(self) -> bool:
        print("\n  Checking version consistency...")
        
        version_pattern = r'__version__\s*=\s*["\']([^"\']+)["\']'
        
        init_file = self.config.pygwalker_dir / "__init__.py"
        if not init_file.exists():
            self._add_result(
                "Version Consistency",
                False,
                "__init__.py not found",
                [],
                f"File not found: {init_file}"
            )
            return False
        
        init_content = init_file.read_text()
        match = re.search(version_pattern, init_content)
        if not match:
            self._add_result(
                "Version Consistency",
                False,
                "__version__ not found in __init__.py",
                [],
                "Version definition not found"
            )
            return False
        
        python_version = match.group(1)
        
        if self.config.verbose:
            print(f"    Python package version: {python_version}")
        
        pyproject_content = self.config.pyproject_path.read_text()
        if 'dynamic = ["version"]' not in pyproject_content:
            self._add_result(
                "Version Consistency",
                False,
                "pyproject.toml version configuration",
                [],
                "pyproject.toml should use dynamic version"
            )
            return False
        
        app_package_json = self.config.app_dir / "package.json"
        if app_package_json.exists():
            with open(app_package_json) as f:
                app_pkg = json.load(f)
            app_version = app_pkg.get("version", "")
            if self.config.verbose:
                print(f"    Frontend app version: {app_version}")
        
        pyproject_content = self.config.pyproject_path.read_text()
        gw_dsl_parser_match = re.search(r'gw_dsl_parser==([\d.]+)', pyproject_content)
        app_dsl_version = ""
        if app_package_json.exists():
            with open(app_package_json) as f:
                app_pkg = json.load(f)
            app_dsl_version = app_pkg.get("dependencies", {}).get("@kanaries/gw-dsl-parser", "")
            app_dsl_version = app_dsl_version.replace("^", "").replace("~", "")
        
        if gw_dsl_parser_match and app_dsl_version:
            py_dsl_version = gw_dsl_parser_match.group(1)
            if self.config.verbose:
                print(f"    Python gw_dsl_parser version: {py_dsl_version}")
                print(f"    Frontend @kanaries/gw-dsl-parser version: {app_dsl_version}")
            
            if not py_dsl_version.startswith(app_dsl_version) and not app_dsl_version.startswith(py_dsl_version):
                major_minor_py = ".".join(py_dsl_version.split(".")[:3])
                major_minor_app = ".".join(app_dsl_version.split(".")[:3])
                
                if major_minor_py != major_minor_app:
                    self._add_result(
                        "Version Consistency",
                        False,
                        "gw-dsl-parser versions mismatch",
                        [],
                        f"Python: {py_dsl_version} vs Frontend: {app_dsl_version}"
                    )
                    return False
        
        self._add_result(
            "Version Consistency",
            True,
            f"Version {python_version} is valid and consistent",
            [f"Package version: {python_version}"] if self.config.verbose else []
        )
        return True

    def check_dist_artifacts(self) -> bool:
        print("\n  Checking frontend dist artifacts...")
        
        required_files = [
            "pygwalker-app.iife.js",
            "pygwalker-app.es.js",
            "dsl-to-workflow.umd.js",
            "vega-to-dsl.umd.js",
        ]
        
        if not self.config.dist_dir.exists():
            self._add_result(
                "Dist Artifacts",
                False,
                "dist directory not found",
                [],
                f"Missing: {self.config.dist_dir}. Please run 'yarn build' in app/ directory first."
            )
            return False
        
        existing = list(self.config.dist_dir.glob("*"))
        existing_names = [f.name for f in existing if f.is_file()]
        
        if self.config.verbose:
            print(f"    Files in dist/: {existing_names}")
        
        missing = [f for f in required_files if f not in existing_names]
        
        if missing:
            self._add_result(
                "Dist Artifacts",
                False,
                f"Missing {len(missing)} files from dist/",
                [],
                f"Missing: {', '.join(missing)}"
            )
            return False
        
        sizes = []
        for f in required_files:
            file_path = self.config.dist_dir / f
            size = file_path.stat().st_size
            if size == 0:
                self._add_result(
                    "Dist Artifacts",
                    False,
                    f"{f} is empty",
                    [],
                    f"File size is 0 bytes"
                )
                return False
            sizes.append(f"{f}: {size / 1024:.1f} KB")
        
        if self.config.verbose:
            self._add_result(
                "Dist Artifacts",
                True,
                f"All {len(required_files)} dist files present and non-empty",
                sizes
            )
        else:
            self._add_result(
                "Dist Artifacts",
                True,
                f"All {len(required_files)} dist files present and non-empty"
            )
        return True

    def check_importable(self) -> bool:
        if self.config.skip_import:
            self._add_result(
                "Import Check",
                True,
                "Skipped (--skip-import flag set)"
            )
            return True
        
        print("\n  Checking key imports...")
        
        critical_imports = [
            "pygwalker",
            "pygwalker.api.adapter",
            "pygwalker.api.html",
            "pygwalker.api.component",
            "pygwalker.api.pygwalker",
        ]
        
        import_errors = []
        
        for import_path in critical_imports:
            try:
                __import__(import_path)
                if self.config.verbose:
                    print(f"    Successfully imported: {import_path}")
            except Exception as e:
                error_msg = f"{import_path}: {str(e)}"
                import_errors.append(error_msg)
        
        if import_errors:
            self._add_result(
                "Import Check",
                False,
                f"{len(import_errors)} imports failed",
                [],
                "\n".join(import_errors)
            )
            return False
        
        try:
            import pygwalker
            from pygwalker.api.adapter import walk, render, table
            from pygwalker.api.html import to_html
            from pygwalker.api.component import component
            from pygwalker.data_parsers.base import FieldSpec
            
            expected_exports = ["walk", "render", "table", "to_html", "component", "FieldSpec"]
            details = [f"Exported: {e}" for e in expected_exports]
            
            self._add_result(
                "Import Check",
                True,
                f"All {len(critical_imports)} critical imports successful",
                details if self.config.verbose else []
            )
            return True
        except Exception as e:
            self._add_result(
                "Import Check",
                False,
                "Key API export check failed",
                [],
                str(e)
            )
            return False

    def check_manifest_include_templates(self) -> bool:
        print("\n  Checking MANIFEST.in and build config...")
        
        manifest_path = self.config.project_root / "MANIFEST.in"
        if manifest_path.exists():
            manifest_content = manifest_path.read_text()
            if "graft pygwalker/templates" not in manifest_content:
                self._add_result(
                    "Manifest/Build Config",
                    False,
                    "MANIFEST.in missing templates graft",
                    [],
                    "Missing 'graft pygwalker/templates' in MANIFEST.in"
                )
                return False
            if self.config.verbose:
                print("    MANIFEST.in found with templates graft")
        else:
            if self.config.verbose:
                print("    MANIFEST.in not found, checking pyproject.toml")
        
        pyproject_content = self.config.pyproject_path.read_text()
        
        checks = [
            ('"pygwalker/templates/**', "templates glob in include"),
            ('"pygwalker/templates/**/*', "templates/* glob in include"),
        ]
        
        missing = []
        for check_str, desc in checks:
            if check_str not in pyproject_content:
                missing.append(desc)
        
        if missing:
            self._add_result(
                "Manifest/Build Config",
                False,
                "pyproject.toml missing template includes",
                [],
                f"Missing: {', '.join(missing)}"
            )
            return False
        
        self._add_result(
            "Manifest/Build Config",
            True,
            "Build configuration includes templates"
        )
        return True

    def run(self) -> bool:
        self._print_header("PYGWALKER RELEASE PRE-CHECK")
        print(f"  Project root: {self.config.project_root}")
        print(f"  Time: {__import__('time').strftime('%Y-%m-%d %H:%M:%S')}")
        
        checks = [
            ("Template Files", self.check_template_files),
            ("Version Consistency", self.check_version_consistency),
            ("Dist Artifacts", self.check_dist_artifacts),
            ("Import Check", self.check_importable),
            ("Manifest/Build Config", self.check_manifest_include_templates),
        ]
        
        for name, check_func in checks:
            result = check_func()
            
            if not result and self.config.strict:
                print(f"\n  [!] Stopping on failure: {name}")
                break
        
        self._print_summary()
        
        return self.all_passed

    def _print_summary(self):
        print("\n" + "=" * 70)
        print("  PRE-CHECK SUMMARY")
        print("=" * 70)
        
        passed = 0
        failed = 0
        
        for name, result in self.results.items():
            if result.status == CheckStatus.PASSED:
                status_str = "✓ PASS"
                passed += 1
            elif result.status == CheckStatus.FAILED:
                status_str = "✗ FAIL"
                failed += 1
            else:
                status_str = "? UNKNOWN"
            
            print(f"  {status_str:10} {name:35}")
        
        print("\n" + "-" * 70)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 70)
        
        if failed > 0:
            print("\n  [!] RELEASE BLOCKED: Pre-check failed. Please fix the issues above.")
        else:
            print("\n  [✓] All pre-checks passed. Ready to build and publish!")


def main():
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(
        prog="pre-release-check",
        description="Pre-release validation checks for PyGWalker build and publish"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Path to project root (defaults to script's parent directory)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Stop immediately on first failure"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output"
    )
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help="Skip import checks (useful for CI environment without full install)"
    )
    
    args = parser.parse_args()
    
    if args.project_root:
        project_root = Path(args.project_root).resolve()
    else:
        project_root = Path(__file__).resolve().parent.parent
    
    config = ReleaseCheckConfig(
        project_root=project_root,
        pygwalker_dir=project_root / "pygwalker",
        templates_dir=project_root / "pygwalker" / "templates",
        dist_dir=project_root / "pygwalker" / "templates" / "dist",
        app_dir=project_root / "app",
        pyproject_path=project_root / "pyproject.toml",
        verbose=args.verbose,
        strict=args.strict,
        skip_import=args.skip_import
    )
    
    checker = ReleaseChecker(config)
    
    success = checker.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
