"""
orchestrator.py - Self-Healing Bug Hunter Pipeline Orchestrator

This module orchestrates asynchronous data flow across Scout -> Reproducer -> Fixer -> Verifier agents,
featuring an adaptive iterative multi-repair loop (up to 3 attempts with diagnostic feedback).
"""

import time
import asyncio
from typing import List, Dict, Any
from agents.scout import ScoutAgent
from agents.reproducer import ReproducerAgent
from agents.fixer import FixerAgent
from agents.verifier import VerifierAgent
from config import BugReport, TestReproduction, FixResult, VerificationResult
from benchmark import BugHunterBenchmark, BenchmarkMetrics
from snapshot_manager import SnapshotManager

class BugHunterOrchestrator:
    """
    BugHunterOrchestrator: Main pipeline orchestrator for the 4-agent self-healing workflow.
    """

    def __init__(self, max_repair_attempts: int = 3, base_dir: str = None):
        self.scout_agent = ScoutAgent()
        self.reproducer_agent = ReproducerAgent()
        self.fixer_agent = FixerAgent()
        self.verifier_agent = VerifierAgent()
        self.max_repair_attempts = max_repair_attempts
        self.snapshot_manager = SnapshotManager(base_dir=base_dir)

    async def run_pipeline(self, target_dir: str) -> Dict[str, Any]:
        """
        Executes the asynchronous Scout -> Reproducer -> Fixer -> Verifier pipeline
        with an adaptive multi-attempt feedback loop and safe snapshot rollbacks.
        """
        print("================================================================================")
        print("🚀 [Self-Healing Bug Hunter] Starting 4-Agent Autonomous Pipeline...")
        print("================================================================================")

        start_time = time.time()
        pipeline_results = []

        bug_reports: List[BugReport] = await self.scout_agent.scan_directory(target_dir)

        if not bug_reports:
            print("🎉 No bugs or security vulnerabilities detected. Codebase is healthy!")
            duration = time.time() - start_time
            metrics = BugHunterBenchmark.evaluate([], duration)
            return {"results": [], "metrics": metrics}

        for report in bug_reports:
            print("\n--------------------------------------------------------------------------------")
            print(f"📌 PROCESSING BUG: {report.bug_id} - {report.title} [{report.severity}]")
            print("--------------------------------------------------------------------------------")

            test_repro: TestReproduction = await self.reproducer_agent.reproduce_bug(report)

            # Create safe snapshot prior to patching
            snapshot_id = self.snapshot_manager.create_snapshot([report.file_path])

            # Adaptive Iterative Repair Loop
            fix_result = None
            verification = None
            feedback = None
            is_patch_successful = False

            for attempt in range(1, self.max_repair_attempts + 1):
                fix_result = await self.fixer_agent.fix_bug(
                    report, 
                    test_repro, 
                    attempt=attempt, 
                    feedback=feedback
                )
                verification = await self.verifier_agent.verify_patch(report, fix_result)

                if fix_result.final_test_status == "PASSED" and verification.is_accepted:
                    print(f"🎯 [Orchestrator] Fix verified and accepted on attempt {attempt}/{self.max_repair_attempts}!")
                    is_patch_successful = True
                    self.snapshot_manager.cleanup_snapshot(snapshot_id)
                    break
                else:
                    feedback = (
                        f"Test status: {fix_result.final_test_status}. "
                        f"Audit Notes: {verification.audit_notes}"
                    )
                    if attempt < self.max_repair_attempts:
                        print(f"⚠️ [Orchestrator] Attempt {attempt} failed validation. Retrying with adaptive feedback...")

            # Safe Rollback: If patch was not successfully accepted, restore original file
            if not is_patch_successful:
                print(f"🛡️ [Orchestrator] Safe Rollback: Patch for {report.bug_id} could not be safely verified. Reverting to pristine snapshot.")
                self.snapshot_manager.restore_snapshot(snapshot_id)

            pipeline_results.append({
                "bug_report": report,
                "test_reproduction": test_repro,
                "fix_result": fix_result,
                "verification_result": verification
            })

        duration = time.time() - start_time
        metrics: BenchmarkMetrics = BugHunterBenchmark.evaluate(pipeline_results, duration)

        print("\n================================================================================")
        print(f"✅ [Self-Healing Bug Hunter] Pipeline Completed! Patch Acceptance Rate: %{metrics.patch_acceptance_rate}")
        print("================================================================================")
        
        return {
            "results": pipeline_results,
            "metrics": metrics
        }
