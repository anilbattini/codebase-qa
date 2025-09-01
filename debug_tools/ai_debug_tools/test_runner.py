#!/usr/bin/env python3
"""
Test Runner - Test Execution and Reporting
==========================================

This module handles test execution, reporting, and result management.
It follows clean code principles by keeping files focused and under 250 lines.

Usage:
    from test_runner import TestRunner
    runner = TestRunner()
    runner.run_all_tests()
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Add the core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from test_helpers import TestConfig, TestResult, create_test_logger, cleanup_test_files


class TestRunner:
    """Handles test execution and reporting."""
    
    def __init__(self):
        self.config = TestConfig()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {}
        }
        self.log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
    
    def print_banner(self):
        """Print the test suite banner."""
        print("=" * 80)
        print("🚀 DEVELOPER TEST SUITE - COMPLETE END-TO-END TESTING")
        print("=" * 80)
        print("This script will test ALL functionalities of the RAG tool:")
        print("✅ Project setup and validation")
        print("✅ Embedding model compatibility") 
        print("✅ RAG index building")
        print("✅ Query processing and answer quality")
        print("✅ UI functionality (rebuild index, debug tools, chat)")
        print("✅ Comprehensive logging and reporting")
        print("=" * 80)
        print()
    
    def get_project_configuration(self) -> Dict[str, Any]:
        """Get project configuration with 1-minute timeout - asks questions but defaults if no input."""
        print("📋 PROJECT CONFIGURATION")
        print("-" * 40)
        
        # Ask about default project with timeout
        print("Do you want to use the default source project?")
        print("Default project: Android SampleResponsive")
        print("Location: /Users/macuser/WORK/Samples/Android/SampleResponsive")
        print("⏰ Timeout: 60 seconds (will use default if no input)")
        
        import threading
        import time
        
        # Default values
        project_dir = "/Users/macuser/WORK/Samples/Android/SampleResponsive"
        project_type = "android"
        
        # Ask for project directory with timeout
        user_input = None
        def get_input():
            nonlocal user_input
            user_input = input("Use default project? (y/n): ").lower().strip()
        
        input_thread = threading.Thread(target=get_input)
        input_thread.daemon = True
        input_thread.start()
        
        # Wait up to 60 seconds
        input_thread.join(timeout=60)
        
        if user_input is None:
            print("⏰ Timeout reached. Using default project.")
        elif user_input in ['y', 'yes']:
            print(f"✅ Using default project: {project_dir}")
        elif user_input in ['n', 'no']:
            print("⏰ Timeout reached. Using default project.")
        else:
            print("⏰ Invalid input. Using default project.")
        
        # Ask for project type with timeout
        print("\nSelect project type:")
        for key, value in self.config.project_types.items():
            print(f"  {key}. {value}")
        print("⏰ Timeout: 60 seconds (will use default if no input)")
        
        user_input = None
        def get_project_type_input():
            nonlocal user_input
            user_input = input("Enter project type (1-8): ").strip()
        
        input_thread = threading.Thread(target=get_project_type_input)
        input_thread.daemon = True
        input_thread.start()
        
        # Wait up to 60 seconds
        input_thread.join(timeout=60)
        
        if user_input is None:
            print("⏰ Timeout reached. Using default project type: android")
        elif user_input in self.config.project_types:
            project_type = self.config.project_types[user_input]
            print(f"✅ Using project type: {project_type}")
        else:
            print("⏰ Invalid input. Using default project type: android")
        
        # Import centralized model configuration
        import sys
        import os
        core_path = os.path.join(os.path.dirname(__file__), '..', '..', 'core')
        if core_path not in sys.path:
            sys.path.insert(0, core_path)
        
        from config.model_config import model_config
        
        return {
            "project_dir": project_dir,
            "project_type": project_type,
            "ollama_endpoint": model_config.get_ollama_endpoint(),
            "ollama_model": model_config.get_ollama_model(),
            "embedding_model": model_config.get_embedding_model(),
            "chunk_size": model_config.get_chunk_size(),
            "chunk_overlap": model_config.get_chunk_overlap(),
            "search_k": model_config.get_search_k()
        }
    
    def run_test(self, test_func, config: Dict[str, Any], test_name: str) -> TestResult:
        """Run a single test and return result."""
        result = TestResult(test_name)
        
        try:
            test_result = test_func(config)
            if isinstance(test_result, dict):
                result.details = test_result.get("details", {})
                result.status = test_result.get("status", "unknown")
                result.error = test_result.get("error")
            else:
                result.set_success()
        except Exception as e:
            result.set_failed(str(e))
        
        return result
    
    def generate_report(self, config: Dict[str, Any]):
        """Generate comprehensive test report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate text report
        report_file = os.path.join(self.log_dir, f"developer_test_report_{timestamp}.txt")
        with open(report_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("🚀 DEVELOPER TEST SUITE REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Timestamp: {self.results['timestamp']}\n")
            f.write(f"Project: {config['project_dir']}\n")
            f.write(f"Type: {config['project_type']}\n")
            f.write("=" * 80 + "\n\n")
            
            # Test results
            for test in self.results["tests"]:
                status_icon = "✅" if test.status == "success" else "❌"
                f.write(f"{status_icon} {test.test_name}: {test.status}\n")
                if test.error:
                    f.write(f"   Error: {test.error}\n")
                f.write("\n")
            
            # Summary
            f.write("=" * 80 + "\n")
            f.write("📊 SUMMARY\n")
            f.write("=" * 80 + "\n")
            total_tests = len(self.results["tests"])
            passed_tests = sum(1 for test in self.results["tests"] if test.status == "success")
            failed_tests = total_tests - passed_tests
            
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {passed_tests}\n")
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n")
            
            if failed_tests == 0:
                f.write("\n🎉 ALL TESTS PASSED! The RAG tool is ready to use.\n")
            else:
                f.write(f"\n⚠️  {failed_tests} tests failed. Please check the logs.\n")
        
        # Generate JSON report
        json_file = os.path.join(self.log_dir, f"developer_test_results_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump({
                "timestamp": self.results["timestamp"],
                "config": config,
                "tests": [test.to_dict() for test in self.results["tests"]],
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100
                }
            }, f, indent=2)
        
        print(f"\n📊 Reports generated:")
        print(f"   Text: {report_file}")
        print(f"   JSON: {json_file}")
    
    def print_summary(self):
        """Print test summary."""
        total_tests = len(self.results["tests"])
        passed_tests = sum(1 for test in self.results["tests"] if test.status == "success")
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! The RAG tool is ready to use.")
        else:
            print(f"\n⚠️  {failed_tests} tests failed. Please check the logs.")
        
        print("=" * 80) 