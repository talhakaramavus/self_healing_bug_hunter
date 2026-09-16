"""
orchestrator.py - Self-Healing Bug Hunter Akış Yöneticisi (Orchestrator)

Bu modül, Scout -> Reproducer -> Fixer ajanları arasındaki asenkron veri aktarımını 
ve otomatik yaşam döngüsünü (lifecycle) yönetir.
"""

import asyncio
from typing import List, Dict, Any
from agents.scout import ScoutAgent
from agents.reproducer import ReproducerAgent
from agents.fixer import FixerAgent
from config import BugReport, TestReproduction, FixResult

class BugHunterOrchestrator:
    """
    BugHunterOrchestrator: 3 ajanın uyum içinde çalışmasını sağlayan ana orkestratör sınıfı.
    """

    def __init__(self):
        # Ajanları ilklendir
        self.scout_agent = ScoutAgent()
        self.reproducer_agent = ReproducerAgent()
        self.fixer_agent = FixerAgent()

    async def run_pipeline(self, target_dir: str) -> List[Dict[str, Any]]:
        """
        Scout -> Reproducer -> Fixer asenkron boru hattını çalıştırır.

        :param target_dir: Taranacak ve iyileştirilecek hedef projenin dizin yolu
        :return: Süreçteki tüm sonuçların listesi
        """
        print("================================================================================")
        print("🚀 [Self-Healing Bug Hunter] Otonom İyileştirme Süreci Başlatılıyor (google-genai)...")
        print("================================================================================")

        pipeline_results = []

        # 1. ADIM: Scout Agent ile Hata Tespiti
        bug_reports: List[BugReport] = await self.scout_agent.scan_directory(target_dir)

        if not bug_reports:
            print("🎉 Projede herhangi bir hata veya açık tespit edilmedi. Kod tabanı sağlıklı!")
            return []

        # Her tespit edilen hata için Reproducer ve Fixer ajanlarını sırayla çalıştır
        for report in bug_reports:
            print("\n--------------------------------------------------------------------------------")
            print(f"📌 İŞLENEN HATA: {report.bug_id} - {report.title} [{report.severity}]")
            print("--------------------------------------------------------------------------------")

            # 2. ADIM: Reproducer Agent ile Başarısız Test Yazımı ve Doğrulama
            test_repro: TestReproduction = await self.reproducer_agent.reproduce_bug(report)

            # 3. ADIM: Fixer Agent ile Kaynak Kod Tamiratı ve Doğrulama
            fix_result: FixResult = await self.fixer_agent.fix_bug(report, test_repro)

            pipeline_results.append({
                "bug_report": report,
                "test_reproduction": test_repro,
                "fix_result": fix_result
            })

        print("\n================================================================================")
        print("✅ [Self-Healing Bug Hunter] Tüm Hatalar Başarıyla İşlendi ve İyileştirildi!")
        print("================================================================================")
        return pipeline_results
