"""
main.py - Self-Healing Bug Hunter Main CLI Entry Point

This file triggers the 4-agent asynchronous pipeline (Scout, Reproducer, Fixer, Verifier) 
and executes autonomous bug discovery, reproduction, fixing, and auditing.
Supports multi-language detection, AST static security analysis, iterative repair, 
automated PR creation, and real-time Web Dashboard.
"""

import os
import sys
import argparse
import asyncio

# Configure UTF-8 encoding for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from orchestrator import BugHunterOrchestrator
from reporter import BugReporter
from benchmark import BugHunterBenchmark
from logger import Logger
from multi_language import MultiLanguageManager
from pr_creator import PullRequestCreator

async def main():
    """
    Main entry point: parses CLI arguments and runs the Bug Hunter pipeline.
    """
    parser = argparse.ArgumentParser(description="Self-Healing Bug Hunter (Google GenAI Multi-Agent System)")
    parser.add_argument("--target-dir", type=str, default=None, help="Target codebase directory to scan")
    parser.add_argument("--export-reports", action="store_true", default=True, help="Export HTML, Markdown, and JSON reports")
    parser.add_argument("--export-benchmark", action="store_true", default=True, help="Save benchmark metrics report")
    parser.add_argument("--create-pr", action="store_true", default=False, help="Autonomously create git branch and Pull Request for verified patches")
    parser.add_argument("--max-repair-attempts", type=int, default=3, help="Maximum iterative repair attempts per bug")
    parser.add_argument("--dashboard", action="store_true", default=False, help="Launch interactive real-time Web Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port for Web Dashboard (default: 8080)")
    args = parser.parse_args()

    # Launch Web Dashboard if requested
    if args.dashboard:
        from dashboard import start_dashboard
        start_dashboard(args.port)
        return

    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = args.target_dir or os.path.join(current_dir, "sample_target")

    sample_data_file = os.path.join(target_dir, "sample_data.txt")
    if not os.path.exists(sample_data_file):
        with open(sample_data_file, "w", encoding="utf-8") as f:
            f.write("Line 1: Test Data\nLine 2: Self-Healing Bug Hunter\nLine 3: Agentic Pipeline\n")

    Logger.banner("SELF-HEALING BUG HUNTER MULTI-AGENT SYSTEM")
    Logger.info(f"Target Codebase Directory: {target_dir}")

    # Detect codebase programming languages
    detected_languages = MultiLanguageManager.detect_project_languages(target_dir)
    Logger.info(f"Detected Languages: {', '.join(detected_languages).upper()}")

    orchestrator = BugHunterOrchestrator(max_repair_attempts=args.max_repair_attempts)

    pipeline_data = await orchestrator.run_pipeline(target_dir)
    results = pipeline_data["results"]
    metrics = pipeline_data["metrics"]

    Logger.banner("📊 SUMMARY REPORT & BENCHMARK METRICS")
    for index, res in enumerate(results, start=1):
        bug = res["bug_report"]
        repro = res["test_reproduction"]
        fix = res["fix_result"]
        ver = res["verification_result"]

        Logger.step(f"[{index}] BUG ID: {bug.bug_id} - {bug.title}")
        print(f"    • Type: {bug.bug_type} | Severity: {bug.severity}")
        print(f"    • Reproduction Test: {repro.test_file_path} (Initial Status: {repro.initial_test_status})")
        print(f"    • Post-Fix Status: {fix.final_test_status}")
        print(f"    • Verifier Acceptance: {'✅ ACCEPTED' if ver.is_accepted else '❌ REJECTED'} (Score: {ver.security_score}/100)")
        print(f"    • Generated PR Title: {fix.pr_title}")

        # Optional automated Git Branch & PR creation
        if args.create_pr and ver.is_accepted:
            pr_res = PullRequestCreator.create_pr_for_fix(fix, ver, repo_dir=current_dir)
            print(f"    • Git Branch & PR: {pr_res.message}")

        print("-" * 70)

    Logger.step("⚡ BENCHMARK METRICS")
    print(f"    • True-Positives: {metrics.true_positives} / False Alarms: {metrics.false_alarms}")
    print(f"    • Patch Acceptance Rate: %{metrics.patch_acceptance_rate}")
    print(f"    • Average Time-to-Fix: {metrics.avg_time_to_fix_seconds}s (Total: {metrics.total_duration_seconds}s)")
    print(f"    • Estimated Token Cost: ${metrics.total_token_cost_usd} USD")

    if args.export_reports:
        BugReporter.export_json(results)
        BugReporter.export_markdown(results)
        BugReporter.export_html(results)
        Logger.success("Reports exported: bug_hunter_report.html, bug_hunter_report.md, bug_hunter_report.json")

    if args.export_benchmark:
        BugHunterBenchmark.export_report(metrics)
        Logger.success("Benchmark report exported: benchmark_report.md, benchmark_report.json")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        Logger.warning("Process interrupted by user.")