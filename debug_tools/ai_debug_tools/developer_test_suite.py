#!/usr/bin/env python3
"""
Developer Test Suite - Complete End-to-End Testing
===================================================

This is the ONE script that developers should run to verify all functionalities
of the RAG tool before using the UI. It follows clean code principles by using
focused modules and keeping files under 250 lines.

Usage:
    python developer_test_suite.py
"""

import os
import sys
from typing import Dict, Any

# Add the core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from test_runner import TestRunner
from test_suite import TestSuite
from ui_tests import UITests


class DeveloperTestSuite:
    """Complete end-to-end testing suite for developers."""
    
    def __init__(self):
        self.runner = TestRunner()
        self.test_suite = TestSuite()
        self.ui_tests = UITests()
    
    def run_complete_test_suite(self):
        """Run the complete test suite."""
        # Print banner
        self.runner.print_banner()
        
        # Get project configuration
        config = self.runner.get_project_configuration()
        
        # Run all tests
        tests = [
            ("Project Setup", self.test_suite.test_project_setup),
            ("Ollama Connectivity", self.test_suite.test_ollama_connectivity),
            ("Embedding Dimension Fix", self.test_suite.test_embedding_dimension_fix),
            ("RAG Building", self.test_suite.test_rag_building),
            ("Query Processing", self.test_suite.test_query_processing),
            ("UI App Functionality", self.test_suite.test_ui_app_functionality),
            ("UI Functionality", self.ui_tests.test_ui_functionality)
        ]
        
        # Execute tests
        for test_name, test_func in tests:
            print(f"\n{'='*80}")
            print(f"Running: {test_name}")
            print(f"{'='*80}")
            
            result = self.runner.run_test(test_func, config, test_name)
            self.runner.results["tests"].append(result)
            
            # Print immediate result
            status_icon = "✅" if result.status == "success" else "❌"
            print(f"{status_icon} {test_name}: {result.status}")
            if result.error:
                print(f"   Error: {result.error}")
        
        # Generate reports
        self.runner.generate_report(config)
        self.runner.print_summary()


def main():
    """Main entry point."""
    try:
        suite = DeveloperTestSuite()
        suite.run_complete_test_suite()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 