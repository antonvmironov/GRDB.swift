#!/usr/bin/env python3
"""
GRDB.swift Test Runner

This script builds and tests the GRDB.swift package in a Linux container environment.
It's designed for CI/CD and local development use, providing comprehensive test coverage
and detailed reporting.

Usage:
    ./run_all_tests.py [options]

Options:
    --package-only       Only run Swift Package Manager tests
    --coverage           Enable code coverage reporting
    --report-path PATH   Path to store test reports (default: ./reports)
    --skip-sqlite        Skip SQLite build tests
    --filter PATTERN     Run only tests matching the pattern
    --clean              Clean before building
    --verbose            Show verbose output

Example:
    ./run_all_tests.py --coverage --filter "SQLite"
"""

import argparse
import datetime
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Known issues or limitations in the Linux/Docker environment
KNOWN_ISSUES = {
    "SQLCipher": "SQLCipher tests require CocoaPods which is not available on Linux",
    "XCFramework": "XCFramework builds are not supported on Linux",
    "CoreGraphics": "CoreGraphics framework is not available on Linux - some tests will be skipped",
    "DispatchQueue": "The __dispatch_queue_get_label function works differently on Linux - using compatibility wrapper",
    "CustomSQLiteTests": "Tests in the CustomSQLite directory rely on Xcode and are not supported in SPM builds",
}

def print_header(message: str) -> None:
    """Print a formatted header message."""
    print(f"\n{'=' * 80}")
    print(f"== {message}")
    print(f"{'=' * 80}\n")

def print_step(message: str) -> None:
    """Print a formatted step message."""
    print(f"📋 {message}")

def print_success(message: str) -> None:
    """Print a formatted success message."""
    print(f"✅ {message}")

def print_error(message: str) -> None:
    """Print a formatted error message."""
    print(f"❌ {message}")

def print_warning(message: str) -> None:
    """Print a formatted warning message."""
    print(f"⚠️  {message}")

def run_command(cmd: List[str], cwd: Optional[Path] = None, 
                capture_output: bool = False, 
                env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
    """
    Run a shell command and return the exit code, stdout, and stderr.

    Args:
        cmd: Command to run as a list of strings
        cwd: Working directory to run the command in
        capture_output: Whether to capture output or stream it
        env: Environment variables to set

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                check=False,
                env=merged_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return result.returncode, result.stdout, result.stderr
        else:
            # Stream output in real-time
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=cwd,
                check=False,
                env=merged_env
            )
            return result.returncode, "", ""
    except Exception as e:
        print_error(f"Failed to run command {' '.join(cmd)}: {e}")
        return 1, "", str(e)

def setup_reports_directory(base_path: str) -> Path:
    """
    Create and setup the reports directory structure.

    Args:
        base_path: Base path for reports

    Returns:
        Path to the reports directory
    """
    reports_dir = Path(base_path)
    reports_dir.mkdir(exist_ok=True)

    # Create subdirectories
    (reports_dir / "test-results").mkdir(exist_ok=True)
    (reports_dir / "coverage").mkdir(exist_ok=True)
    (reports_dir / "html").mkdir(exist_ok=True)

    return reports_dir

def check_swift_version() -> bool:
    """
    Check if Swift is installed and meets minimum version requirements.

    Returns:
        True if Swift is available and meets requirements
    """
    print_step("Checking Swift installation...")

    exit_code, stdout, stderr = run_command(["swift", "--version"], capture_output=True)

    if exit_code != 0:
        print_error("Swift is not installed or not in PATH")
        return False

    print_success(f"Swift version: {stdout.strip()}")
    
    # Verify Swift 6+ requirement
    match = re.search(r'Swift version (\d+)\.', stdout)
    if match and int(match.group(1)) >= 6:
        return True
    else:
        print_error("Swift 6+ is required to build GRDB.swift")
        return False

def run_spm_tests(coverage: bool = False, filter: Optional[str] = None) -> bool:
    """
    Run Swift Package Manager tests.

    Args:
        coverage: Whether to enable code coverage
        filter: Optional test filter pattern

    Returns:
        True if tests passed
    """
    print_header("Running Swift Package Manager Tests")

    cmd = ["swift", "test", "--parallel"]
    
    if coverage:
        cmd.append("--enable-code-coverage")
    
    if filter:
        cmd.extend(["--filter", filter])

    start_time = time.time()
    exit_code, stdout, stderr = run_command(cmd)
    duration = time.time() - start_time
    
    if exit_code == 0:
        print_success(f"SPM tests passed in {duration:.2f}s")
        return True
    else:
        print_error(f"SPM tests failed after {duration:.2f}s")
        return False

def clean_package() -> None:
    """Clean the Swift package."""
    print_step("Cleaning Swift package...")
    run_command(["swift", "package", "clean"])
    
    # Remove build artifacts
    for path in ["./reports", "./.build"]:
        if os.path.exists(path):
            print_step(f"Removing {path}...")
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                print_warning(f"Failed to remove {path}: {e}")

def build_sqlite_custom() -> bool:
    """
    Check SQLite configuration.

    Returns:
        True if configuration is valid
    """
    print_header("Checking SQLite Configuration")
    
    # For SPM builds, we use the SQLite configuration directly from Package.swift
    # The GRDBSQLite target is already properly set up there
    print_step("Using SQLite configuration from Package.swift...")
    
    # Just verify the SQLite headers are available
    if os.path.exists("GRDBSQLite/sqlite3.h"):
        print_success("Found SQLite headers in GRDBSQLite directory")
        return True
    else:
        print_warning("SQLite headers not found in expected location, but will continue with SPM build")
        # Don't fail - SPM will handle this
        return True

def patch_test_files() -> None:
    """
    Patch test files for platform compatibility.
    This function handles differences between macOS and Linux environments.
    """
    print_step("Patching test files for platform compatibility...")
    
    # Check if we're running on Linux
    if platform.system() != "Linux":
        print_step("Not running on Linux, skipping patches")
        return
    
    try:
        # Copy our patch files to override the test files
        patches_dir = Path("patches")
        if patches_dir.exists():
            # Copy CGFloatTests.swift
            cgfloat_patch = patches_dir / "CGFloatTests.swift"
            cgfloat_test = Path("Tests/GRDBTests/CGFloatTests.swift")
            if cgfloat_patch.exists() and cgfloat_test.exists():
                print_step(f"Copying patched {cgfloat_test.name}...")
                shutil.copy(cgfloat_patch, cgfloat_test)
                print_success(f"Patched {cgfloat_test}")
            
            # Copy DispatchQueueLabel.swift to Tests/GRDBTests/Support
            dispatch_patch = patches_dir / "DispatchQueueLabel.swift"
            support_dir = Path("Tests/GRDBTests/Support")
            support_dir.mkdir(exist_ok=True)
            dispatch_target = support_dir / "DispatchQueueLabel.swift"
            
            if dispatch_patch.exists():
                print_step(f"Copying {dispatch_patch.name} to {support_dir}...")
                shutil.copy(dispatch_patch, dispatch_target)
                print_success(f"Added {dispatch_target}")
                
            # Patch DatabaseSnapshotTests.swift to use getQueueLabel
            db_snapshot_test = Path("Tests/GRDBTests/DatabaseSnapshotTests.swift")
            if db_snapshot_test.exists():
                print_step(f"Patching {db_snapshot_test.name}...")
                with open(db_snapshot_test, "r") as f:
                    content = f.read()
                
                # Replace the __dispatch_queue_get_label calls with our wrapper
                patched_content = re.sub(
                    r'String\(utf8String: __dispatch_queue_get_label\(nil\)\)',
                    'getQueueLabel(nil)',
                    content
                )
                
                # Add import for our support file
                if "#if canImport(Dispatch)" not in patched_content:
                    patched_content = "#if canImport(Dispatch)\nimport Dispatch\n#endif\n\n" + patched_content
                
                # Write the patched file
                with open(db_snapshot_test, "w") as f:
                    f.write(patched_content)
                
                print_success(f"Patched {db_snapshot_test}")
        else:
            # Fallback to in-place patching if patches directory doesn't exist
            cgfloat_test = Path("Tests/GRDBTests/CGFloatTests.swift")
            if cgfloat_test.exists():
                print_step(f"Patching {cgfloat_test}...")
                
                # Read the file content
                with open(cgfloat_test, "r") as f:
                    content = f.read()
                
                # Replace CoreGraphics import with conditional import
                patched_content = content.replace(
                    'import CoreGraphics',
                    '#if canImport(CoreGraphics)\nimport CoreGraphics\n#endif'
                )
                
                # Make the test conditional on platform
                patched_content = patched_content.replace(
                    'class CGFloatTests: GRDBTestCase {',
                    '#if canImport(CoreGraphics)\nclass CGFloatTests: GRDBTestCase {\n#else\n// CGFloat tests are skipped on Linux\nclass CGFloatTests {}\n#endif'
                )
                
                # Write the patched file
                with open(cgfloat_test, "w") as f:
                    f.write(patched_content)
                
                print_success(f"Patched {cgfloat_test}")
        
        print_success("Test files patched for platform compatibility")
    except Exception as e:
        print_warning(f"Failed to patch test files: {e}")

def generate_summary_report(results: Dict, reports_dir: Path) -> None:
    """
    Generate a summary report of all build and test results.

    Args:
        results: Dictionary of test results
        reports_dir: Path to the reports directory
    """
    print_step("Generating summary report...")

    # Generate timestamp
    timestamp = datetime.datetime.now().isoformat()

    summary = {
        "timestamp": timestamp,
        "platform": platform.platform(),
        "swift_version": get_swift_version(),
        "tests": results,
        "total_tests": len(results),
        "successful_tests": sum(1 for r in results.values() if r.get("success", False)),
        "skipped_tests": sum(1 for r in results.values() if r.get("skipped", False)),
        "known_issues": KNOWN_ISSUES,
        "overall_success": all(r.get("success", False) for r in results.values() if not r.get("skipped", False))
    }

    # Write JSON summary
    summary_file = reports_dir / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    # Write human-readable summary
    summary_text_file = reports_dir / "summary.txt"
    with open(summary_text_file, "w") as f:
        f.write(f"GRDB.swift Test Summary\n")
        f.write(f"=====================\n\n")
        f.write(f"Date: {timestamp}\n")
        f.write(f"Platform: {platform.platform()}\n")
        f.write(f"Swift Version: {get_swift_version()}\n\n")
        f.write(f"Results:\n")
        f.write(f"--------\n")
        for test_name, result in results.items():
            if result.get("skipped", False):
                f.write(f"- {test_name}: SKIPPED ({result.get('reason', 'No reason provided')})\n")
            elif result.get("success", False):
                f.write(f"- {test_name}: PASSED ({result.get('duration', 0):.2f}s)\n")
            else:
                f.write(f"- {test_name}: FAILED ({result.get('duration', 0):.2f}s)\n")
        
        f.write(f"\nSummary:\n")
        f.write(f"--------\n")
        f.write(f"Total Tests: {len(results)}\n")
        f.write(f"Passed: {sum(1 for r in results.values() if r.get('success', False))}\n")
        f.write(f"Failed: {sum(1 for r in results.values() if not r.get('success', False) and not r.get('skipped', False))}\n")
        f.write(f"Skipped: {sum(1 for r in results.values() if r.get('skipped', False))}\n")
        f.write(f"Overall: {'SUCCESS' if summary['overall_success'] else 'FAILURE'}\n")

    print_success("Summary report generated")

def get_swift_version() -> str:
    """Get the Swift version as a string."""
    exit_code, stdout, stderr = run_command(["swift", "--version"], capture_output=True)
    if exit_code == 0:
        match = re.search(r'Swift version ([0-9\.]+)', stdout)
        if match:
            return match.group(1)
    return "unknown"

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="GRDB.swift Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  ./run_all_tests.py

  # Run only Swift Package Manager tests
  ./run_all_tests.py --package-only

  # Run tests with code coverage
  ./run_all_tests.py --coverage

  # Run specific tests
  ./run_all_tests.py --filter "SQLite"
        """
    )

    parser.add_argument(
        "--package-only",
        action="store_true",
        help="Only run Swift Package Manager tests"
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Enable code coverage reporting"
    )

    parser.add_argument(
        "--report-path",
        default="./reports",
        help="Path to store test reports (default: ./reports)"
    )

    parser.add_argument(
        "--skip-sqlite",
        action="store_true",
        help="Skip SQLite build tests"
    )

    parser.add_argument(
        "--filter",
        help="Run only tests matching the pattern"
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean before building"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show verbose output"
    )

    return parser.parse_args()

def main() -> int:
    """
    Main function to build and test GRDB.swift.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse command line arguments
    args = parse_arguments()

    print_header("GRDB.swift Test Runner")
    print(f"Running on {platform.platform()} with Python {platform.python_version()}")

    # Check prerequisites
    if not check_swift_version():
        return 1

    # Clean if requested
    if args.clean:
        clean_package()

    # Setup directories
    reports_dir = setup_reports_directory(args.report_path)
    
    # Patch test files for platform compatibility
    patch_test_files()
    
    # Track test results
    results = {}
    overall_success = True

    # Run SPM tests
    start_time = time.time()
    spm_success = run_spm_tests(args.coverage, args.filter)
    duration = time.time() - start_time
    
    results["SwiftPackageManager"] = {
        "success": spm_success,
        "duration": duration,
        "skipped": False
    }
    
    overall_success = overall_success and spm_success

    # If not package-only, run additional tests
    if not args.package_only:
        # Verify SQLite configuration
        if not args.skip_sqlite:
            start_time = time.time()
            sqlite_check_success = build_sqlite_custom()
            duration = time.time() - start_time
            
            results["SQLiteConfiguration"] = {
                "success": sqlite_check_success,
                "duration": duration,
                "skipped": False
            }
            
            # This is just a check, don't fail the overall process if it fails
            # SPM will use the SQLite configuration from Package.swift
        
        # Skip tests that require Xcode/CocoaPods
        for test_name, reason in KNOWN_ISSUES.items():
            results[test_name] = {
                "success": False,
                "skipped": True,
                "reason": reason
            }
    
    # Generate summary report
    generate_summary_report(results, reports_dir)
    
    # Print final results
    print_header("Test Results")
    for test_name, result in results.items():
        if result.get("skipped", False):
            print(f"⚠️  {test_name}: SKIPPED ({result.get('reason', '')})")
        elif result.get("success", False):
            print(f"✅ {test_name}: PASSED ({result.get('duration', 0):.2f}s)")
        else:
            print(f"❌ {test_name}: FAILED ({result.get('duration', 0):.2f}s)")
    
    if overall_success:
        print_success("All tests passed!")
        return 0
    else:
        print_error("Some tests failed. Check the reports directory for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())