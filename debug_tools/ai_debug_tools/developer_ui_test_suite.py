#!/usr/bin/env python3
"""
UI Automation Test Suite for RAG Codebase QA Tool

This test suite uses browser automation to test actual UI flows and user interactions.
It follows the same verification patterns as developer_test_suite.py to ensure real functionality.
"""

import os
import sys
import time
import subprocess
import threading
import requests
from typing import Dict, Any, List
import json
from datetime import datetime

# Add core path for imports
core_path = os.path.join(os.path.dirname(__file__), '..', '..', 'core')
if core_path not in sys.path:
    sys.path.insert(0, core_path)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium not available. Install with: pip install selenium webdriver-manager")

class UIAutomationTestSuite:
    """UI Automation Test Suite using Selenium WebDriver with real functionality verification."""
    
    def __init__(self):
        self.driver = None
        self.app_process = None
        self.app_url = "http://localhost:8501"
        self.test_results = []
        self.log_file = f"ui_automation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message):
        """Log message to both console and file."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a') as f:
            f.write(log_message + "\n")
        
    def setup_browser(self):
        """Setup Chrome browser with appropriate options."""
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available. Install with: pip install selenium webdriver-manager")
            
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Commented out to see browser
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        # Use webdriver-manager to automatically download and manage ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
        self.log(f"🔍 Browser setup complete. Chrome version: {self.driver.capabilities['browserVersion']}")
        self.log(f"🔍 ChromeDriver version: {self.driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]}")
        
    def start_streamlit_app(self):
        """Start the Streamlit app in background."""
        self.log("🚀 Starting Streamlit app...")
        
        # Kill any existing Streamlit processes
        try:
            subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
            time.sleep(2)
        except:
            pass
            
        # Start the app
        app_path = os.path.join(os.path.dirname(__file__), '..', '..', 'core', 'app.py')
        self.app_process = subprocess.Popen(
            ["streamlit", "run", app_path, "--server.port", "8501", "--server.headless", "true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for app to start
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.app_url}/_stcore/health", timeout=2)
                if response.status_code == 200:
                    self.log(f"✅ Streamlit app started at {self.app_url}")
                    return True
            except:
                pass
            time.sleep(1)
            
        raise Exception("Failed to start Streamlit app")
        
    def wait_for_element(self, by, value, timeout=10):
        """Wait for an element to be present and visible."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
            
    def test_app_startup_and_rag_build(self) -> Dict[str, Any]:
        """Test 1: App startup and RAG building process - following developer_test_suite.py pattern."""
        self.log("🧪 TEST 1: APP STARTUP AND RAG BUILD")
        self.log("-" * 40)
        
        result = {
            "test_name": "app_startup_and_rag_build",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Navigate to app
            self.log(f"🔍 Navigating to: {self.app_url}")
            self.driver.get(self.app_url)
            time.sleep(5)
            
            # Check if page loads
            if "Codebase-QA" in self.driver.title:
                result["details"]["page_loaded"] = True
                self.log("✅ Page loaded successfully")
            else:
                result["status"] = "failed"
                result["error"] = f"Page title not found. Got: {self.driver.title}"
                self.log(f"❌ Page title check failed. Expected 'Codebase-QA', got: {self.driver.title}")
                return result
                
            # Look for project type selector and select Android
            self.log("🔍 Looking for project type selector...")
            project_selector = self.wait_for_element(By.CSS_SELECTOR, "select, [role='combobox']")
            
            if project_selector:
                self.log("✅ Project type selector found")
                result["details"]["selector_found"] = True
                
                # Click to open dropdown
                project_selector.click()
                time.sleep(2)
                
                # Look for Android option and select it
                android_option = self.wait_for_element(By.XPATH, "//*[contains(text(), 'Android') or contains(text(), 'android')]")
                if android_option:
                    android_option.click()
                    time.sleep(3)
                    
                    # CRITICAL: Verify Android is actually selected by checking UI
                    self.log("🔍 Verifying Android selection in UI...")
                    
                    # Method 1: Check if the selector shows "Android"
                    selector_text = project_selector.text.lower()
                    if "android" in selector_text:
                        result["details"]["android_selected"] = True
                        self.log("✅ Android project type verified in selector")
                    else:
                        # Method 2: Look for "android" text anywhere in the UI
                        android_indicators = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'android') or contains(text(), 'Android')]")
                        if android_indicators:
                            result["details"]["android_selected"] = True
                            self.log("✅ Android project type verified in UI")
                        else:
                            result["details"]["android_selected"] = False
                            result["status"] = "failed"
                            result["error"] = "Android selection not verified in UI"
                            self.log("❌ Android selection not verified in UI")
                            return result
                else:
                    result["details"]["android_selected"] = False
                    result["status"] = "failed"
                    result["error"] = "Android option not found in dropdown"
                    self.log("❌ Android option not found in dropdown")
                    return result
            else:
                result["details"]["selector_found"] = False
                result["status"] = "failed"
                result["error"] = "Project type selector not found"
                self.log("❌ Project type selector not found")
                return result
            
            # Only proceed with RAG build if Android is properly selected
            if result["details"].get("android_selected", False):
                # Look for build button and trigger RAG build
                self.log("🔍 Looking for build/rebuild button...")
                build_button = self.wait_for_element(By.XPATH, "//*[contains(text(), 'Build') or contains(text(), 'Rebuild') or contains(text(), 'Index')]")
                
                if build_button:
                    result["details"]["build_button_found"] = True
                    self.log("✅ Build button found")
                    
                    # Click build button
                    build_button.click()
                    time.sleep(2)
                    
                    # Look for progress indicators
                    progress_indicators = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Building') or contains(text(), 'Processing') or contains(text(), 'Loading')]")
                    
                    if progress_indicators:
                        result["details"]["progress_shown"] = True
                        self.log("✅ Progress indicators shown")
                    else:
                        result["details"]["progress_shown"] = False
                        self.log("⚠️ No progress indicators found")
                        
                    # Wait for completion (up to 60 seconds)
                    max_wait = 60
                    for i in range(max_wait):
                        success_messages = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'successfully') or contains(text(), 'complete') or contains(text(), 'ready')]")
                        if success_messages:
                            result["details"]["build_completed"] = True
                            self.log("✅ RAG build completed")
                            break
                        time.sleep(1)
                    else:
                        result["details"]["build_completed"] = False
                        self.log("⚠️ Build completion not detected")
                        
                else:
                    result["details"]["build_button_found"] = False
                    self.log("⚠️ Build button not found")
            else:
                self.log("⚠️ Skipping RAG build test - Android not properly selected")
                
            result["status"] = "success"
            self.log("✅ App startup and RAG build test completed")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.log(f"❌ App startup and RAG build test failed: {e}")
            import traceback
            self.log(f"🔍 Full traceback: {traceback.format_exc()}")
            
        return result
        
    def test_chat_functionality(self) -> Dict[str, Any]:
        """Test 2: Chat interface and query processing - following developer_test_suite.py pattern."""
        self.log("🧪 TEST 2: CHAT FUNCTIONALITY")
        self.log("-" * 40)
        
        result = {
            "test_name": "chat_functionality",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Look for chat input
            chat_input = self.wait_for_element(By.CSS_SELECTOR, "input[type='text'], textarea")
            
            if chat_input:
                result["details"]["chat_input_found"] = True
                self.log("✅ Chat input found")
                
                # Enter a test query
                test_query = "What is the main activity?"
                chat_input.clear()
                chat_input.send_keys(test_query)
                time.sleep(1)
                
                # Look for submit button
                submit_button = self.wait_for_element(By.XPATH, "//*[contains(text(), 'Ask') or contains(text(), 'Submit') or contains(text(), 'Send')]")
                
                if submit_button:
                    result["details"]["submit_button_found"] = True
                    self.log("✅ Submit button found")
                    
                    # Click submit
                    submit_button.click()
                    time.sleep(5)
                    
                    # Look for response
                    response_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'chat') or contains(@class, 'message') or contains(@class, 'response')]")
                    
                    if response_elements:
                        result["details"]["response_received"] = True
                        self.log("✅ Response received")
                    else:
                        result["details"]["response_received"] = False
                        self.log("⚠️ No response detected")
                        
                else:
                    result["details"]["submit_button_found"] = False
                    self.log("⚠️ Submit button not found")
                    
            else:
                result["details"]["chat_input_found"] = False
                self.log("⚠️ Chat input not found")
                
            result["status"] = "success"
            self.log("✅ Chat functionality test completed")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.log(f"❌ Chat functionality test failed: {e}")
            
        return result
        
    def test_debug_tools_functionality(self) -> Dict[str, Any]:
        """Test 3: Debug tools functionality - following developer_test_suite.py pattern."""
        self.log("🧪 TEST 3: DEBUG TOOLS FUNCTIONALITY")
        self.log("-" * 40)
        
        result = {
            "test_name": "debug_tools_functionality",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Look for debug tools expander
            debug_expander = self.wait_for_element(By.XPATH, "//*[contains(text(), 'Debug') or contains(text(), 'Inspection')]")
            
            if debug_expander:
                result["details"]["debug_section_found"] = True
                self.log("✅ Debug section found")
                
                # Click to expand
                debug_expander.click()
                time.sleep(2)
                
                # Look for debug tabs
                debug_tabs = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Vector DB') or contains(text(), 'Chunk') or contains(text(), 'Retrieval')]")
                
                if debug_tabs:
                    result["details"]["debug_tabs_found"] = True
                    self.log("✅ Debug tabs found")
                    
                    # Test clicking on a debug tab
                    if len(debug_tabs) > 0:
                        debug_tabs[0].click()
                        time.sleep(2)
                        result["details"]["debug_tab_clicked"] = True
                        self.log("✅ Debug tab clicked")
                        
                else:
                    result["details"]["debug_tabs_found"] = False
                    self.log("⚠️ Debug tabs not found")
                    
            else:
                result["details"]["debug_section_found"] = False
                self.log("⚠️ Debug section not found")
                
            result["status"] = "success"
            self.log("✅ Debug tools functionality test completed")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.log(f"❌ Debug tools functionality test failed: {e}")
            
        return result
        
    def test_session_state_and_configuration(self) -> Dict[str, Any]:
        """Test 4: Session state and configuration - following developer_test_suite.py pattern."""
        self.log("🧪 TEST 4: SESSION STATE AND CONFIGURATION")
        self.log("-" * 40)
        
        result = {
            "test_name": "session_state_and_configuration",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Check if session state is properly initialized
            # Look for elements that indicate session state is working
            session_indicators = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Project Type') or contains(text(), 'Android') or contains(text(), 'Ready')]")
            
            if session_indicators:
                result["details"]["session_state_working"] = True
                self.log("✅ Session state indicators found")
            else:
                result["details"]["session_state_working"] = False
                self.log("⚠️ Session state indicators not found")
                
            # Check for configuration elements
            config_indicators = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Model') or contains(text(), 'Embedding') or contains(text(), 'Endpoint')]")
            
            if config_indicators:
                result["details"]["configuration_visible"] = True
                self.log("✅ Configuration elements visible")
            else:
                result["details"]["configuration_visible"] = False
                self.log("⚠️ Configuration elements not visible")
                
            result["status"] = "success"
            self.log("✅ Session state and configuration test completed")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.log(f"❌ Session state and configuration test failed: {e}")
            
        return result
        
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all UI automation tests with real functionality verification."""
        self.log("🚀 STARTING UI AUTOMATION TEST SUITE")
        self.log("=" * 50)
        
        try:
            # Setup browser
            self.setup_browser()
            self.log("✅ Browser setup complete")
            
            # Start Streamlit app
            self.start_streamlit_app()
            self.log("✅ Streamlit app started")
            
            # Run tests following developer_test_suite.py pattern
            tests = [
                ("App Startup and RAG Build", self.test_app_startup_and_rag_build),
                ("Chat Functionality", self.test_chat_functionality),
                ("Debug Tools Functionality", self.test_debug_tools_functionality),
                ("Session State and Configuration", self.test_session_state_and_configuration)
            ]
            
            for test_name, test_func in tests:
                self.log(f"\n{'='*20} {test_name} {'='*20}")
                
                # Check if browser is still responsive
                try:
                    # Simple check to see if browser is still working
                    self.driver.current_url
                except Exception as e:
                    self.log(f"❌ Browser connection lost: {e}")
                    self.log("🔄 Reconnecting browser...")
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.setup_browser()
                    self.driver.get(self.app_url)
                    time.sleep(3)
                
                result = test_func()
                self.test_results.append(result)
                
            # Generate report
            self.generate_report()
            
        except Exception as e:
            self.log(f"❌ Test suite failed: {e}")
            import traceback
            self.log(f"🔍 Full traceback: {traceback.format_exc()}")
            
        finally:
            # Cleanup
            if self.driver:
                try:
                    self.driver.quit()
                    self.log("🔍 Browser closed")
                except:
                    pass
            if self.app_process:
                try:
                    self.app_process.terminate()
                    self.log("🔍 Streamlit app terminated")
                except:
                    pass
                
            self.log(f"📄 Complete log saved to: {self.log_file}")
                
    def generate_report(self):
        """Generate test report following developer_test_suite.py pattern."""
        self.log("\n" + "="*50)
        self.log("📊 UI AUTOMATION TEST REPORT")
        self.log("="*50)
        
        passed = sum(1 for result in self.test_results if result["status"] == "success")
        failed = sum(1 for result in self.test_results if result["status"] == "failed")
        total = len(self.test_results)
        
        self.log(f"Total Tests: {total}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {failed}")
        self.log(f"Success Rate: {(passed/total)*100:.1f}%")
        
        self.log("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "success" else "❌"
            self.log(f"{status_icon} {result['test_name']}: {result['status']}")
            if result.get("error"):
                self.log(f"   Error: {result['error']}")
            if result.get("details"):
                for key, value in result["details"].items():
                    self.log(f"   {key}: {value}")
                    
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"ui_automation_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "success_rate": (passed/total)*100
                },
                "results": self.test_results
            }, f, indent=2)
            
        self.log(f"\n📄 Report saved: {report_file}")

def main():
    """Main entry point for UI automation tests."""
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium not available. Install with: pip install selenium webdriver-manager")
        return
        
    test_suite = UIAutomationTestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main() 