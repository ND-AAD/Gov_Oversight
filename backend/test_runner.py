#!/usr/bin/env python3
"""
Test runner for LA 2028 RFP Monitor Phase 1.

Comprehensive test suite to validate all Phase 1 functionality before moving to Phase 2.
"""

import sys
import subprocess
import os
from pathlib import Path
import argparse
import time

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print colored header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")


def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")


def run_command(cmd, description="", capture_output=True):
    """Run a command and return success status."""
    if description:
        print(f"{Colors.OKCYAN}Running: {description}{Colors.ENDC}")
    
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0, ""
    except Exception as e:
        return False, str(e)


def check_dependencies():
    """Check that required dependencies are installed."""
    print_header("Checking Dependencies")
    
    dependencies = [
        ("python", "python --version", "Python 3.10+"),
        ("pytest", "pytest --version", "pytest testing framework"),
        ("click", "python -c 'import click; print(click.__version__)'", "Click CLI framework"),
    ]
    
    all_good = True
    
    for name, check_cmd, description in dependencies:
        success, output = run_command(check_cmd, f"Checking {name}")
        if success:
            version = output.strip().split('\n')[0] if output else "installed"
            print_success(f"{description}: {version}")
        else:
            print_error(f"{description}: Not found")
            all_good = False
    
    return all_good


def run_unit_tests():
    """Run unit tests for data models and core functionality."""
    print_header("Running Unit Tests")
    
    test_files = [
        ("test_models.py", "Data Models (RFP, SiteConfig, FieldMapping)"),
        ("test_location_binder.py", "Location-Binding Engine"),
    ]
    
    all_passed = True
    results = {}
    
    for test_file, description in test_files:
        print_info(f"Testing: {description}")
        
        cmd = f"cd tests && python -m pytest {test_file} -v"
        success, output = run_command(cmd, capture_output=True)
        
        if success:
            print_success(f"{description}: PASSED")
            results[test_file] = "PASSED"
        else:
            print_error(f"{description}: FAILED")
            print(f"Error output:\n{output}")
            results[test_file] = "FAILED"
            all_passed = False
    
    return all_passed, results


def run_integration_tests():
    """Run integration tests."""
    print_header("Running Integration Tests")
    
    cmd = "cd tests && python -m pytest test_integration.py -v"
    success, output = run_command(cmd, "Integration tests")
    
    if success:
        print_success("Integration tests: PASSED")
        return True
    else:
        print_error("Integration tests: FAILED")
        print(f"Error output:\n{output}")
        return False


def test_cli_functionality():
    """Test CLI functionality."""
    print_header("Testing CLI Functionality")
    
    # Create temporary test directory
    import tempfile
    temp_dir = tempfile.mkdtemp()
    
    cli_tests = [
        (f"python main.py --data-dir {temp_dir} stats", "Statistics command"),
        (f"python main.py --data-dir {temp_dir} list-sites", "List sites command"),
        (f"python main.py --data-dir {temp_dir} list-rfps", "List RFPs command"),
        (f"python main.py --data-dir {temp_dir} backup", "Backup command"),
    ]
    
    all_passed = True
    
    for cmd, description in cli_tests:
        success, output = run_command(cmd, f"Testing {description}")
        if success:
            print_success(f"{description}: PASSED")
        else:
            print_error(f"{description}: FAILED")
            print(f"Error: {output}")
            all_passed = False
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    return all_passed


def test_data_validation():
    """Test data validation functionality."""
    print_header("Testing Data Validation")
    
    validation_tests = [
        (
            "python -c \"from models.validation import validate_url; print('OK' if validate_url('https://lacounty.gov').is_valid else 'FAIL')\"",
            "URL validation"
        ),
        (
            "python -c \"from models.validation import validate_date_string; print('OK' if validate_date_string('2024-12-16').is_valid else 'FAIL')\"",
            "Date validation"
        ),
        (
            "python -c \"from models.validation import validate_currency_string; print('OK' if validate_currency_string('$50,000').is_valid else 'FAIL')\"",
            "Currency validation"
        ),
        (
            "python -c \"from models.validation import validate_olympic_relevance; print('OK' if validate_olympic_relevance('2028 Olympics surveillance')[0] else 'FAIL')\"",
            "Olympic relevance detection"
        ),
    ]
    
    all_passed = True
    
    for cmd, description in validation_tests:
        success, output = run_command(cmd, f"Testing {description}")
        if success and "OK" in output:
            print_success(f"{description}: PASSED")
        else:
            print_error(f"{description}: FAILED")
            all_passed = False
    
    return all_passed


def test_serialization():
    """Test data serialization functionality."""
    print_header("Testing Data Serialization")
    
    # Test RFP serialization
    rfp_test = """
from models import RFP
from datetime import datetime
import json

rfp = RFP(
    id='test',
    title='Test RFP',
    url='https://example.com',
    source_site='test',
    extracted_fields={'status': 'Active'},
    detected_at=datetime.now(),
    content_hash='hash',
    categories=['Test']
)

# Test serialization
data = rfp.to_dict()
restored = RFP.from_dict(data)

print('OK' if restored.id == rfp.id and restored.title == rfp.title else 'FAIL')
"""
    
    success, output = run_command(f"python -c \"{rfp_test}\"", "RFP serialization")
    if success and "OK" in output:
        print_success("RFP serialization: PASSED")
        return True
    else:
        print_error("RFP serialization: FAILED")
        return False


def generate_test_report(results):
    """Generate comprehensive test report."""
    print_header("Phase 1 Test Report")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result == "PASSED")
    failed_tests = total_tests - passed_tests
    
    print(f"\n{Colors.BOLD}Test Summary:{Colors.ENDC}")
    print(f"Total Tests: {total_tests}")
    print_success(f"Passed: {passed_tests}")
    if failed_tests > 0:
        print_error(f"Failed: {failed_tests}")
    else:
        print_success("Failed: 0")
    
    print(f"\n{Colors.BOLD}Detailed Results:{Colors.ENDC}")
    for test_name, result in results.items():
        status_color = Colors.OKGREEN if result == "PASSED" else Colors.FAIL
        print(f"  {status_color}{test_name}: {result}{Colors.ENDC}")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.ENDC}")
    
    if success_rate >= 90:
        print_success("\n🎉 Phase 1 is ready for production!")
        print_success("✅ Ready to proceed to Phase 2: Frontend Integration")
    elif success_rate >= 75:
        print_warning("\n⚠️  Phase 1 has some issues but is mostly functional")
        print_warning("Consider fixing failing tests before Phase 2")
    else:
        print_error("\n❌ Phase 1 has significant issues")
        print_error("Must fix failing tests before proceeding to Phase 2")
    
    return success_rate >= 90


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Test runner for LA 2028 RFP Monitor Phase 1")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--cli-only", action="store_true", help="Run only CLI tests")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency checking")
    args = parser.parse_args()
    
    print_header("LA 2028 RFP Monitor - Phase 1 Test Suite")
    print_info("Testing all Phase 1 functionality before Phase 2...")
    
    start_time = time.time()
    results = {}
    
    # Check dependencies
    if not args.skip_deps:
        if not check_dependencies():
            print_error("Dependency check failed. Please install missing dependencies.")
            sys.exit(1)
        results["dependencies"] = "PASSED"
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    all_passed = True
    
    # Run tests based on arguments
    if args.unit_only:
        unit_passed, unit_results = run_unit_tests()
        results.update(unit_results)
        all_passed = unit_passed
    elif args.integration_only:
        integration_passed = run_integration_tests()
        results["integration_tests"] = "PASSED" if integration_passed else "FAILED"
        all_passed = integration_passed
    elif args.cli_only:
        cli_passed = test_cli_functionality()
        results["cli_tests"] = "PASSED" if cli_passed else "FAILED"
        all_passed = cli_passed
    else:
        # Run all tests
        
        # Unit tests
        unit_passed, unit_results = run_unit_tests()
        results.update(unit_results)
        all_passed &= unit_passed
        
        # Integration tests
        integration_passed = run_integration_tests()
        results["integration_tests"] = "PASSED" if integration_passed else "FAILED"
        all_passed &= integration_passed
        
        # CLI tests
        cli_passed = test_cli_functionality()
        results["cli_tests"] = "PASSED" if cli_passed else "FAILED"
        all_passed &= cli_passed
        
        # Validation tests
        validation_passed = test_data_validation()
        results["validation_tests"] = "PASSED" if validation_passed else "FAILED"
        all_passed &= validation_passed
        
        # Serialization tests
        serialization_passed = test_serialization()
        results["serialization_tests"] = "PASSED" if serialization_passed else "FAILED"
        all_passed &= serialization_passed
    
    # Generate report
    ready_for_phase2 = generate_test_report(results)
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n{Colors.BOLD}Test execution completed in {duration:.2f} seconds{Colors.ENDC}")
    
    # Exit with appropriate code
    if ready_for_phase2:
        print_success("\n🚀 Phase 1 testing complete - Ready for Phase 2!")
        sys.exit(0)
    else:
        print_error("\n🚨 Phase 1 testing failed - Fix issues before Phase 2")
        sys.exit(1)


if __name__ == "__main__":
    main()
