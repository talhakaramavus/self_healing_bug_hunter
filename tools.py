"""
tools.py - Self-Healing Bug Hunter Araç Yardımcıları (Tool Helpers)

Bu modül, ajanların dosya okuma, dosya yazma ve unit testlerini (pytest/unittest)
otonom olarak çalıştırıp sonuçları analiz edebilmesi için gerekli araç fonksiyonlarını içerir.
"""

import os
import sys
import subprocess
from typing import Tuple

def read_file(file_path: str) -> str:
    """
    Belirtilen dosya yolundaki içeriği okur.
    
    :param file_path: Okunacak dosya yolu
    :return: Dosya içeriği metin string'i
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """
    Belirtilen dosya yoluna içeriği yazar (klasörler yoksa otomatik oluşturur).
    
    :param file_path: Yazılacak dosya yolu
    :param content: Yazılacak içerik
    """
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def run_pytest(test_file_path: str) -> Tuple[bool, str]:
    """
    Belirtilen pytest test dosyasını bir alt süreç (subprocess) olarak çalıştırır.
    
    :param test_file_path: Çalıştırılacak unit test dosya yolu
    :return: (is_passed: bool, output_log: str) ikilisi
             is_passed True ise tüm testler başarıyla geçmiş demektir.
    """
    if not os.path.exists(test_file_path):
        return False, f"Test dosyası mevcut değil: {test_file_path}"

    try:
        # sys.executable kullanarak mevcut Python ortamındaki pytest'i tetikle
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file_path, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30
        )
        is_passed = (result.returncode == 0)
        output = result.stdout + "\n" + result.stderr
        return is_passed, output.strip()
    except subprocess.TimeoutExpired:
        return False, "Test çalıştırma zaman aşımına uğradı (Timeout 30s)."
    except Exception as e:
        return False, f"Test çalıştırılırken beklenmeyen bir hata oluştu: {str(e)}"
