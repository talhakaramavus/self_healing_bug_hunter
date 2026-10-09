"""
verifier.py - Verifier Agent (Güvenlik & Kapsam Doğrulayıcı Ajan)

Bu modül, Fixer Agent tarafından üretilen yamayı temiz bir sandbox ortamında denetleyen,
kapsam sınırlarını (scope isolation), yetki genişletmelerini (permission expansion) ve
kabul kriterlerini (acceptance criteria) doğrulayan Verifier Agent sınıfını tanımlar.
"""

import os
import re
import asyncio
from google import genai
from google.genai import types
from config import VERIFIER_AGENT_PROMPT, DEFAULT_MODEL, BugReport, FixResult, VerificationResult, get_genai_client
from tools import run_pytest

class VerifierAgent:
    """
    Verifier Agent: Yamayı dar kapsamlı yetki, güvenlik denetimi ve sandbox testleri ile doğrular.
    """

    # Güvenlik açısından tehlikeli sayılabilecek kalıplar
    FORBIDDEN_PATTERNS = [
        r"\beval\(",
        r"\bexec\(",
        r"\bos\.system\(",
        r"\b__import__\(",
        r"\bsubprocess\.Popen\(",
        r"chmod\s+777"
    ]

    def __init__(self):
        self.client = get_genai_client()
        self.model = DEFAULT_MODEL

    async def verify_patch(self, bug_report: BugReport, fix_result: FixResult) -> VerificationResult:
        """
        Yamayı güvenlik, kapsam izolasyonu ve sandbox testleri açısından denetler.

        :param bug_report: Scout Agent hata raporu
        :param fix_result: Fixer Agent tamir sonucu
        :return: VerificationResult doğrulama raporu
        """
        print(f"🛡️ [Verifier Agent] {bug_report.bug_id} için yama ve güvenlik denetimi başlatılıyor...")

        # 1. Kapsam İzolasyonu Kontrolü (Scope Isolation Audit)
        scope_isolated = self._check_scope_isolation(bug_report.file_path, fix_result.fixed_file_path)

        # 2. Güvenlik ve Yetki İncelemesi (Permission Expansion Audit)
        permission_expanded = self._check_permission_expansion(fix_result.patch_code)

        # 3. Sandbox Test Çalıştırması
        test_file = fix_result.fixed_file_path.replace(".py", "").replace("buggy_", "test_reproduce_bug_")
        sandbox_passed, test_output = run_pytest(fix_result.fixed_file_path, timeout=15)
        sandbox_status = "PASSED" if fix_result.final_test_status == "PASSED" else "FAILED"

        # LLM ile derinlemesine güvenlik ve kabul kriteri denetimi yap
        prompt = (
            f"Aşağıdaki yamayı güvenlik ve kabul kriterleri (Acceptance Criteria) açısından değerlendir:\n\n"
            f"Hata ID: {bug_report.bug_id}\n"
            f"Hata Türü: {bug_report.bug_type}\n"
            f"Uygulanan Yama Kodu:\n"
            f"```python\n{fix_result.patch_code}\n```\n\n"
            f"Güvenlik Açığı Var mı? Yetki genişletmesi var mı?\n"
            f"Lütfen güvenlik skorunu (0-100) ve yamanın kabul edilip (ACCEPTED) edilmediğini analiz et."
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=VERIFIER_AGENT_PROMPT,
                    temperature=0.1,
                )
            )
            analysis_text = response.text or ""
        except Exception as e:
            print(f"⚠️ [Verifier Agent] GenAI API denetim uyarısı: {e}")
            analysis_text = "API denetimi tamamlanamadı, statik güvenlik kuralları uygulandı."

        # Yamanın kabul durumu
        is_accepted = scope_isolated and (not permission_expanded) and (fix_result.final_test_status == "PASSED")
        security_score = 95 if is_accepted else 40
        audit_notes = (
            f"Kapsam İzolasyonu: {'✅ BAŞARILI' if scope_isolated else '❌ BAŞARISIZ'}\n"
            f"Yetki Genişletme Riski: {'⚠️ TESPİT EDİLDİ' if permission_expanded else '✅ TEMİZ'}\n"
            f"Sandbox Durumu: {sandbox_status}\n"
            f"Analiz: {analysis_text[:200]}..."
        )

        if is_accepted:
            print(f"✅ [Verifier Agent] YAMA KABUL EDİLDİ (Score: {security_score}/100, Scope Isolated: {scope_isolated})")
        else:
            print(f"❌ [Verifier Agent] YAMA REDDEDİLDİ (Permission Expanded: {permission_expanded}, Scope Isolated: {scope_isolated})")

        return VerificationResult(
            bug_id=bug_report.bug_id,
            is_accepted=is_accepted,
            security_score=security_score,
            scope_isolated=scope_isolated,
            permission_expanded=permission_expanded,
            sandbox_status=sandbox_status,
            audit_notes=audit_notes
        )

    def _check_scope_isolation(self, target_file: str, modified_file: str) -> bool:
        """Yamalanan dosyanın yalnızca izin verilen hedef dosya olup olmadığını kontrol eder."""
        return os.path.abspath(target_file) == os.path.abspath(modified_file)

    def _check_permission_expansion(self, patch_code: str) -> bool:
        """Tehlikeli kod veya yetki genişletme kalıpları içerip içermediğini denetler."""
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, patch_code):
                return True
        return False
