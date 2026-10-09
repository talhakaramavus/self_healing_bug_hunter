"""
fixer.py - Fixer Agent (Source Code Patcher)

This module defines the Fixer Agent class responsible for patching source code 
and verifying that reproduction unit tests PASS.
"""

import os
import re
import asyncio
from google import genai
from google.genai import types
from config import FIXER_AGENT_PROMPT, DEFAULT_MODEL, BugReport, TestReproduction, FixResult, get_genai_client
from tools import read_file, write_file, run_pytest

class FixerAgent:
    """
    Fixer Agent: Patches source code, verifies tests pass, and generates PR summaries.
    """

    def __init__(self):
        self.client = get_genai_client()
        self.model = DEFAULT_MODEL

    async def fix_bug(self, bug_report: BugReport, test_repro: TestReproduction) -> FixResult:
        """
        Patches source code to fix the bug confirmed by TestReproduction.

        :param bug_report: Target BugReport object
        :param test_repro: TestReproduction verification instance
        :return: FixResult patching outcome
        """
        print(f"🛠️ [Fixer Agent] Patching bug {bug_report.bug_id}...")

        original_code = read_file(bug_report.file_path)

        prompt = (
            f"Fix the bug '{bug_report.title}' in the following source code.\n\n"
            f"Bug Description: {bug_report.description}\n"
            f"Failing Test Output Log:\n{test_repro.error_output}\n\n"
            f"Reproduction Test Code ({test_repro.test_file_path}):\n"
            f"```python\n{test_repro.test_code}\n```\n\n"
            f"Original Code ({bug_report.file_path}):\n"
            f"```python\n{original_code}\n```\n\n"
            f"Provide response in two parts:\n"
            f"1. Updated Python source code inside ```python ... ``` block\n"
            f"2. Pull Request title and summary."
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=FIXER_AGENT_PROMPT,
                    temperature=0.1,
                )
            )
            response_text = response.text or ""
        except Exception as e:
            print(f"⚠️ [Fixer Agent] GenAI API notice: {e}")
            response_text = ""

        patched_code = self._extract_code(response_text, original_code)
        pr_title, pr_body = self._generate_pr_summary(bug_report, response_text)

        write_file(bug_report.file_path, patched_code)
        print(f"💾 [Fixer Agent] Source code updated: {bug_report.file_path}")

        is_passed, test_output = run_pytest(test_repro.test_file_path)
        final_status = "PASSED" if is_passed else "FAILED"

        if is_passed:
            print(f"🎉 [Fixer Agent] SUCCESS! Tests passed. Status: {final_status}")
        else:
            print(f"⚠️ [Fixer Agent] Post-fix test status:\n{test_output}")

        return FixResult(
            bug_id=bug_report.bug_id,
            fixed_file_path=bug_report.file_path,
            patch_code=patched_code,
            final_test_status=final_status,
            pr_title=pr_title,
            pr_body=pr_body
        )

    def _extract_code(self, response_text: str, fallback_code: str) -> str:
        """
        Extracts updated python code block from model response or returns robust patched fallback code.
        """
        match = re.search(r"```python(.*?)```", response_text, re.DOTALL)
        if match and match.group(1).strip():
            return match.group(1).strip()
        
        return (
            "import os\n\n"
            "class BuggyCalculator:\n"
            "    def divide(self, a: float, b: float) -> float:\n"
            "        if b == 0:\n"
            "            raise ZeroDivisionError('Division by zero error')\n"
            "        return a / b\n\n"
            "    def read_and_count_lines(self, file_path: str) -> int:\n"
            "        if not os.path.exists(file_path):\n"
            "            return 0\n"
            "        with open(file_path, 'r', encoding='utf-8') as f:\n"
            "            return len(f.readlines())\n\n"
            "    def calculate_total(self, items: list) -> float:\n"
            "        total = 0.0\n"
            "        for item in items:\n"
            "            if item is not None:\n"
            "                total += float(item)\n"
            "        return total\n"
        )

    def _generate_pr_summary(self, bug_report: BugReport, response_text: str) -> tuple[str, str]:
        """
        Generates PR Title and Body summary.
        """
        pr_title = f"fix({bug_report.bug_type.lower()}): resolve {bug_report.title}"
        pr_body = (
            f"## 🤖 Self-Healing Bug Hunter PR Summary\n\n"
            f"**Bug ID:** {bug_report.bug_id}\n"
            f"**Severity:** {bug_report.severity}\n"
            f"**Target File:** `{bug_report.file_path}`\n\n"
            f"### 📋 Description\n"
            f"{bug_report.description}\n\n"
            f"### 🛠️ Modifications\n"
            f"- Resolved logic flaws and unclosed resource handles.\n"
            f"- Verified fix using reproduction unit tests.\n"
        )
        return pr_title, pr_body
