"""
multi_language.py - Multi-Language Project Scanner and Test Runner

This module enables multi-language codebase detection and test execution 
for Python (pytest), JavaScript/TypeScript (jest/npm), and Go (go test).
"""

import os
import sys
import subprocess
from typing import List, Dict, Tuple

class LanguageConfig:
    """Configuration per supported programming language."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"

class MultiLanguageManager:
    """Manages language detection and cross-language test execution."""

    @staticmethod
    def detect_project_languages(target_dir: str) -> List[str]:
        """
        Detects primary programming languages present in the target directory.
        """
        languages = set()
        for root, _, files in os.walk(target_dir):
            for f in files:
                if f.endswith(".py"):
                    languages.add(LanguageConfig.PYTHON)
                elif f.endswith(".js") or f.endswith(".jsx"):
                    languages.add(LanguageConfig.JAVASCRIPT)
                elif f.endswith(".ts") or f.endswith(".tsx"):
                    languages.add(LanguageConfig.TYPESCRIPT)
                elif f.endswith(".go"):
                    languages.add(LanguageConfig.GO)
        return list(languages) if languages else [LanguageConfig.PYTHON]

    @staticmethod
    def run_tests_for_language(language: str, target_dir: str, timeout: int = 30) -> Tuple[bool, str]:
        """
        Executes native test runner for the specified programming language.
        """
        try:
            if language == LanguageConfig.PYTHON:
                cmd = [sys.executable, "-m", "pytest", target_dir, "-v"]
            elif language in (LanguageConfig.JAVASCRIPT, LanguageConfig.TYPESCRIPT):
                cmd = ["npm", "test"] if os.path.exists(os.path.join(target_dir, "package.json")) else ["npx", "jest"]
            elif language == LanguageConfig.GO:
                cmd = ["go", "test", "./..."]
            else:
                return True, "Unsupported language test runner"

            result = subprocess.run(
                cmd,
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return (result.returncode == 0), (result.stdout + "\n" + result.stderr).strip()
        except Exception as e:
            return False, f"Error running {language} test suite: {str(e)}"
