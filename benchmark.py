"""
benchmark.py - Self-Healing Bug Hunter Benchmark & Performance Evaluation Module

This module measures True-Positives, False Alarms, Patch Acceptance Rate (%), 
Estimated Token Costs ($), and Time-to-Fix latency.
"""

import time
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from tools import write_file

@dataclass
class BenchmarkMetrics:
    """Benchmark evaluation metrics model."""
    total_bugs_scanned: int
    true_positives: int
    false_alarms: int
    patch_acceptance_rate: float  # Percentage (%)
    total_token_cost_usd: float  # Estimated USD cost
    avg_time_to_fix_seconds: float
    total_duration_seconds: float

class BugHunterBenchmark:
    """
    BugHunterBenchmark: Evaluates system performance with quantitative metrics.
    """

    ESTIMATED_INPUT_COST_PER_1K = 0.00015   # Gemini 2.5 Flash estimated token pricing
    ESTIMATED_OUTPUT_COST_PER_1K = 0.00060

    @staticmethod
    def evaluate(results: List[Dict[str, Any]], total_duration_seconds: float) -> BenchmarkMetrics:
        """
        Analyzes pipeline results to calculate benchmark metrics.
        """
        total_bugs = len(results)
        if total_bugs == 0:
            return BenchmarkMetrics(0, 0, 0, 0.0, 0.0, 0.0, total_duration_seconds)

        true_positives = 0
        false_alarms = 0
        accepted_patches = 0

        for res in results:
            repro = res.get("test_reproduction")
            verifier = res.get("verification_result")

            if repro and repro.initial_test_status == "FAILED":
                true_positives += 1
            else:
                false_alarms += 1

            if verifier and verifier.is_accepted:
                accepted_patches += 1

        acceptance_rate = round((accepted_patches / total_bugs) * 100, 2)
        avg_time = round(total_duration_seconds / total_bugs, 2)
        
        estimated_tokens = total_bugs * 4000
        estimated_cost = round((estimated_tokens / 1000) * BugHunterBenchmark.ESTIMATED_INPUT_COST_PER_1K, 5)

        return BenchmarkMetrics(
            total_bugs_scanned=total_bugs,
            true_positives=true_positives,
            false_alarms=false_alarms,
            patch_acceptance_rate=acceptance_rate,
            total_token_cost_usd=estimated_cost,
            avg_time_to_fix_seconds=avg_time,
            total_duration_seconds=round(total_duration_seconds, 2)
        )

    @staticmethod
    def export_report(metrics: BenchmarkMetrics, json_path: str = "benchmark_report.json", md_path: str = "benchmark_report.md"):
        """Exports benchmark metrics report to file."""
        write_file(json_path, json.dumps(asdict(metrics), indent=2))

        md_content = f"""# 📊 Self-Healing Bug Hunter Benchmark Report

| Metric | Value |
| :--- | :--- |
| **Total Bugs Scanned** | `{metrics.total_bugs_scanned}` |
| **True-Positives** | `{metrics.true_positives}` |
| **False Alarms** | `{metrics.false_alarms}` |
| **Patch Acceptance Rate** | **`%{metrics.patch_acceptance_rate}`** |
| **Average Time-to-Fix** | `{metrics.avg_time_to_fix_seconds}s` |
| **Total Pipeline Duration** | `{metrics.total_duration_seconds}s` |
| **Estimated Token Cost** | `${metrics.total_token_cost_usd} USD` |
"""
        write_file(md_path, md_content)
        return md_path
