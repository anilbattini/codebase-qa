#!/usr/bin/env python3
"""
Setup script for codebase-qa package.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="codebase-qa",
    version="0.1.0",
    author="Codebase QA Team",
    author_email="team@codebase-qa.com",
    description="A RAG-powered codebase question answering tool with Streamlit UI",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/codebase-qa/codebase-qa",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "codebase-qa=codebase_qa.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "codebase_qa": ["*.py", "debug_tools/*.py", "debug_tools/*.md"],
    },
    keywords="rag, codebase, qa, streamlit, langchain, ollama",
    project_urls={
        "Bug Reports": "https://github.com/codebase-qa/codebase-qa/issues",
        "Source": "https://github.com/codebase-qa/codebase-qa",
        "Documentation": "https://github.com/codebase-qa/codebase-qa#readme",
    },
) 