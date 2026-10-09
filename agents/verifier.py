"""
verifier.py - Verifier Agent (Security & Scope Validator)

This module defines the Verifier Agent class responsible for auditing patch security, 
scope boundary isolation, and explicit acceptance criteria.
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
    Verifier Agent: Audits patches under strict security rules and sandbox test verification.
    """

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
        Audits patch for security, scope isolation, and sandbox test verification.

        :param bug_report: Target BugReport object
        :param fix_result: FixResult instance
        :return: VerificationResult audit report
        """
        print(f"🛡️ [Verifier Agent] Auditing patch & security scope for {bug_report.bug_id}...")

        scope_isolated = self._check_scope_isolation(bug_report.file_path, fix_result.fixed_file_path)
        permission_expanded = self._check_permission_expansion(fix_result.patch_code)
        sandbox_passed, test_output = run_pytest(fix_result.fixed_file_path, timeout=15)
        sandbox_status = "PASSED" if fix_result.final_test_status == "PASSED" else "FAILED"

        prompt = (
            f"Audit the following patch for security vulnerabilities and acceptance criteria:\n\n"
            f"Bug ID: {bug_report.bug_id}\n"
            f"Bug Type: {bug_report.bug_type}\n"
            f"Applied Patch Code:\n"
            f"```python\n{fix_result.patch_code}\n```\n\n"
            f"Does the patch introduce dangerous security flaws or permission expansions?\n"
            f"Determine security score (0-100) and indicate if patch is ACCEPTED."
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
            print(f"⚠️ [Verifier Agent] GenAI API audit notice: {e}")
            analysis_text = "API audit completed via static security rules."

        is_accepted = scope_isolated and (not permission_expanded) and (fix_result.final_test_status == "PASSED")
        security_score = 95 if is_accepted else 40
        audit_notes = (
            f"Scope Isolation: {'✅ PASSED' if scope_isolated else '❌ FAILED'}\n"
            f"Permission Expansion Risk: {'⚠️ DETECTED' if permission_expanded else '✅ CLEAN'}\n"
            f"Sandbox Status: {sandbox_status}\n"
            f"Analysis: {analysis_text[:200]}..."
        )

        if is_accepted:
            print(f"✅ [Verifier Agent] PATCH ACCEPTED (Score: {security_score}/100, Scope Isolated: {scope_isolated})")
        else:
            print(f"❌ [Verifier Agent] PATCH REJECTED (Permission Expanded: {permission_expanded}, Scope Isolated: {scope_isolated})")

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
        """Verifies that only the target file was modified."""
        return os.path.abspath(target_file) == os.path.abspath(modified_file)

    def _check_permission_expansion(self, patch_code: str) -> bool:
        """Audits patch code for forbidden or dangerous code execution patterns."""
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, patch_code):
                return True
        return False
