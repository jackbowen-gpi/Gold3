#!/usr/bin/env python
"""
Comprehensive test runner for GOLD3 Django project.

This script provides multiple ways to run tests with different configurations:
- All tests
- Unit tests only (fast)
- Integration tests only
- Smoke tests only
- Tests by app
- Tests with coverage
- Tests with different verbosity levels

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit            # Run unit tests only
    python run_tests.py --integration     # Run integration tests only
    python run_tests.py --smoke           # Run smoke tests only
    python run_tests.py --app workflow    # Run tests for specific app
    python run_tests.py --coverage        # Run with coverage report
    python run_tests.py --verbose         # Run with verbose output
    python run_tests.py --failfast        # Stop on first failure
"""

import argparse
import sys
import subprocess
from pathlib import Path


class TestRunner:
    """Comprehensive test runner for GOLD3 project."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.django_manage = self.project_root / "manage.py"
        self.pytest_config = self.project_root / "pytest.ini"

    def run_django_tests(self, test_path=None, verbosity=2, failfast=False):
        """Run tests using Django's test runner."""
        cmd = [
            sys.executable,
            str(self.django_manage),
            "test",
            "--settings=gchub_db.test_settings",
        ]

        if test_path:
            cmd.append(test_path)

        if verbosity:
            cmd.extend(["--verbosity", str(verbosity)])

        if failfast:
            cmd.append("--failfast")

        print(f"Running Django tests: {' '.join(cmd)}")
        return subprocess.run(cmd, cwd=self.project_root)

    def run_pytest(
        self,
        test_path=None,
        coverage=False,
        verbose=False,
        markers=None,
        failfast=False,
    ):
        """Run tests using pytest."""
        cmd = [sys.executable, "-m", "pytest"]

        if test_path:
            cmd.append(str(test_path))

        if coverage:
            cmd.extend(["--cov=gchub_db", "--cov-report=html", "--cov-report=term"])

        if verbose:
            cmd.append("-v")
        # Remove the -q option to allow normal pytest output

        if markers:
            cmd.extend(["-m", markers])

        if failfast:
            cmd.append("--tb=short")
            cmd.append("-x")

        print(f"Running pytest: {' '.join(cmd)}")
        return subprocess.run(cmd, cwd=self.project_root)

    def run_unit_tests(self, **kwargs):
        """Run unit tests only."""
        print("🧪 Running Unit Tests (Fast, Isolated)")
        return self.run_pytest("tests/unit", markers="unit", **kwargs)

    def run_integration_tests(self, **kwargs):
        """Run integration tests only."""
        print("🔗 Running Integration Tests (May be slower)")
        return self.run_pytest("tests/integration", markers="integration", **kwargs)

    def run_smoke_tests(self, **kwargs):
        """Run smoke tests only."""
        print("🚀 Running Smoke Tests (Quick CI checks)")
        return self.run_pytest("tests/smoke", markers="smoke", **kwargs)

    def run_app_tests(self, app_name, **kwargs):
        """Run tests for a specific Django app."""
        print(f"📱 Running tests for app: {app_name}")
        test_path = f"gchub_db.apps.{app_name}"
        return self.run_django_tests(test_path, **kwargs)

    def run_all_tests(self, **kwargs):
        """Run all tests."""
        print("🎯 Running All Tests")
        return self.run_pytest(**kwargs)

    def run_workflow_tests(self, **kwargs):
        """Run workflow-specific tests."""
        print("⚙️ Running Workflow Tests")
        return self.run_app_tests("workflow", **kwargs)

    def run_with_coverage(self, **kwargs):
        """Run tests with coverage."""
        print("📊 Running Tests with Coverage")
        kwargs["coverage"] = True
        return self.run_all_tests(**kwargs)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for GOLD3 Django project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit            # Run unit tests only
  python run_tests.py --integration     # Run integration tests only
  python run_tests.py --smoke           # Run smoke tests only
  python run_tests.py --app workflow    # Run tests for workflow app
  python run_tests.py --coverage        # Run with coverage report
  python run_tests.py --verbose         # Run with verbose output
  python run_tests.py --failfast        # Stop on first failure
        """,
    )

    # Test type options
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument("--unit", action="store_true", help="Run unit tests only")
    test_group.add_argument("--integration", action="store_true", help="Run integration tests only")
    test_group.add_argument("--smoke", action="store_true", help="Run smoke tests only")
    test_group.add_argument("--app", metavar="APP_NAME", help="Run tests for specific Django app")
    test_group.add_argument("--workflow", action="store_true", help="Run workflow tests")

    # Test configuration options
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--failfast", action="store_true", help="Stop on first failure")
    parser.add_argument("--django", action="store_true", help="Use Django test runner instead of pytest")

    args = parser.parse_args()

    runner = TestRunner()

    # Determine test configuration
    kwargs = {"coverage": args.coverage, "verbose": args.verbose}

    if args.failfast:
        kwargs["failfast"] = True

    # Run appropriate tests
    if args.unit:
        result = runner.run_unit_tests(**kwargs)
    elif args.integration:
        result = runner.run_integration_tests(**kwargs)
    elif args.smoke:
        result = runner.run_smoke_tests(**kwargs)
    elif args.app:
        result = runner.run_app_tests(args.app, **kwargs)
    elif args.workflow:
        result = runner.run_workflow_tests(**kwargs)
    elif args.coverage:
        result = runner.run_with_coverage(**kwargs)
    else:
        # Default: run all tests
        if args.django:
            result = runner.run_django_tests(**kwargs)
        else:
            result = runner.run_all_tests(**kwargs)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
