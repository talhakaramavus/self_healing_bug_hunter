"""
test_bug_hunter.py - Self-Healing Bug Hunter Test Suite

This module tests the core data models, tools, report exporters,
static analyzer, multi-language detection, PR creator, and Dashboard state.
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
from dashboard import DASHBOARD_STATE, load_initial_reports
from snapshot_manager import SnapshotManager
from complexity_analyzer import ComplexityAnalyzer
from hook_manager import HookManager

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

def test_dashboard_state_loading():
    """Tests that dashboard initializes state and metrics correctly."""
    load_initial_reports()
    assert isinstance(DASHBOARD_STATE, dict)
    assert "metrics" in DASHBOARD_STATE
    assert "results" in DASHBOARD_STATE
    assert "is_running" in DASHBOARD_STATE
    assert DASHBOARD_STATE["is_running"] is False

def test_snapshot_manager(tmp_path):
    """Tests snapshot creation, file modification, and safe rollback."""
    test_file = tmp_path / "code.py"
    original_content = "def calculate(): return 42\n"
    write_file(str(test_file), original_content)

    mgr = SnapshotManager(base_dir=str(tmp_path))
    snap_id = mgr.create_snapshot([str(test_file)])

    # Modify file
    write_file(str(test_file), "def calculate(): return 'corrupted'\n")
    assert read_file(str(test_file)) != original_content

    # Roll back
    success = mgr.restore_snapshot(snap_id)
    assert success is True
    assert read_file(str(test_file)) == original_content

    # Cleanup
    mgr.cleanup_snapshot(snap_id)

def test_complexity_analyzer(tmp_path):
    """Tests detection of functions with cyclomatic complexity exceeding threshold."""
    complex_code = """
def nested_branches(x):
    if x > 1:
        if x > 2:
            if x > 3:
                for i in range(x):
                    while i > 0:
                        if i == 5:
                            return True
                        elif i == 6:
                            return False
    return None
"""
    test_file = tmp_path / "complex.py"
    write_file(str(test_file), complex_code)

    issues = ComplexityAnalyzer.analyze_file(str(test_file), threshold=5)
    assert len(issues) >= 1
    assert issues[0]["bug_type"] == "Complexity"
    assert "Score:" in issues[0]["title"]

def test_hook_manager(tmp_path):
    """Tests installation and uninstallation of git pre-commit hook."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    # Install hook
    ok, msg = HookManager.install_pre_commit_hook(str(tmp_path))
    assert ok is True
    hook_file = tmp_path / ".git" / "hooks" / "pre-commit"
    assert hook_file.exists()
    assert "Self-Healing Bug Hunter" in hook_file.read_text(encoding="utf-8")

    # Uninstall hook
    ok, msg = HookManager.uninstall_pre_commit_hook(str(tmp_path))
    assert ok is True
    assert not hook_file.exists()
