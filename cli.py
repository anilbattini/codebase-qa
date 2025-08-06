#!/usr/bin/env python3
"""
CLI entry point for codebase-qa.
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Codebase QA - RAG-powered codebase question answering tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  codebase-qa run                    # Run in current directory
  codebase-qa run /path/to/project  # Run for specific project
  codebase-qa run --port 8501       # Run on specific port
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run the Streamlit UI')
    run_parser.add_argument(
        'project_path',
        nargs='?',
        default='.',
        help='Path to the project directory (default: current directory)'
    )
    run_parser.add_argument(
        '--port',
        type=int,
        default=8501,
        help='Port to run the Streamlit app on (default: 8501)'
    )
    run_parser.add_argument(
        '--host',
        default='localhost',
        help='Host to bind to (default: localhost)'
    )
    run_parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode (no browser)'
    )
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'version':
        print("codebase-qa version 0.1.0")
        return 0
    
    elif args.command == 'run':
        return run_streamlit(args)
    
    return 0


def run_streamlit(args):
    """Run the Streamlit application."""
    # Resolve the project path
    project_path = os.path.abspath(args.project_path)
    
    if not os.path.exists(project_path):
        print(f"❌ Error: Project path '{project_path}' does not exist.")
        return 1
    
    if not os.path.isdir(project_path):
        print(f"❌ Error: Project path '{project_path}' is not a directory.")
        return 1
    
    # Find the codebase-qa directory (should be in the project or a subdirectory)
    codebase_qa_dir = find_codebase_qa_dir(project_path)
    
    if not codebase_qa_dir:
        print(f"❌ Error: Could not find codebase-qa directory in '{project_path}'")
        print("Make sure you're running from a directory that contains the codebase-qa tool.")
        return 1
    
    # Change to the codebase-qa directory
    os.chdir(codebase_qa_dir)
    
    # Build the streamlit command
    cmd = [
        sys.executable, "-m", "streamlit", "run", "core/app.py",
        "--server.port", str(args.port),
        "--server.address", args.host
    ]
    
    # Add headless mode if requested
    if args.headless:
        cmd.extend(["--server.headless", "true"])
    
    print(f"🚀 Starting Codebase QA for project: {project_path}")
    print(f"📁 Codebase QA directory: {codebase_qa_dir}")
    print(f"🌐 UI will be available at: http://{args.host}:{args.port}")
    print(f"📋 Command: {' '.join(cmd)}")
    print()
    
    try:
        # Set environment variable for the project path
        env = os.environ.copy()
        env['CODEBASE_QA_PROJECT_PATH'] = project_path
        
        # Run streamlit
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 Codebase QA stopped by user.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


def find_codebase_qa_dir(project_path):
    """Find the codebase-qa directory within the project."""
    # Look for codebase-qa directory in the project path
    possible_paths = [
        os.path.join(project_path, "codebase-qa"),
        os.path.join(project_path, "codebase-qa", "codebase-qa"),
        project_path,  # In case we're already in the codebase-qa directory
    ]
    
    for path in possible_paths:
        if os.path.exists(os.path.join(path, "app.py")):
            return path
    
    # If not found, look for any directory containing app.py
    for root, dirs, files in os.walk(project_path):
        if "app.py" in files:
            # Check if this looks like a codebase-qa directory
            if any(f in files for f in ["config.py", "rag_manager.py", "ui_components.py"]):
                return root
    
    return None


if __name__ == "__main__":
    sys.exit(main()) 