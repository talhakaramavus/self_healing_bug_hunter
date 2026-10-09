"""
reporter.py - Self-Healing Bug Hunter Report Exporter (HTML, Markdown, JSON)

This module exports bug discovery and resolution results to Markdown, HTML, and JSON reports.
"""

import os
import json
from typing import List, Dict, Any
from tools import write_file

class BugReporter:
    """Exports bug reports and verification metrics in multiple formats."""

    @staticmethod
    def export_json(results: List[Dict[str, Any]], output_path: str = "bug_hunter_report.json"):
        """Exports pipeline results to JSON format."""
        export_data = []
        for item in results:
            bug = item["bug_report"]
            repro = item["test_reproduction"]
            fix = item["fix_result"]
            ver = item["verification_result"]
            export_data.append({
                "bug_id": bug.bug_id,
                "title": bug.title,
                "file_path": bug.file_path,
                "bug_type": bug.bug_type,
                "severity": bug.severity,
                "initial_test_status": repro.initial_test_status,
                "final_test_status": fix.final_test_status,
                "is_accepted": ver.is_accepted,
                "security_score": ver.security_score,
                "pr_title": fix.pr_title
            })
        write_file(output_path, json.dumps(export_data, indent=2, ensure_ascii=False))
        return output_path

    @staticmethod
    def export_markdown(results: List[Dict[str, Any]], output_path: str = "bug_hunter_report.md"):
        """Exports pipeline results to Markdown format."""
        md_content = "# 🛡️ Self-Healing Bug Hunter Report\n\n"
        md_content += "| Bug ID | Title | Type | Severity | Initial Test | Final Status | Verification | PR Title |\n"
        md_content += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        for item in results:
            bug = item["bug_report"]
            repro = item["test_reproduction"]
            fix = item["fix_result"]
            ver = item["verification_result"]
            accepted = "ACCEPTED" if ver.is_accepted else "REJECTED"
            md_content += f"| `{bug.bug_id}` | {bug.title} | {bug.bug_type} | {bug.severity} | `{repro.initial_test_status}` | **`{fix.final_test_status}`** | `{accepted}` ({ver.security_score}/100) | {fix.pr_title} |\n"
        
        write_file(output_path, md_content)
        return output_path

    @staticmethod
    def export_html(results: List[Dict[str, Any]], output_path: str = "bug_hunter_report.html"):
        """Exports pipeline results to a modern HTML web report."""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Self-Healing Bug Hunter Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 30px; }
        h1 { color: #38bdf8; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #1e293b; border-radius: 8px; overflow: hidden; }
        th, td { padding: 14px 16px; text-align: left; border-bottom: 1px solid #334155; }
        th { background: #334155; color: #94a3b8; }
        .badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
        .badge-passed { background: #166534; color: #4ade80; }
        .badge-failed { background: #991b1b; color: #fca5a5; }
    </style>
</head>
<body>
    <h1>🛡️ Self-Healing Bug Hunter Report</h1>
    <table>
        <thead>
            <tr>
                <th>Bug ID</th>
                <th>Title</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Initial Test</th>
                <th>Final Status</th>
                <th>Verification</th>
                <th>PR Title</th>
            </tr>
        </thead>
        <tbody>
"""
        for item in results:
            bug = item["bug_report"]
            repro = item["test_reproduction"]
            fix = item["fix_result"]
            ver = item["verification_result"]
            accepted = "ACCEPTED" if ver.is_accepted else "REJECTED"
            html += f"""
            <tr>
                <td><code>{bug.bug_id}</code></td>
                <td>{bug.title}</td>
                <td>{bug.bug_type}</td>
                <td>{bug.severity}</td>
                <td><span class="badge badge-failed">{repro.initial_test_status}</span></td>
                <td><span class="badge badge-passed">{fix.final_test_status}</span></td>
                <td><strong>{accepted}</strong> ({ver.security_score}/100)</td>
                <td>{fix.pr_title}</td>
            </tr>
"""
        html += """
        </tbody>
    </table>
</body>
</html>
"""
        write_file(output_path, html)
        return output_path
