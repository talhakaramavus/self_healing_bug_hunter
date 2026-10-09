"""
orchestrator.py - Self-Healing Bug Hunter Akış Yöneticisi (Orchestrator)

Bu modül, Scout -> Reproducer -> Fixer -> Verifier ajanları arasındaki asenkron veri aktarımını 
ve otomatik yaşam döngüsünü (lifecycle) yönetir.
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

class BugHunterOrchestrator:
    """
    BugHunterOrchestrator: 4 ajanın uyum içinde çalışmasını sağlayan ana orkestratör sınıfı.
    """

    def __init__(self):
        # 4 Ajanı ilklendir
        self.scout_agent = ScoutAgent()
        self.reproducer_agent = ReproducerAgent()
        self.fixer_agent = FixerAgent()
        self.verifier_agent = VerifierAgent()

    async def run_pipeline(self, target_dir: str) -> Dict[str, Any]:
        """
        Scout -> Reproducer -> Fixer -> Verifier asenkron boru hattını çalıştırır.

        :param target_dir: Taranacak ve iyileştirilecek hedef projenin dizin yolu
        :return: Süreçteki tüm sonuçları ve benchmark metriklerini içeren sözlük
        """
        print("================================================================================")
        print("🚀 [Self-Healing Bug Hunter] 4-Ajanlı Otonom İyileştirme Süreci Başlatılıyor...")
        print("================================================================================")

        start_time = time.time()
        pipeline_results = []

        # 1. ADIM: Scout Agent ile Hata Tespiti
        bug_reports: List[BugReport] = await self.scout_agent.scan_directory(target_dir)

        if not bug_reports:
            print("🎉 Projede herhangi bir hata veya açık tespit edilmedi. Kod tabanı sağlıklı!")
            duration = time.time() - start_time
            metrics = BugHunterBenchmark.evaluate([], duration)
            return {"results": [], "metrics": metrics}

        # Her tespit edilen hata için 4 ajanlı boru hattını sırayla çalıştır
        for report in bug_reports:
            print("\n--------------------------------------------------------------------------------")
            print(f"📌 İŞLENEN HATA: {report.bug_id} - {report.title} [{report.severity}]")
            print("--------------------------------------------------------------------------------")

            # 2. ADIM: Reproducer Agent ile Başarısız Test Yazımı ve Doğrulama
            test_repro: TestReproduction = await self.reproducer_agent.reproduce_bug(report)

            # 3. ADIM: Fixer Agent ile Kaynak Kod Tamiratı ve Doğrulama
            fix_result: FixResult = await self.fixer_agent.fix_bug(report, test_repro)

            # 4. ADIM: Verifier Agent ile Sandbox Güvenlik & Kapsam Doğrulaması
            verification: VerificationResult = await self.verifier_agent.verify_patch(report, fix_result)

            pipeline_results.append({
                "bug_report": report,
                "test_reproduction": test_repro,
                "fix_result": fix_result,
                "verification_result": verification
            })

        duration = time.time() - start_time
        metrics: BenchmarkMetrics = BugHunterBenchmark.evaluate(pipeline_results, duration)

        print("\n================================================================================")
        print(f"✅ [Self-Healing Bug Hunter] Süreç Tamamlandı! Kabul Oranı: %{metrics.patch_acceptance_rate}")
        print("================================================================================")
        
        return {
            "results": pipeline_results,
            "metrics": metrics
        }
