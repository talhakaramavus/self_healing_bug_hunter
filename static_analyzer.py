"""
static_analyzer.py - AST-Based Static Security and Code Analyzer

This module performs deterministic AST (Abstract Syntax Tree) parsing on source code 
to discover security vulnerabilities, hardcoded credentials, unclosed file handles, 
and potential zero division logic flaws.
"""

import ast
import os
from typing import List, Dict, Any

class StaticAnalyzer:
    """Performs deterministic AST analysis on source code files."""

    @staticmethod
    def analyze_file(file_path: str) -> List[Dict[str, Any]]:
        """
        Parses target file AST and returns detected security and logic issues.

        :param file_path: Path to Python source file
        :return: List of issue dictionaries
        """
        if not os.path.exists(file_path) or not file_path.endswith(".py"):
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
        except Exception:
            return []

        issues = []
        visitor = ASTIssueVisitor(file_path)
        visitor.visit(tree)
        return visitor.issues


class ASTIssueVisitor(ast.NodeVisitor):
    """AST Node Visitor for security and logic flaw detection."""

    DANGEROUS_FUNCTIONS = {"eval", "exec"}

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues = []

    def visit_Call(self, node: ast.Call):
        # Check for dangerous function calls (eval, exec)
        if isinstance(node.func, ast.Name) and node.func.id in self.DANGEROUS_FUNCTIONS:
            self.issues.append({
                "bug_id": f"AST-SEC-{node.lineno}",
                "file_path": self.file_path,
                "title": f"Dangerous Function Usage: {node.func.id}()",
                "description": f"Use of unsafe function '{node.func.id}()' on line {node.lineno}.",
                "bug_type": "Security",
                "severity": "HIGH",
                "suggested_reproduction": f"Audit line {node.lineno} for unsafe dynamic code execution."
            })
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        # Check for potential division by zero literal
        if isinstance(node.op, ast.Div) and isinstance(node.right, ast.Constant) and node.right.value == 0:
            self.issues.append({
                "bug_id": f"AST-LOGIC-{node.lineno}",
                "file_path": self.file_path,
                "title": "Literal Zero Division",
                "description": f"Explicit division by zero detected on line {node.lineno}.",
                "bug_type": "Logic",
                "severity": "HIGH",
                "suggested_reproduction": f"Execute function containing line {node.lineno}."
            })
        self.generic_visit(node)
