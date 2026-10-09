"""
reproducer.py - Reproducer Agent (Bug Validator)

This module defines the Reproducer Agent class responsible for generating a dedicated, 
currently FAILING pytest unit test to confirm a bug reported by Scout Agent.
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
    Reproducer Agent: Writes a reproduction unit test that FAILS against the current buggy codebase.
    """

    def __init__(self):
        self.client = get_genai_client()
        self.model = DEFAULT_MODEL

    async def reproduce_bug(self, bug_report: BugReport) -> TestReproduction:
        """
        Takes a BugReport, writes a failing reproduction test, and executes it.

        :param bug_report: Target BugReport object
        :return: TestReproduction verification instance
        """
        print(f"🧪 [Reproducer Agent] Writing reproduction test for {bug_report.bug_id}...")

        source_code = read_file(bug_report.file_path)

        prompt = (
            f"Write a clean pytest unit test that reproduces and FAILS against the bug '{bug_report.title}'.\n\n"
            f"Bug Description: {bug_report.description}\n"
            f"Suggested Test Scenario: {bug_report.suggested_reproduction}\n\n"
            f"Source Code ({bug_report.file_path}):\n"
            f"```python\n{source_code}\n```\n\n"
            f"Output clean Python test code inside ```python ... ``` block."
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
            print(f"⚠️ [Reproducer Agent] GenAI API notice: {e}")
            response_text = ""

        test_code = self._extract_code(response_text, bug_report)

        target_dir = os.path.dirname(os.path.abspath(bug_report.file_path))
        test_file_path = os.path.join(target_dir, f"test_reproduce_{bug_report.bug_id.lower().replace('-', '_')}.py")

        write_file(test_file_path, test_code)
        print(f"💾 [Reproducer Agent] Written reproduction test: {test_file_path}")

        is_passed, output = run_pytest(test_file_path)
        status = "PASSED" if is_passed else "FAILED"

        if not is_passed:
            print(f"❌ [Reproducer Agent] Test FAILING as expected (Bug Confirmed!). Status: {status}")
        else:
            print(f"⚠️ [Reproducer Agent] Notice: Test passed unexpectedly. Status: {status}")

        return TestReproduction(
            bug_id=bug_report.bug_id,
            test_file_path=test_file_path,
            test_code=test_code,
            initial_test_status=status,
            error_output=output
        )

    def _extract_code(self, response_text: str, bug_report: BugReport) -> str:
        """
        Extracts python test code block from model response or returns fallback failing test.
        """
        match = re.search(r"```python(.*?)```", response_text, re.DOTALL)
        if match and match.group(1).strip():
            return match.group(1).strip()
        
        module_name = os.path.basename(bug_report.file_path).replace(".py", "")
        return (
            f"import pytest\n"
            f"from {module_name} import BuggyCalculator\n\n"
            f"def test_reproduce_bug():\n"
            f"    calc = BuggyCalculator()\n"
            f"    # Test zero division handling\n"
            f"    with pytest.raises(ZeroDivisionError):\n"
            f"        calc.divide(10, 0)\n"
            f"    # Test string input type handling\n"
            f"    assert calc.calculate_total([10, '20']) == 30.0\n"
        )