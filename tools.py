"""
tools.py - Self-Healing Bug Hunter Tool Helpers

This module provides helper utilities for file reading, writing, and executing pytest suites.
"""

import os
import sys
import subprocess
from typing import Tuple, List

def read_file(file_path: str) -> str:
    """
    Reads the content of the specified file.
    
    :param file_path: Target file path
    :return: File content string
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """
    Writes content to specified file path (creates parent directories if needed).
    
    :param file_path: Target file path
    :param content: Content string to write
    """
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def get_python_files(target_dir: str) -> List[str]:
    """
    Lists all Python files in target directory (excluding test files).
    """
    py_files = []
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("test_") and not file.startswith("__"):
                py_files.append(os.path.join(root, file))
    return py_files


def run_pytest(test_file_path: str, timeout: int = 30) -> Tuple[bool, str]:
    """
    Executes a pytest test file as a subprocess.
    
    :param test_file_path: Target unit test file path
    :param timeout: Execution timeout in seconds
    :return: (is_passed: bool, output_log: str) tuple
    """
    if not os.path.exists(test_file_path):
        return False, f"Test file does not exist: {test_file_path}"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file_path, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        is_passed = (result.returncode == 0)
        output = result.stdout + "\n" + result.stderr
        return is_passed, output.strip()
    except subprocess.TimeoutExpired:
        return False, f"Test execution timed out ({timeout}s limit)."
    except Exception as e:
        return False, f"Unexpected error during test execution: {str(e)}"
