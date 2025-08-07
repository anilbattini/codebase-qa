#!/usr/bin/env python3
"""
Comprehensive Test Runner
Runs all tests to diagnose quality issues, embedding problems, and answer relevance.
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Any

# Add the core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from quality_test_suite import QualityTestSuite
from embedding_dimension_test import EmbeddingDimensionTest

class ComprehensiveTestRunner:
    """Runs comprehensive tests for all identified issues."""
    
    def __init__(self, project_dir: str, ollama_model: str = "llama3.1", ollama_endpoint: str = "http://127.0.0.1:11434"):
        self.project_dir = project_dir
        self.ollama_model = ollama_model
        self.ollama_endpoint = ollama_endpoint
        self.results = {}
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests."""
        print("🚀 Comprehensive Test Runner")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test 1: Embedding Dimension Issue
        print("\n🔧 Test 1: Embedding Dimension Diagnosis")
        print("-" * 40)
        embedding_test = EmbeddingDimensionTest(self.project_dir, self.ollama_endpoint)
        embedding_results = embedding_test.run_complete_fix()
        self.results["embedding_dimension"] = embedding_results
        
        # Test 2: Quality Test Suite
        print("\n📊 Test 2: Quality Test Suite")
        print("-" * 40)
        quality_test = QualityTestSuite(self.project_dir, self.ollama_model, self.ollama_endpoint)
        quality_results = quality_test.run_comprehensive_test()
        self.results["quality_tests"] = quality_results
        
        # Test 3: Specific Question Tests
        print("\n❓ Test 3: Specific Question Tests")
        print("-" * 40)
        question_results = self._test_specific_questions(quality_test)
        self.results["specific_questions"] = question_results
        
        total_time = time.time() - start_time
        
        # Generate comprehensive report
        report = self._generate_report(total_time)
        
        # Save results
        self._save_results(report)
        
        return report
    
    def _test_specific_questions(self, quality_test: QualityTestSuite) -> Dict[str, Any]:
        """Test specific questions mentioned by the user."""
        questions = [
            {
                "question": "What is this codebase about?",
                "expected_rating": 4,
                "description": "Basic codebase overview"
            },
            {
                "question": "What is the impact if I want to change the flow skipping MainActivity and directly go to SettingsFragment?",
                "expected_rating": 4,
                "description": "Impact analysis question"
            },
            {
                "question": "What is the business logic in SettingsFragment?",
                "expected_rating": 4,
                "description": "Business logic question"
            },
            {
                "question": "What is the validation given to username in LoginScreen?",
                "expected_rating": 4,
                "description": "Validation question"
            },
            {
                "question": "List down the project directory file structure",
                "expected_rating": 4,
                "description": "File structure question"
            }
        ]
        
        results = {
            "test_name": "specific_questions",
            "timestamp": datetime.now().isoformat(),
            "questions": []
        }
        
        for q_data in questions:
            print(f"Testing: {q_data['question']}")
            try:
                result = quality_test.test_question_quality(
                    q_data["question"], 
                    q_data["expected_rating"]
                )
                result["description"] = q_data["description"]
                results["questions"].append(result)
                
                # Print quick summary
                satisfaction = result.get("details", {}).get("satisfaction_rating", 0)
                status = result.get("status", "unknown")
                print(f"  Status: {status}, Satisfaction: {satisfaction}/10")
                
            except Exception as e:
                error_result = {
                    "question": q_data["question"],
                    "status": "failed",
                    "error": str(e),
                    "description": q_data["description"]
                }
                results["questions"].append(error_result)
                print(f"  Status: failed, Error: {e}")
        
        return results
    
    def _generate_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_time": total_time,
            "project_dir": self.project_dir,
            "ollama_model": self.ollama_model,
            "ollama_endpoint": self.ollama_endpoint,
            "summary": {},
            "recommendations": [],
            "detailed_results": self.results
        }
        
        # Analyze embedding dimension results
        embedding_results = self.results.get("embedding_dimension", {})
        if embedding_results.get("recommendation"):
            report["summary"]["embedding_status"] = "fixed" if "✅" in embedding_results["recommendation"] else "needs_attention"
            report["recommendations"].append(embedding_results["recommendation"])
        
        # Analyze quality test results
        quality_results = self.results.get("quality_tests", {})
        quality_tests = quality_results.get("tests", [])
        
        successful_tests = sum(1 for test in quality_tests if test.get("status") == "success")
        total_tests = len(quality_tests)
        
        report["summary"]["quality_tests"] = {
            "total": total_tests,
            "successful": successful_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        # Analyze specific question results
        question_results = self.results.get("specific_questions", {})
        questions = question_results.get("questions", [])
        
        avg_satisfaction = 0
        successful_questions = 0
        
        for question in questions:
            if question.get("status") == "success":
                successful_questions += 1
                satisfaction = question.get("details", {}).get("satisfaction_rating", 0)
                avg_satisfaction += satisfaction
        
        if successful_questions > 0:
            avg_satisfaction /= successful_questions
        
        report["summary"]["question_quality"] = {
            "total_questions": len(questions),
            "successful_questions": successful_questions,
            "average_satisfaction": round(avg_satisfaction, 2),
            "success_rate": (successful_questions / len(questions) * 100) if questions else 0
        }
        
        # Generate recommendations
        if avg_satisfaction < 4:
            report["recommendations"].append("⚠️ Answer quality is below expected (4/10). Review query processing and context building.")
        
        if successful_questions < len(questions):
            report["recommendations"].append("⚠️ Some questions failed to process. Check error logs for details.")
        
        if report["summary"]["quality_tests"]["success_rate"] < 80:
            report["recommendations"].append("⚠️ Quality tests have low success rate. Review RAG building process.")
        
        return report
    
    def _save_results(self, report: Dict[str, Any]):
        """Save comprehensive results to file."""
        # Create results directory
        results_dir = os.path.join(self.project_dir, "debug_tools", "test_results")
        os.makedirs(results_dir, exist_ok=True)
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(results_dir, f"comprehensive_test_results_{timestamp}.json")
        
        with open(results_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: {results_file}")
        
        # Save summary report
        summary_file = os.path.join(results_dir, f"test_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write("COMPREHENSIVE TEST SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Timestamp: {report['timestamp']}\n")
            f.write(f"Total Time: {report['total_time']:.2f}s\n")
            f.write(f"Project: {report['project_dir']}\n")
            f.write(f"Model: {report['ollama_model']}\n\n")
            
            f.write("SUMMARY:\n")
            f.write("-" * 20 + "\n")
            
            # Embedding status
            embedding_status = report["summary"].get("embedding_status", "unknown")
            f.write(f"Embedding Status: {embedding_status}\n")
            
            # Quality tests
            quality_summary = report["summary"].get("quality_tests", {})
            f.write(f"Quality Tests: {quality_summary.get('successful', 0)}/{quality_summary.get('total', 0)} successful\n")
            
            # Question quality
            question_summary = report["summary"].get("question_quality", {})
            f.write(f"Question Quality: {question_summary.get('average_satisfaction', 0)}/10 average satisfaction\n")
            f.write(f"Questions Processed: {question_summary.get('successful_questions', 0)}/{question_summary.get('total_questions', 0)}\n\n")
            
            f.write("RECOMMENDATIONS:\n")
            f.write("-" * 20 + "\n")
            for rec in report.get("recommendations", []):
                f.write(f"• {rec}\n")
        
        print(f"📝 Summary saved to: {summary_file}")

def main():
    """Main function to run comprehensive tests."""
    print("🚀 Starting Comprehensive Test Runner")
    print("=" * 60)
    
    # Configuration
    project_dir = "../"  # Adjust as needed
    ollama_model = "llama3.1"
    ollama_endpoint = "http://127.0.0.1:11434"
    
    # Initialize test runner
    runner = ComprehensiveTestRunner(project_dir, ollama_model, ollama_endpoint)
    
    # Run all tests
    report = runner.run_all_tests()
    
    # Print final summary
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    
    print(f"⏱️  Total Time: {report['total_time']:.2f}s")
    print(f"🔧 Embedding Status: {report['summary'].get('embedding_status', 'unknown')}")
    
    quality_summary = report["summary"].get("quality_tests", {})
    print(f"📊 Quality Tests: {quality_summary.get('successful', 0)}/{quality_summary.get('total', 0)} successful")
    
    question_summary = report["summary"].get("question_quality", {})
    print(f"❓ Question Quality: {question_summary.get('average_satisfaction', 0)}/10 average satisfaction")
    print(f"✅ Questions Processed: {question_summary.get('successful_questions', 0)}/{question_summary.get('total_questions', 0)}")
    
    print("\n💡 RECOMMENDATIONS:")
    for rec in report.get("recommendations", []):
        print(f"  {rec}")
    
    print(f"\n📁 Results saved to: {project_dir}/debug_tools/test_results/")

if __name__ == "__main__":
    main() 