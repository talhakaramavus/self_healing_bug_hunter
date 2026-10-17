"""
dashboard.py - Self-Healing Bug Hunter Interactive Web Dashboard

A zero-dependency, real-time web dashboard powered by Python's built-in HTTP server.
Provides visual monitoring of the 4-agent pipeline, live benchmark metrics,
patch diff comparisons, and interactive pipeline execution.
"""

import os
import sys
import json
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any

from orchestrator import BugHunterOrchestrator
from reporter import BugReporter
from benchmark import BugHunterBenchmark

DASHBOARD_STATE = {
    "is_running": False,
    "last_run": None,
    "current_step": "Idle",
    "results": [],
    "metrics": {
        "total_bugs_scanned": 0,
        "true_positives": 0,
        "false_alarms": 0,
        "patch_acceptance_rate": 0.0,
        "total_token_cost_usd": 0.0,
        "avg_time_to_fix_seconds": 0.0,
        "total_duration_seconds": 0.0
    }
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Self-Healing Bug Hunter | Live Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #090d16;
            --card-bg: #111827;
            --border: #1f2937;
            --primary: #38bdf8;
            --primary-glow: rgba(56, 189, 248, 0.15);
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            padding: 24px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 24px;
        }
        .header-title {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .badge {
            background: var(--primary-glow);
            color: var(--primary);
            border: 1px solid var(--primary);
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
        }
        .btn-run {
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: #fff;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .btn-run:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
        }
        .btn-run:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            padding: 16px;
            border-radius: 12px;
        }
        .metric-label {
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 6px;
        }
        .metric-value {
            font-size: 26px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: var(--primary);
        }
        .pipeline-status {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }
        .status-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .agent-steps {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
        }
        .agent-step {
            background: #1f2937;
            padding: 14px;
            border-radius: 8px;
            border-left: 4px solid var(--border);
        }
        .agent-step.active {
            border-left-color: var(--primary);
            background: rgba(56, 189, 248, 0.08);
        }
        .agent-step.done {
            border-left-color: var(--success);
        }
        .agent-name {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 4px;
        }
        .agent-desc {
            font-size: 12px;
            color: var(--text-muted);
        }
        .results-section {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }
        .results-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 14px;
            font-size: 14px;
        }
        .results-table th, .results-table td {
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
            text-align: left;
        }
        .results-table th {
            color: var(--text-muted);
            font-weight: 600;
        }
        .status-pill {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .pill-passed { background: rgba(16, 185, 129, 0.15); color: var(--success); }
        .pill-failed { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
        pre {
            font-family: 'JetBrains Mono', monospace;
            background: #030712;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 12px;
            color: #e5e7eb;
            margin-top: 8px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-title">
            <h2>🛡️ Self-Healing Bug Hunter</h2>
            <span class="badge">4-Agent Autonomous System</span>
        </div>
        <button id="runBtn" class="btn-run" onclick="startHunt()">
            <span>⚡ Run Autonomous Pipeline</span>
        </button>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Bugs Scanned</div>
            <div class="metric-value" id="valBugs">0</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Patch Acceptance Rate</div>
            <div class="metric-value" id="valAcceptance">0%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg Time-to-Fix</div>
            <div class="metric-value" id="valTime">0.0s</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Estimated Token Cost</div>
            <div class="metric-value" id="valCost">$0.00</div>
        </div>
    </div>

    <div class="pipeline-status">
        <div class="status-header">
            <h3>4-Agent Pipeline Workflow</h3>
            <span id="pipelineStatus" style="color: var(--text-muted); font-size: 13px;">Status: Ready</span>
        </div>
        <div class="agent-steps">
            <div class="agent-step done" id="stepScout">
                <div class="agent-name">🔍 Scout Agent</div>
                <div class="agent-desc">AST & GenAI Code Scanning</div>
            </div>
            <div class="agent-step done" id="stepRepro">
                <div class="agent-name">🧪 Reproducer Agent</div>
                <div class="agent-desc">Generates Failing Pytest</div>
            </div>
            <div class="agent-step done" id="stepFix">
                <div class="agent-name">🛠️ Fixer Agent</div>
                <div class="agent-desc">Iterative Source Patching</div>
            </div>
            <div class="agent-step done" id="stepVer">
                <div class="agent-name">🛡️ Verifier Agent</div>
                <div class="agent-desc">Sandbox & Scope Security Audit</div>
            </div>
        </div>
    </div>

    <div class="results-section">
        <h3>Inspection & Patch Resolution Reports</h3>
        <table class="results-table">
            <thead>
                <tr>
                    <th>Bug ID</th>
                    <th>Title & Severity</th>
                    <th>Type</th>
                    <th>Initial Test</th>
                    <th>Final Status</th>
                    <th>Verifier Security</th>
                    <th>PR Title</th>
                </tr>
            </thead>
            <tbody id="resultsBody">
                <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No reports yet. Click 'Run Autonomous Pipeline' to start.</td></tr>
            </tbody>
        </table>
    </div>

    <script>
        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                
                document.getElementById('valBugs').innerText = data.metrics.total_bugs_scanned;
                document.getElementById('valAcceptance').innerText = '%' + data.metrics.patch_acceptance_rate;
                document.getElementById('valTime').innerText = data.metrics.avg_time_to_fix_seconds + 's';
                document.getElementById('valCost').innerText = '$' + data.metrics.total_token_cost_usd;
                
                const btn = document.getElementById('runBtn');
                const statusSpan = document.getElementById('pipelineStatus');
                
                if (data.is_running) {
                    btn.disabled = true;
                    btn.innerHTML = '<span>⏳ Hunting in progress...</span>';
                    statusSpan.innerText = 'Status: ' + data.current_step;
                } else {
                    btn.disabled = false;
                    btn.innerHTML = '<span>⚡ Run Autonomous Pipeline</span>';
                    statusSpan.innerText = data.last_run ? 'Last Run: ' + data.last_run : 'Status: Ready';
                }

                if (data.results && data.results.length > 0) {
                    const tbody = document.getElementById('resultsBody');
                    tbody.innerHTML = '';
                    data.results.forEach(item => {
                        const bug = item.bug_report;
                        const repro = item.test_reproduction;
                        const fix = item.fix_result;
                        const ver = item.verification_result;

                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td><code>${bug.bug_id}</code></td>
                            <td><strong>${bug.title}</strong> <span class="status-pill pill-failed">${bug.severity}</span></td>
                            <td>${bug.bug_type}</td>
                            <td><span class="status-pill pill-failed">${repro.initial_test_status}</span></td>
                            <td><span class="status-pill pill-passed">${fix.final_test_status}</span></td>
                            <td><span class="status-pill pill-passed">Score: ${ver.security_score}/100</span></td>
                            <td>${fix.pr_title}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            } catch (err) {
                console.error("Dashboard fetch error:", err);
            }
        }

        async function startHunt() {
            try {
                document.getElementById('runBtn').disabled = true;
                await fetch('/api/run', { method: 'POST' });
                setTimeout(fetchStatus, 500);
            } catch (err) {
                alert("Error starting pipeline: " + err);
            }
        }

        setInterval(fetchStatus, 2500);
        fetchStatus();
    </script>
</body>
</html>
"""

class DashboardHTTPHandler(BaseHTTPRequestHandler):
    """Handles Dashboard HTTP API and UI serving."""

    def log_message(self, format, *args):
        # Mute standard noisy HTTP server logging
        return

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/" or url.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif url.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(DASHBOARD_STATE).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == "/api/run":
            if not DASHBOARD_STATE["is_running"]:
                thread = threading.Thread(target=self._run_pipeline_background, daemon=True)
                thread.start()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "started"}).encode("utf-8"))
            else:
                self.send_response(409)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "already_running"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def _run_pipeline_background(self):
        """Executes the BugHunterOrchestrator pipeline in a background thread."""
        DASHBOARD_STATE["is_running"] = True
        DASHBOARD_STATE["current_step"] = "Executing 4-Agent Pipeline..."
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            target_dir = os.path.join(current_dir, "sample_target")
            
            orchestrator = BugHunterOrchestrator()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            pipeline_data = loop.run_until_complete(orchestrator.run_pipeline(target_dir))
            loop.close()

            DASHBOARD_STATE["results"] = [
                {
                    "bug_report": item["bug_report"].__dict__,
                    "test_reproduction": item["test_reproduction"].__dict__,
                    "fix_result": item["fix_result"].__dict__,
                    "verification_result": item["verification_result"].__dict__,
                }
                for item in pipeline_data["results"]
            ]
            DASHBOARD_STATE["metrics"] = pipeline_data["metrics"].__dict__
            DASHBOARD_STATE["last_run"] = "Just now"
            DASHBOARD_STATE["current_step"] = "Completed"
        except Exception as e:
            DASHBOARD_STATE["current_step"] = f"Error: {str(e)}"
        finally:
            DASHBOARD_STATE["is_running"] = False

def load_initial_reports():
    """Pre-populates dashboard state if existing reports are present."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    bench_file = os.path.join(current_dir, "benchmark_report.json")
    report_file = os.path.join(current_dir, "bug_hunter_report.json")

    if os.path.exists(bench_file):
        try:
            with open(bench_file, "r", encoding="utf-8") as f:
                DASHBOARD_STATE["metrics"] = json.load(f)
                DASHBOARD_STATE["last_run"] = "Prior Run"
        except Exception:
            pass

    if os.path.exists(report_file):
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                items = json.load(f)
                DASHBOARD_STATE["results"] = [
                    {
                        "bug_report": {
                            "bug_id": item.get("bug_id", "BUG-001"),
                            "title": item.get("title", ""),
                            "bug_type": item.get("bug_type", "Logic"),
                            "severity": item.get("severity", "HIGH")
                        },
                        "test_reproduction": {
                            "initial_test_status": item.get("initial_test_status", "FAILED")
                        },
                        "fix_result": {
                            "final_test_status": item.get("final_test_status", "PASSED"),
                            "pr_title": item.get("pr_title", "")
                        },
                        "verification_result": {
                            "security_score": item.get("security_score", 95)
                        }
                    }
                    for item in items
                ]
        except Exception:
            pass

def start_dashboard(port: int = 8080):
    """Starts the Self-Healing Bug Hunter web dashboard server."""
    load_initial_reports()
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, DashboardHTTPHandler)
    print("=" * 70)
    print(f"📊 [Dashboard] Self-Healing Bug Hunter Web Dashboard is live!")
    print(f"👉 Local URL: http://127.0.0.1:{port}")
    print(f"👉 Press Ctrl+C to stop the dashboard server.")
    print("=" * 70)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server...")
        httpd.server_close()

if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    start_dashboard(port)
