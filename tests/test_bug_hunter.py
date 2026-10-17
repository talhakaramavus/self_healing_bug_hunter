"""
test_bug_hunter.py - Self-Healing Bug Hunter Test Suite

This module tests the core data models, tools, report exporters,
static analyzer, multi-language detection, and PR creator.
"""

import os
import sys
import pytest

# Ensure parent directory is in sys.path for cross-platform imports in CI environments
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import BugReport, TestReproduction, FixResult, VerificationResult
from tools import read_file, write_file, get_python_files
from reporter import BugReporter
from static_analyzer import StaticAnalyzer
from multi_language import MultiLanguageManager, LanguageConfig
from pr_creator import PullRequestCreator

def test_data_models():
    """Tests instantiation of core dataclass models."""
    report = BugReport(
        bug_id="BUG-TEST",
        file_path="sample.py",
        title="Test Bug",
        description="Sample description",
        bug_type="Logic",
        severity="HIGH",
        suggested_reproduction="Run test"
    )
    assert report.bug_id == "BUG-TEST"
    assert report.severity == "HIGH"

def test_file_tools(tmp_path):
    """Tests file reading and writing utilities."""
    test_file = tmp_path / "sample.txt"
    content = "Hello Self-Healing Bug Hunter"
    write_file(str(test_file), content)
    
    assert os.path.exists(test_file)
    assert read_file(str(test_file)) == content

def test_reporter_export(tmp_path):
    """Tests HTML, Markdown, and JSON report exporters with 4-agent verification data."""
    bug = BugReport("BUG-01", "app.py", "Null Pointer", "Null check missing", "Logic", "HIGH", "repro")
    repro = TestReproduction("BUG-01", "test_app.py", "def test(): pass", "FAILED", "Error log")
    fix = FixResult("BUG-01", "app.py", "patched code", "PASSED", "fix: null check", "PR body")
    ver = VerificationResult("BUG-01", True, 95, True, False, "PASSED", "Clean audit notes")
    
    results = [{"bug_report": bug, "test_reproduction": repro, "fix_result": fix, "verification_result": ver}]
    
    json_path = str(tmp_path / "report.json")
    md_path = str(tmp_path / "report.md")
    html_path = str(tmp_path / "report.html")

    BugReporter.export_json(results, json_path)
    BugReporter.export_markdown(results, md_path)
    BugReporter.export_html(results, html_path)

    assert os.path.exists(json_path)
    assert os.path.exists(md_path)
    assert os.path.exists(html_path)

def test_static_analyzer(tmp_path):
    """Tests AST static analyzer for dangerous calls and zero divisions."""
    buggy_code = """
def bad_func():
    eval("1 + 1")
    return 10 / 0
"""
    code_file = tmp_path / "unsafe.py"
    write_file(str(code_file), buggy_code)

    issues = StaticAnalyzer.analyze_file(str(code_file))
    assert len(issues) >= 2
    types = [i["bug_type"] for i in issues]
    assert "Security" in types
    assert "Logic" in types

def test_multi_language_detection(tmp_path):
    """Tests codebase multi-language detection across python, javascript, and go."""
    write_file(str(tmp_path / "service.py"), "print('hello')")
    write_file(str(tmp_path / "app.ts"), "const x: number = 42;")
    write_file(str(tmp_path / "main.go"), "package main")

    langs = MultiLanguageManager.detect_project_languages(str(tmp_path))
    assert LanguageConfig.PYTHON in langs
    assert LanguageConfig.TYPESCRIPT in langs
    assert LanguageConfig.GO in langs

def test_pr_creator_skipped_when_unaccepted():
    """Tests PR creator skips unaccepted patches."""
    fix = FixResult("BUG-02", "app.py", "patch", "FAILED", "fix: title", "body")
    ver = VerificationResult("BUG-02", False, 30, False, True, "FAILED", "Scope leak detected")
    
    res = PullRequestCreator.create_pr_for_fix(fix, ver)
    assert res.status == "SKIPPED"
    assert res.commit_sha is None
