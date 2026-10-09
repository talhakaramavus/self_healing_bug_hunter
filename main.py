"""
main.py - Self-Healing Bug Hunter Ana Çalıştırma Dosyası

Bu dosya google-genai SDK mimarisindeki 4 ajanı (Scout, Reproducer, Fixer, Verifier) 
asenkron boru hattı (async/await) ile tetikler ve örnek/hedef proje üzerindeki 
otonom test-tamir sürecini yürütür.
"""

import os
import sys
import argparse
import asyncio

# Windows konsol çıktı şifrelemesini UTF-8 olarak ayarla (Emoji gösterim hatalarını önler)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from orchestrator import BugHunterOrchestrator
from reporter import BugReporter
from benchmark import BugHunterBenchmark
from logger import Logger

async def main():
    """
    Ana giriş noktası: Komut satırı argümanlarını ayrıştırır ve Bug Hunter boru hattını çalıştırır.
    """
    parser = argparse.ArgumentParser(description="Self-Healing Bug Hunter (Google GenAI Multi-Agent System)")
    parser.add_argument("--target-dir", type=str, default=None, help="Taranacak hedef kod dizini")
    parser.add_argument("--export-reports", action="store_true", default=True, help="HTML, Markdown ve JSON raporlarını dışa aktar")
    parser.add_argument("--export-benchmark", action="store_true", default=True, help="Benchmark metrik raporunu kaydet")
    args = parser.parse_args()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = args.target_dir or os.path.join(current_dir, "sample_target")

    # Örnek dosya okuma testi için geçici bir test veri dosyası oluştur
    sample_data_file = os.path.join(target_dir, "sample_data.txt")
    if not os.path.exists(sample_data_file):
        with open(sample_data_file, "w", encoding="utf-8") as f:
            f.write("Satır 1: Test Verisi\nSatır 2: Antigravity Self-Healing\nSatır 3: Bug Hunter\n")

    Logger.banner("SELF-HEALING BUG HUNTER MULTI-AGENT SYSTEM")
    Logger.info(f"Hedef Kod Dizini: {target_dir}")

    # Orkestratörü ilklendir
    orchestrator = BugHunterOrchestrator()

    # Asenkron 4-ajanlı boru hattını çalıştır (Scout -> Reproducer -> Fixer -> Verifier)
    pipeline_data = await orchestrator.run_pipeline(target_dir)
    results = pipeline_data["results"]
    metrics = pipeline_data["metrics"]

    # İşlem sonuçlarını ekrana özetle
    Logger.banner("📊 ÖZET RAPOR VE BENCHMARK METRİKLERİ")
    for index, res in enumerate(results, start=1):
        bug = res["bug_report"]
        repro = res["test_reproduction"]
        fix = res["fix_result"]
        ver = res["verification_result"]

        Logger.step(f"[{index}] HATA ID: {bug.bug_id} - {bug.title}")
        print(f"    • Tür: {bug.bug_type} | Öncelik: {bug.severity}")
        print(f"    • Doğrulama Testi: {repro.test_file_path} (İlk Durum: {repro.initial_test_status})")
        print(f"    • Tamirat Sonrası Durum: {fix.final_test_status}")
        print(f"    • Verifier Kabul Durumu: {'✅ KABUL EDİLDİ' if ver.is_accepted else '❌ REDDEDİLDİ'} (Score: {ver.security_score}/100)")
        print(f"    • Üretilen PR Başlığı: {fix.pr_title}")
        print("-" * 70)

    # Benchmark Özeti
    Logger.step("⚡ BENCHMARK METRİKLERİ")
    print(f"    • Gerçek Pozitif Hatalar: {metrics.true_positives} / Yanlış Alarm: {metrics.false_alarms}")
    print(f"    • Yama Kabul Oranı: %{metrics.patch_acceptance_rate}")
    print(f"    • Ortalama Tamir Süresi: {metrics.avg_time_to_fix_seconds}s (Toplam: {metrics.total_duration_seconds}s)")
    print(f"    • Tahmini Token Maliyeti: ${metrics.total_token_cost_usd} USD")

    # Raporları Dışa Aktar
    if args.export_reports:
        BugReporter.export_json(results)
        BugReporter.export_markdown(results)
        BugReporter.export_html(results)
        Logger.success("Raporlar kaydedildi: bug_hunter_report.html, bug_hunter_report.md, bug_hunter_report.json")

    if args.export_benchmark:
        BugHunterBenchmark.export_report(metrics)
        Logger.success("Benchmark raporu kaydedildi: benchmark_report.md, benchmark_report.json")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        Logger.warning("Süreç kullanıcı tarafından durduruldu.")