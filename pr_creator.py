"""
pr_creator.py - Automated Git Branch & GitHub Pull Request Creator

This module autonomously creates git branches, commits validated patches,
and creates GitHub Pull Requests using GitHub REST API or local git operations.
"""

import os
import subprocess
import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional, Dict, Any
from config import FixResult, VerificationResult

@dataclass
class PRCreationResult:
    """Result of automated branch and PR creation."""
    bug_id: str
    branch_name: str
    commit_sha: Optional[str]
    pr_url: Optional[str]
    status: str  # "PR_CREATED", "COMMITTED_LOCAL", "FAILED", "SKIPPED"
    message: str

class PullRequestCreator:
    """Creates dedicated git branches, commits verified patches, and publishes PRs."""

    @staticmethod
    def create_pr_for_fix(
        fix_result: FixResult, 
        verification: VerificationResult,
        repo_dir: Optional[str] = None
    ) -> PRCreationResult:
        """
        Creates a dedicated git branch and commits the verified patch.
        If GITHUB_TOKEN and remote repo are detected, attempts to create a Pull Request.

        :param fix_result: FixResult object containing patch and PR details
        :param verification: VerificationResult object confirming acceptance
        :param repo_dir: Base repository directory
        :return: PRCreationResult with branch, commit, and PR URL information
        """
        if not verification.is_accepted:
            return PRCreationResult(
                bug_id=fix_result.bug_id,
                branch_name="",
                commit_sha=None,
                pr_url=None,
                status="SKIPPED",
                message="Patch was not accepted by Verifier Agent. PR creation skipped."
            )

        cwd = repo_dir or os.getcwd()
        sanitized_id = fix_result.bug_id.lower().replace("-", "_").replace(" ", "_")
        branch_name = f"fix/bug_hunter_{sanitized_id}"

        try:
            # 1. Ensure git is available
            subprocess.run(["git", "status"], cwd=cwd, capture_output=True, check=True)

            # 2. Create or checkout branch
            subprocess.run(["git", "checkout", "-B", branch_name], cwd=cwd, capture_output=True, check=True)

            # 3. Stage the modified file
            rel_path = os.path.relpath(fix_result.fixed_file_path, cwd)
            subprocess.run(["git", "add", rel_path], cwd=cwd, capture_output=True, check=True)

            # 4. Commit patch
            commit_msg = f"{fix_result.pr_title}\n\n{fix_result.pr_body}\n\nVerified by Self-Healing Bug Hunter"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=cwd, capture_output=True, check=True)

            # Get commit hash
            commit_res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True)
            commit_sha = commit_res.stdout.strip()

            # 5. Check if GitHub Token is available for API PR creation
            github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            pr_url = None

            if github_token:
                pr_url = PullRequestCreator._try_github_api_pr(cwd, branch_name, fix_result, github_token)

            status = "PR_CREATED" if pr_url else "COMMITTED_LOCAL"
            msg = f"Branch '{branch_name}' committed ({commit_sha[:7]})." + (f" PR: {pr_url}" if pr_url else " Ready to push.")
            print(f"🚀 [PR Creator] {msg}")

            return PRCreationResult(
                bug_id=fix_result.bug_id,
                branch_name=branch_name,
                commit_sha=commit_sha,
                pr_url=pr_url,
                status=status,
                message=msg
            )

        except Exception as e:
            err_msg = f"Git operation failed: {str(e)}"
            print(f"⚠️ [PR Creator] {err_msg}")
            return PRCreationResult(
                bug_id=fix_result.bug_id,
                branch_name=branch_name,
                commit_sha=None,
                pr_url=None,
                status="FAILED",
                message=err_msg
            )

    @staticmethod
    def _try_github_api_pr(cwd: str, branch: str, fix_result: FixResult, token: str) -> Optional[str]:
        """Attempts to push branch and open a PR via GitHub REST API."""
        try:
            # Push branch
            subprocess.run(["git", "push", "-u", "origin", branch], cwd=cwd, capture_output=True, check=True)

            # Get origin URL to find owner/repo
            rem_res = subprocess.run(["git", "remote", "get-url", "origin"], cwd=cwd, capture_output=True, text=True)
            remote_url = rem_res.stdout.strip()
            
            # Parse owner/repo from remote URL (https or ssh)
            parts = remote_url.replace(".git", "").replace(":", "/").split("/")
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1]
                api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
                
                payload = json.dumps({
                    "title": fix_result.pr_title,
                    "body": fix_result.pr_body,
                    "head": branch,
                    "base": "main"
                }).encode("utf-8")

                req = urllib.request.Request(
                    api_url, 
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github.v3+json",
                        "Content-Type": "application/json",
                        "User-Agent": "Self-Healing-Bug-Hunter"
                    }
                )

                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    return resp_data.get("html_url")
        except Exception:
            return None
        return None
