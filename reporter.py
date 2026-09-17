"""
reporter.py - Self-Healing Bug Hunter Rapor Üreticisi (HTML, Markdown, JSON)

Bu modül, otonom hata tespiti ve tamirat sonuçlarını Markdown, HTML ve JSON formatlarında dışa aktarır.
"""

import os
import json
from typing import List, Dict, Any
from tools import write_file

class BugReporter:
    """Hata ve tamirat sonuçlarını farklı formatlarda raporlayan sınıf."""

    @staticmethod
    def export_json(results: List[Dict[str, Any]], output_path: str = "bug_hunter_report.json"):
        """Sonuçları JSON formatında kaydeder."""
        export_data = []
        for item in results:
            bug = item["bug_report"]
            repro = item["test_reproduction"]
            fix = item["fix_result"]
            export_data.append({
                "bug_id": bug.bug_id,
                "title": bug.title,
                "file_path": bug.file_path,
                "bug_type": bug.bug_type,
                "severity": bug.severity,
                "initial_test_status": repro.initial_test_status,
                "final_test_status": fix.final_test_status,
                "pr_title": fix.pr_title
            })
        write_file(output_path, json.dumps(export_data, indent=2, ensure_ascii=False))
        return output_path

    @staticmethod
    def export_markdown(results: List[Dict[str, Any]], output_path: str = "bug_hunter_report.md"):
        """Sonuçları Markdown formatında kaydeder."""
        md_content = "# 🛡️ Self-Healing Bug Hunter Raporu\n\n"
        md_content += "| Hata ID | Başlık | Tür | Kritiklik | İlk Durum | Son Durum | PR Başlığı |\n"
        md_content += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        for item in results:
            bug = item["bug_report"]
            repro = item["test_reproduction"]
            fix = item["fix_result"]
            md_content += f"| `{bug.bug_id}` | {bug.title} | {bug.bug_type} | {bug.severity} | `{repro.initial_test_status}` | **`{fix.final_test_status}`** | {fix.pr_title} |\n"
        
        write_file(output_path, md_content)
        return output_path

    @staticmethod
    def export_html(results: List[Dict[str, Any]], output_path: str = "bug_hunter_report.html"):
        """Sonuçları şık bir HTML web raporu olarak kaydeder."""
        html = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Self-Healing Bug Hunter Raporu</title>
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
    <h1>🛡️ Self-Healing Bug Hunter Raporu</h1>
    <table>
        <thead>
            <tr>
                <th>Hata ID</th>
                <th>Başlık</th>
                <th>Tür</th>
                <th>Kritiklik</th>
                <th>İlk Durum</th>
                <th>Son Durum</th>
                <th>PR Başlığı</th>
            </tr>
        </thead>
        <tbody>
"""
        for item in results:
            bug = item["bug_report"]
            repro = item["test_reproduction"]
            fix = item["fix_result"]
            html += f"""
            <tr>
                <td><code>{bug.bug_id}</code></td>
                <td>{bug.title}</td>
                <td>{bug.bug_type}</td>
                <td>{bug.severity}</td>
                <td><span class="badge badge-failed">{repro.initial_test_status}</span></td>
                <td><span class="badge badge-passed">{fix.final_test_status}</span></td>
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
