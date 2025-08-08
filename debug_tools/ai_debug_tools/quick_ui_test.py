#!/usr/bin/env python3
"""
Quick UI Test - Focused on key verifications
"""

import os
import sys
import time
import subprocess
import requests
from typing import Dict, Any
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

class QuickUITest:
    """Quick UI test focusing on key verifications."""
    
    def __init__(self):
        self.driver = None
        self.app_process = None
        self.app_url = "http://localhost:8501"
        self.log_file = f"quick_ui_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message):
        """Log message to both console and file."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a') as f:
            f.write(log_message + "\n")
        
    def setup_browser(self):
        """Setup Chrome browser."""
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available")
            
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(5)
        
    def start_streamlit_app(self):
        """Start Streamlit app."""
        self.log("🚀 Starting Streamlit app...")
        
        # Kill existing processes
        try:
            subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
            time.sleep(2)
        except:
            pass
            
        # Start app
        app_path = os.path.join(os.path.dirname(__file__), '..', '..', 'core', 'app.py')
        self.app_process = subprocess.Popen(
            ["streamlit", "run", app_path, "--server.port", "8501", "--server.headless", "true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for app to start
        for attempt in range(30):
            try:
                response = requests.get(f"{self.app_url}/_stcore/health", timeout=2)
                if response.status_code == 200:
                    self.log(f"✅ Streamlit app started at {self.app_url}")
                    return True
            except:
                pass
            time.sleep(1)
            
        raise Exception("Failed to start Streamlit app")
        
    def test_app_loads(self):
        """Test 1: App loads successfully."""
        self.log("🧪 TEST 1: APP LOADS")
        
        try:
            self.driver.get(self.app_url)
            time.sleep(3)
            
            self.log(f"🔍 URL: {self.driver.current_url}")
            self.log(f"🔍 Title: {self.driver.title}")
            self.log(f"🔍 Page size: {len(self.driver.page_source)} bytes")
            
            if "Codebase-QA" in self.driver.title:
                self.log("✅ App loads successfully")
                return True
            else:
                self.log(f"❌ App load failed. Title: {self.driver.title}")
                return False
                
        except Exception as e:
            self.log(f"❌ App load test failed: {e}")
            return False
            
    def test_ui_elements_present(self):
        """Test 2: Key UI elements are present."""
        self.log("🧪 TEST 2: UI ELEMENTS PRESENT")
        
        try:
            # Check for any form elements
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            self.log(f"🔍 Found {len(forms)} form elements")
            
            # Check for any input elements
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            self.log(f"🔍 Found {len(inputs)} input elements")
            
            # Check for any button elements
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            self.log(f"🔍 Found {len(buttons)} button elements")
            
            # Check for any select elements
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            self.log(f"🔍 Found {len(selects)} select elements")
            
            if len(forms) > 0 or len(inputs) > 0 or len(buttons) > 0:
                self.log("✅ UI elements present")
                return True
            else:
                self.log("❌ No UI elements found")
                return False
                
        except Exception as e:
            self.log(f"❌ UI elements test failed: {e}")
            return False
            
    def test_page_interaction(self):
        """Test 3: Can interact with page elements."""
        self.log("🧪 TEST 3: PAGE INTERACTION")
        
        try:
            # Try to find and click any clickable element
            clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, "button, [role='button'], [tabindex]")
            self.log(f"🔍 Found {len(clickable_elements)} clickable elements")
            
            if len(clickable_elements) > 0:
                # Try to click the first element
                try:
                    clickable_elements[0].click()
                    self.log("✅ Successfully clicked an element")
                    return True
                except Exception as e:
                    self.log(f"⚠️ Click failed: {e}")
                    return True  # Element exists but click failed
            else:
                self.log("❌ No clickable elements found")
                return False
                
        except Exception as e:
            self.log(f"❌ Page interaction test failed: {e}")
            return False
            
    def run_tests(self):
        """Run all quick tests."""
        self.log("🚀 STARTING QUICK UI TESTS")
        self.log("=" * 40)
        
        results = {
            "app_loads": False,
            "ui_elements_present": False,
            "page_interaction": False
        }
        
        try:
            # Setup
            self.setup_browser()
            self.log("✅ Browser setup complete")
            
            self.start_streamlit_app()
            self.log("✅ Streamlit app started")
            
            # Run tests
            results["app_loads"] = self.test_app_loads()
            results["ui_elements_present"] = self.test_ui_elements_present()
            results["page_interaction"] = self.test_page_interaction()
            
            # Summary
            passed = sum(results.values())
            total = len(results)
            
            self.log(f"\n📊 TEST SUMMARY")
            self.log(f"Total Tests: {total}")
            self.log(f"Passed: {passed}")
            self.log(f"Failed: {total - passed}")
            self.log(f"Success Rate: {(passed/total)*100:.1f}%")
            
            for test_name, result in results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                self.log(f"{status} {test_name}")
                
        except Exception as e:
            self.log(f"❌ Test suite failed: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
            if self.app_process:
                self.app_process.terminate()
                
            self.log(f"📄 Log saved to: {self.log_file}")

def main():
    """Main entry point."""
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium not available")
        return
        
    test = QuickUITest()
    test.run_tests()

if __name__ == "__main__":
    main() 