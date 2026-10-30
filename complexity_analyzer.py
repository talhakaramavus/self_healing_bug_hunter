"""
complexity_analyzer.py - Cyclomatic Complexity & Refactoring Analyzer

This module computes McCabe Cyclomatic Complexity on Python codebases using AST analysis.
Identifies overly complex functions, high cognitive branching, and provides 
refactoring recommendations to reduce technical debt.
"""

import ast
import os
from typing import List, Dict, Any

class ComplexityAnalyzer:
    """Calculates Cyclomatic Complexity of functions and classes."""

    DEFAULT_COMPLEXITY_THRESHOLD = 10

    @classmethod
    def analyze_file(cls, file_path: str, threshold: int = DEFAULT_COMPLEXITY_THRESHOLD) -> List[Dict[str, Any]]:
        """
        Parses Python file AST and discovers functions exceeding complexity threshold.

        :param file_path: Path to Python source file
        :param threshold: Cyclomatic complexity threshold (default: 10)
        :return: List of complexity issue dictionaries
        """
        if not os.path.exists(file_path) or not file_path.endswith(".py"):
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
        except Exception:
            return []

        visitor = FunctionComplexityVisitor(file_path, threshold)
        visitor.visit(tree)
        return visitor.issues


class FunctionComplexityVisitor(ast.NodeVisitor):
    """Measures Cyclomatic Complexity for each function or method definition."""

    def __init__(self, file_path: str, threshold: int):
        self.file_path = file_path
        self.threshold = threshold
        self.issues: List[Dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._calculate_and_record(node, node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._calculate_and_record(node, node.name)
        self.generic_visit(node)

    def _calculate_and_record(self, node: ast.AST, func_name: str):
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Branching statements
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Count additional conditions in 'and' / 'or'
                complexity += len(child.values) - 1

        if complexity > self.threshold:
            severity = "HIGH" if complexity > 15 else "MEDIUM"
            self.issues.append({
                "bug_id": f"COMPLEXITY-{node.lineno}",
                "file_path": self.file_path,
                "title": f"High Cyclomatic Complexity: '{func_name}()' (Score: {complexity})",
                "description": (
                    f"Function '{func_name}' at line {node.lineno} has a cyclomatic complexity of {complexity} "
                    f"(exceeds threshold of {self.threshold}). Highly nested branches increase maintenance risk."
                ),
                "bug_type": "Complexity",
                "severity": severity,
                "suggested_reproduction": (
                    f"Refactor '{func_name}' into smaller helper functions with early returns."
                )
            })
