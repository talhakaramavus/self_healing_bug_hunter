"""
main.py - Self-Healing Bug Hunter Ana Çalıştırma Dosyası

Bu dosya google-genai SDK mimarisindeki 3 ajanı (Scout, Reproducer, Fixer) 
asenkron boru hattı (async/await) ile tetikler ve örnek hedef proje üzerindeki 
otonom test-tamir sürecini yürütür.
"""

import os
import sys
import asyncio

# Windows konsol çıktı şifrelemesini UTF-8 olarak ayarla (Emoji gösterim hatalarını önler)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from orchestrator import BugHunterOrchestrator

async def main():
    """
    Ana giriş noktası: Hedef dizini belirler ve Self-Healing Bug Hunter boru hattını çalıştırır.
    """
    # Mevcut dosyanın konumunu al ve sample_target dizinini hedefle
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(current_dir, "sample_target")

    # Örnek dosya okuma testi için geçici bir test veri dosyası oluştur
    sample_data_file = os.path.join(target_dir, "sample_data.txt")
    if not os.path.exists(sample_data_file):
        with open(sample_data_file, "w", encoding="utf-8") as f:
            f.write("Satır 1: Test Verisi\nSatır 2: Antigravity Self-Healing\nSatır 3: Bug Hunter\n")

    print(f"🎯 Hedef Kod Dizini: {target_dir}\n")

    # Orkestratörü ilklendir
    orchestrator = BugHunterOrchestrator()

    # Asenkron boru hattını çalıştır (Scout -> Reproducer -> Fixer)
    results = await orchestrator.run_pipeline(target_dir)

    # İşlem sonuçlarını ekrana özetle
    print("\n================================================================================")
    print("📊 ÖZET RAPOR VE GÜNCELLEMELER")
    print("================================================================================")
    for index, res in enumerate(results, start=1):
        bug = res["bug_report"]
        repro = res["test_reproduction"]
        fix = res["fix_result"]

        print(f"\n[{index}] HATA ID: {bug.bug_id}")
        print(f"    • Başlık: {bug.title}")
        print(f"    • Tür: {bug.bug_type} | Öncelik: {bug.severity}")
        print(f"    • Doğrulama Testi: {repro.test_file_path} (İlk Durum: {repro.initial_test_status})")
        print(f"    • Tamirat Sonrası Durum: {fix.final_test_status}")
        print(f"    • Üretilen PR Başlığı: {fix.pr_title}")
        print("-" * 65)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSüreç kullanıcı tarafından durduruldu.")