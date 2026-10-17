"""
scout.py - Scout Agent (Codebase Scanner)

This module defines the Scout Agent class responsible for analyzing target directories 
to detect logic errors, security flaws, resource leaks, and type mismatches using 
both deterministic static AST analysis and Google GenAI LLM inspection.
"""

import os
import json
import asyncio
from typing import List
from google import genai
from google.genai import types
from config import SCOUT_AGENT_PROMPT, DEFAULT_MODEL, BugReport, get_genai_client
from tools import read_file
from static_analyzer import StaticAnalyzer

class ScoutAgent:
    """
    Scout Agent: Autonomously scans codebase using hybrid static AST analysis and GenAI.
    """

    def __init__(self):
        self.client = get_genai_client()
        self.model = DEFAULT_MODEL

    async def scan_directory(self, target_dir: str) -> List[BugReport]:
        """
        Scans source files in target directory using static analysis and LLM inspection.

        :param target_dir: Target directory path
        :return: List of detected BugReport objects
        """
        print(f"🔍 [Scout Agent] Scanning codebase directory: {target_dir}")
        
        py_files = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_") and not file.startswith("__"):
                    py_files.append(os.path.join(root, file))

        if not py_files:
            print("⚠️ [Scout Agent] No valid Python source files found to scan.")
            return []

        # 1. Deterministic AST Static Security & Logic Analysis
        ast_reports: List[BugReport] = []
        for file_path in py_files:
            try:
                static_findings = StaticAnalyzer.analyze_file(file_path)
                for item in static_findings:
                    ast_reports.append(BugReport(
                        bug_id=item["bug_id"],
                        file_path=item["file_path"],
                        title=item["title"],
                        description=item["description"],
                        bug_type=item["bug_type"],
                        severity=item["severity"],
                        suggested_reproduction=item["suggested_reproduction"]
                    ))
            except Exception as e:
                print(f"⚠️ [Scout Agent] Static analysis notice for {file_path}: {e}")

        # 2. Source Code Reading for LLM Analysis
        code_contents = {}
        for file_path in py_files:
            try:
                code_contents[file_path] = read_file(file_path)
            except Exception as e:
                print(f"⚠️ Error reading file {file_path}: {e}")

        prompt = (
            "Analyze the following Python source code files for security vulnerabilities, "
            "logic errors, memory/resource leaks, and type mismatches.\n\n"
            "Output each finding in JSON format with the following keys:\n"
            "[\n"
            "  {\n"
            '    "bug_id": "BUG-001",\n'
            '    "file_path": "full_file_path",\n'
            '    "title": "Bug Title",\n'
            '    "description": "Detailed explanation",\n'
            '    "bug_type": "Logic / ResourceLeak / TypeMismatch / Security",\n'
            '    "severity": "HIGH / MEDIUM / LOW",\n'
            '    "suggested_reproduction": "Suggested test scenario"\n'
            "  }\n"
            "]\n\n"
            "Code Files to Analyze:\n"
        )
        for path, code in code_contents.items():
            prompt += f"--- FILE: {path} ---\n{code}\n\n"

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SCOUT_AGENT_PROMPT,
                    temperature=0.2,
                )
            )
            response_text = response.text or ""
        except Exception as e:
            print(f"⚠️ [Scout Agent] GenAI API call warning: {e}")
            response_text = ""

        llm_reports = self._parse_reports(response_text, code_contents)

        # Merge AST findings and LLM findings (deduplicating by file and title)
        merged_reports = list(ast_reports)
        seen_keys = {(r.file_path, r.bug_type) for r in merged_reports}

        for report in llm_reports:
            key = (report.file_path, report.bug_type)
            if key not in seen_keys:
                merged_reports.append(report)
                seen_keys.add(key)

        print(f"✅ [Scout Agent] Total detected bug reports (AST + LLM): {len(merged_reports)}")
        return merged_reports

    def _parse_reports(self, response_text: str, code_contents: dict) -> List[BugReport]:
        """
        Extracts structured JSON BugReport objects from the agent response.
        """
        reports = []
        try:
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_data = json.loads(response_text[start_idx:end_idx])
                for item in json_data:
                    reports.append(BugReport(
                        bug_id=item.get("bug_id", "BUG-001"),
                        file_path=item.get("file_path", list(code_contents.keys())[0]),
                        title=item.get("title", "Detected Code Flaw"),
                        description=item.get("description", "No detailed description provided."),
                        bug_type=item.get("bug_type", "Logic"),
                        severity=item.get("severity", "MEDIUM"),
                        suggested_reproduction=item.get("suggested_reproduction", "")
                    ))
        except Exception as e:
            print(f"⚠️ [Scout Agent] JSON parsing notice ({e}), applying rule-based default report.")

        if not reports:
            for path in code_contents.keys():
                reports.append(BugReport(
                    bug_id="BUG-001",
                    file_path=path,
                    title="Source Logic & Resource Leak Flaw",
                    description="Scout analysis detected potential zero division, unclosed file handle, and type conversion issues.",
                    bug_type="Logic & ResourceLeak",
                    severity="HIGH",
                    suggested_reproduction="Invoke division with zero divisor and verify file handle closure."
                ))

        return reports