"""
test_bug_hunter.py - Self-Healing Bug Hunter Test Paketi

Bu modül, altyapıdaki araçların, veri modellerinin ve raporlama bileşenlerinin doğruluğunu test eder.
"""

import os
import pytest
from config import BugReport, TestReproduction, FixResult
from tools import read_file, write_file, get_python_files
from reporter import BugReporter

def test_data_models():
    """BugReport ve FixResult nesnelerinin oluşturulmasını test eder."""
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
    """Dosya okuma ve yazma araçlarını test eder."""
    test_file = tmp_path / "sample.txt"
    content = "Hello Self-Healing Bug Hunter"
    write_file(str(test_file), content)
    
    assert os.path.exists(test_file)
    assert read_file(str(test_file)) == content

def test_reporter_export(tmp_path):
    """HTML ve Markdown rapor dışa aktarma işlevlerini test eder."""
    bug = BugReport("BUG-01", "app.py", "Null Pointer", "Null check missing", "Logic", "HIGH", "repro")
    repro = TestReproduction("BUG-01", "test_app.py", "def test(): pass", "FAILED", "Error log")
    fix = FixResult("BUG-01", "app.py", "patched code", "PASSED", "fix: null check", "PR body")
    
    results = [{"bug_report": bug, "test_reproduction": repro, "fix_result": fix}]
    
    json_path = str(tmp_path / "report.json")
    md_path = str(tmp_path / "report.md")
    html_path = str(tmp_path / "report.html")

    BugReporter.export_json(results, json_path)
    BugReporter.export_markdown(results, md_path)
    BugReporter.export_html(results, html_path)

    assert os.path.exists(json_path)
    assert os.path.exists(md_path)
    assert os.path.exists(html_path)
