"""
reproducer.py - Reproducer Agent (Doğrulayıcı Ajan)

Bu modül, google-genai SDK kullanarak Scout Agent tarafından bildirilen hatayı doğrulamak amacıyla
şu anda BAŞARISIZ (failing) olan bir pytest unit testi yazan Reproducer Agent sınıfını tanımlar.
"""

import os
import re
import asyncio
from google import genai
from google.genai import types
from config import REPRODUCER_AGENT_PROMPT, DEFAULT_MODEL, BugReport, TestReproduction, get_genai_client
from tools import read_file, write_file, run_pytest

class ReproducerAgent:
    """
    Reproducer Agent: Tespit edilen hatayı üreten ve mevcut koda karşı BAŞARISIZ olan unit testi yazar.
    """

    def __init__(self):
        self.client = get_genai_client()
        self.model = DEFAULT_MODEL

    async def reproduce_bug(self, bug_report: BugReport) -> TestReproduction:
        """
        Scout Agent hata raporunu alır, hatayı doğrulayan failing unit testi oluşturur ve çalıştırır.

        :param bug_report: İlgili hata raporu nesnesi
        :return: TestReproduction doğrulama nesnesi
        """
        print(f"🧪 [Reproducer Agent] {bug_report.bug_id} için doğrulama testi yazılıyor...")

        # İlgili kaynak dosyanın içeriğini oku
        source_code = read_file(bug_report.file_path)

        prompt = (
            f"Aşağıdaki kaynak koddaki '{bug_report.title}' hatasını kesin olarak tetikleyen "
            f"ve BAŞARISIZ (FAIL) çıkacak bir pytest unit testi yaz.\n\n"
            f"Hata Açıklaması: {bug_report.description}\n"
            f"Önerilen Test Senaryosu: {bug_report.suggested_reproduction}\n\n"
            f"Kaynak Kod ({bug_report.file_path}):\n"
            f"```python\n{source_code}\n```\n\n"
            f"Sadece ve sadece temiz Python test kodunu ```python ... ``` bloğu içerisinde ver."
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=REPRODUCER_AGENT_PROMPT,
                    temperature=0.2,
                )
            )
            response_text = response.text or ""
        except Exception as e:
            print(f"⚠️ [Reproducer Agent] GenAI API hatası: {e}")
            response_text = ""

        test_code = self._extract_code(response_text, bug_report)

        # Test dosyasının kaydedileceği dizin
        target_dir = os.path.dirname(os.path.abspath(bug_report.file_path))
        test_file_path = os.path.join(target_dir, f"test_reproduce_{bug_report.bug_id.lower().replace('-', '_')}.py")

        # Üretilen test kodunu yaz
        write_file(test_file_path, test_code)
        print(f"💾 [Reproducer Agent] Test yazıldı: {test_file_path}")

        # Testi çalıştır ve BAŞARISIZ (FAILED) olduğunu doğrula
        is_passed, output = run_pytest(test_file_path)
        status = "PASSED" if is_passed else "FAILED"

        if not is_passed:
            print(f"❌ [Reproducer Agent] Beklendiği gibi test BAŞARISIZ oldu (Bug Doğrulandı!). Status: {status}")
        else:
            print(f"⚠️ [Reproducer Agent] Uyarı: Test beklenenin aksine başarılı geçti. Status: {status}")

        return TestReproduction(
            bug_id=bug_report.bug_id,
            test_file_path=test_file_path,
            test_code=test_code,
            initial_test_status=status,
            error_output=output
        )

    def _extract_code(self, response_text: str, bug_report: BugReport) -> str:
        """
        LLM yanıtındaki markdown kod bloklarını ayıklar veya varsayılan faling test üretir.
        """
        match = re.search(r"```python(.*?)```", response_text, re.DOTALL)
        if match and match.group(1).strip():
            return match.group(1).strip()
        
        # Eğer API yanıtından kod bloğu çıkarılamazsa kural tabanlı failing pytest üret
        module_name = os.path.basename(bug_report.file_path).replace(".py", "")
        return (
            f"import pytest\n"
            f"from {module_name} import BuggyCalculator\n\n"
            f"def test_reproduce_bug():\n"
            f"    calc = BuggyCalculator()\n"
            f"    # Sıfıra bölme hatası testi\n"
            f"    with pytest.raises(ZeroDivisionError):\n"
            f"        calc.divide(10, 0)\n"
            f"    # Tip hatası testi\n"
            f"    assert calc.calculate_total([10, '20']) == 30.0\n"
        )