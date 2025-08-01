#!/usr/bin/env python3

import os
import sys
from build_rag import build_rag

def test_vector_db_location():
    """Test that codebase-qa_db is created in the source project directory, not in codebase-qa."""
    
    # Get the current directory (codebase-qa)
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Set project directory to parent (SampleResponsive)
    project_dir = os.path.abspath("..")
    print(f"Project directory: {project_dir}")
    
    # Check if codebase-qa_db exists in project_dir
    db_path = os.path.join(project_dir, "codebase-qa_db")
    print(f"Codebase-qa DB path: {db_path}")
    print(f"Codebase-qa DB exists: {os.path.exists(db_path)}")
    
    # Check if codebase-qa_db exists in current directory
    current_db = os.path.join(current_dir, "codebase-qa_db")
    print(f"Current dir codebase-qa_db: {current_db}")
    print(f"Current dir codebase-qa_db exists: {os.path.exists(current_db)}")
    
    # List contents of project directory
    print(f"\nProject directory contents:")
    for item in os.listdir(project_dir):
        print(f"  {item}")
    
    # List contents of current directory
    print(f"\nCurrent directory contents:")
    for item in os.listdir(current_dir):
        if "codebase-qa_db" in item or "vector_db" in item or "rag_logs" in item:
            print(f"  {item}")

if __name__ == "__main__":
    test_vector_db_location() 