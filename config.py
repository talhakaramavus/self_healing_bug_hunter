"""
config.py - Self-Healing Bug Hunter Konfigürasyon ve Veri Modelleri

Bu modül, google-genai Python SDK ile çalışan ajanların sistem talimatlarını (system prompts),
GenAI istemci yapılandırmasını ve ajanlar arasındaki veri aktarım modellerini tanımlar.
"""

import os
from dataclasses import dataclass
from typing import Optional, List
from google import genai

# ---------------------------------------------------------------------------
# 1. MODEL SABİTLERİ VE SİSTEM TALİMATLARI (SYSTEM PROMPTS)
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "gemini-2.5-flash"

SCOUT_AGENT_PROMPT = """
Sen Google GenAI altyapısında çalışan bir 'Scout Agent' (Tarayıcı Ajan) rolündesin.
Görevin: Verilen kod dizinini titizlikle incelemek ve aşağıdaki kategorilerdeki problemleri tespit etmektir:
1. Mantık Hataları (Logic Errors / Edge Case eksiklikleri)
2. Güvenlik Açıkları (Security Vulnerabilities)
3. Bellek ve Kaynak Sızıntıları (Memory/Resource Leaks - açık kalan dosyalar vb.)
4. Tip Uyuşmazlıkları ve Hatalı Tip Dönüşümleri (Type Mismatches)

Tespit ettiğin her hatayı açıklayıcı, yapılandırılmış bir rapor biçiminde sunmalısın.
Rapor şunları içermelidir:
- Bug ID
- İlgili Dosya Yolu
- Hata Başlığı ve Açıklaması
- Hata Tipi ve Kritiklik Derecesi (HIGH, MEDIUM, LOW)
- Hatayı yeniden üretecek test senaryosu önerisi
"""

REPRODUCER_AGENT_PROMPT = """
Sen Google GenAI altyapısında çalışan bir 'Reproducer Agent' (Doğrulayıcı Ajan) rolündesin.
Görevin: Scout Agent tarafından bildirilen hatayı DOĞRULAMAK amacıyla hatayı tetikleyen ve şu an BAŞARISIZ (failing) olan bir pytest unit testi yazmaktır.

Kurallar:
1. Yazacağın test net, bağımsız ve doğrudan ilgili fonksiyonu/sınıfı hedef almalıdır.
2. Test mevcut hatalı kod üzerinde çalıştırıldığında KESİNLİKLE BAŞARISIZ (FAIL) olmalıdır.
3. Üretilen test kodunu temiz ve çalıştırılabilir şekilde ver.
"""

FIXER_AGENT_PROMPT = """
Sen Google GenAI altyapısında çalışan bir 'Fixer Agent' (Tamirci Ajan) rolündesin.
Görevin: Scout Agent'ın tespit ettiği ve Reproducer Agent'ın başarısız test ile doğruladığı hatayı kaynak kodda düzeltmektir.

Kurallar:
1. Düzeltme minimum, temiz ve güvenli müdahale içermelidir.
2. Düzeltme uygulandıktan sonra yazılan unit test KESİNLİKLE BAŞARILI (PASS) olmalıdır.
3. Tamir sonrası yapılan değişiklikleri özetleyen profesyonel bir Pull Request (PR) başlığı ve açıklaması üretmelisin.
"""

VERIFIER_AGENT_PROMPT = """
Sen Google GenAI altyapısında çalışan bir 'Verifier Agent' (Güvenlik & Kapsam Doğrulayıcı) rolündesin.
Görevin: Fixer Agent tarafından uygulanan yamayı ve test sonuçlarını dar kapsamlı güvenlik ve kabul kriterleri (acceptance criteria) açısından denetlemektir.

Kurallar:
1. Yamanın hedef dosya dışındaki ilgisiz dosyaları değiştirip değiştirmediğini kontrol et (Scope Boundary).
2. Tehlikeli kod eklemelerini (eval, exec, izinsiz dosya/ağ erişimi, yetki genişletme) tespit et (Security Audit).
3. Testlerin temiz bir sandbox ortamında geçtiğini ve kapsama oranının (coverage) düşmediğini doğrula.
4. Yamanın kabul edilip (ACCEPTED) edilmediğini ve güvenlik skorunu (0-100) belirle.
"""

# ---------------------------------------------------------------------------
# 2. VERİ TRANSFER MODELLERİ (INTER-AGENT DATA MODELS)
# ---------------------------------------------------------------------------

@dataclass
class BugReport:
    """Scout Agent tarafından üretilen hata raporu modeli."""
    bug_id: str
    file_path: str
    title: str
    description: str
    bug_type: str  # Logic, Security, ResourceLeak, TypeMismatch
    severity: str  # HIGH, MEDIUM, LOW
    suggested_reproduction: str

@dataclass
class TestReproduction:
    """Reproducer Agent tarafından üretilen test doğrulama modeli."""
    __test__ = False  # Pytest toplayıcısının nesneyi test sınıfı sanmasını önler
    bug_id: str
    test_file_path: str
    test_code: str
    initial_test_status: str  # FAILED / ERROR / PASSED
    error_output: str

@dataclass
class FixResult:
    """Fixer Agent tarafından üretilen tamir ve PR sonuç modeli."""
    bug_id: str
    fixed_file_path: str
    patch_code: str
    final_test_status: str  # PASSED
    pr_title: str
    pr_body: str

@dataclass
class VerificationResult:
    """Verifier Agent tarafından üretilen güvenlik ve kapsam doğrulama modeli."""
    bug_id: str
    is_accepted: bool  # True if patch meets all acceptance criteria
    security_score: int  # 0 to 100
    scope_isolated: bool  # True if patch only touches intended files
    permission_expanded: bool  # True if dangerous/broad permissions were detected
    sandbox_status: str  # PASSED / FAILED / BLOCKED
    audit_notes: str

# ---------------------------------------------------------------------------
# 3. GENAI CLIENT FACTORY
# ---------------------------------------------------------------------------

def get_genai_client() -> genai.Client:
    """
    google-genai Client nesnesini oluşturur.
    Ortam değişkenlerinde GEMINI_API_KEY veya GOOGLE_API_KEY varsa onu kullanır.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)
    return genai.Client(api_key="DUMMY_KEY")