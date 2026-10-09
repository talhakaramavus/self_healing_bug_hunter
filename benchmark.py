"""
benchmark.py - Self-Healing Bug Hunter Performans ve Değerlendirme Modülü (Benchmark)

Bu modül; Gerçek Pozitif Hataları (True-Positives), Yanlış Alarmları (False Alarms), 
Yama Kabul Oranını (Patch Acceptance Rate %), Tahmini Token Maliyetini ($) 
ve Tamir Süresini (Time-to-Fix) hesaplar ve raporlar.
"""

import time
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from tools import write_file

@dataclass
class BenchmarkMetrics:
    """Benchmark değerlendirme metrikleri modeli."""
    total_bugs_scanned: int
    true_positives: int
    false_alarms: int
    patch_acceptance_rate: float  # Percentage (%)
    total_token_cost_usd: float  # Estimated USD cost
    avg_time_to_fix_seconds: float
    total_duration_seconds: float

class BugHunterBenchmark:
    """
    BugHunterBenchmark: Sistem başarısını sayısal metriklerle ölçen benchmark sınıfı.
    """

    ESTIMATED_INPUT_COST_PER_1K = 0.00015   # Gemini 2.5 Flash tahmini token fiyatı
    ESTIMATED_OUTPUT_COST_PER_1K = 0.00060

    @staticmethod
    def evaluate(results: List[Dict[str, Any]], total_duration_seconds: float) -> BenchmarkMetrics:
        """
        İşlem sonuçlarını analiz ederek benchmark metriklerini hesaplar.
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

            # Eğer test başlangıçta FAILED ise gerçek pozitif hatadır
            if repro and repro.initial_test_status == "FAILED":
                true_positives += 1
            else:
                false_alarms += 1

            # Verifier yamayı kabul etti mi?
            if verifier and verifier.is_accepted:
                accepted_patches += 1

        acceptance_rate = round((accepted_patches / total_bugs) * 100, 2)
        avg_time = round(total_duration_seconds / total_bugs, 2)
        
        # Tahmini token maliyeti hesabı (Hata başına ortalama ~4.000 token varsayımı)
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
        """Benchmark sonuçlarını dosyaya kaydeder."""
        write_file(json_path, json.dumps(asdict(metrics), indent=2))

        md_content = f"""# 📊 Self-Healing Bug Hunter Benchmark Raporu

| Metrik | Değer |
| :--- | :--- |
| **Taranan Toplam Hata** | `{metrics.total_bugs_scanned}` |
| **Gerçek Pozitif (True-Positives)** | `{metrics.true_positives}` |
| **Yanlış Alarm (False Alarms)** | `{metrics.false_alarms}` |
| **Yama Kabul Oranı (Acceptance Rate)** | **`%{metrics.patch_acceptance_rate}`** |
| **Ortalama Tamir Süresi (Time-to-Fix)** | `{metrics.avg_time_to_fix_seconds} saniye` |
| **Toplam İşlem Süresi** | `{metrics.total_duration_seconds} saniye` |
| **Tahmini Token Maliyeti** | `${metrics.total_token_cost_usd} USD` |
"""
        write_file(md_path, md_content)
        return md_path
