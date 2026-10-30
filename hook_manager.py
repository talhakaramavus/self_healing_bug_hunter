"""
hook_manager.py - Git Pre-Commit Hook Integration Manager

This module enables automated installation and removal of Git pre-commit hooks,
allowing developers to enforce autonomous bug hunting and security scans
before code can be committed to the repository.
"""

import os
import stat
import subprocess
from typing import Tuple, Optional

class HookManager:
    """Installs, configures, and uninstalls git pre-commit hooks."""

    HOOK_SCRIPT_CONTENT = """#!/usr/bin/env sh
# Self-Healing Bug Hunter Pre-Commit Hook
# Prevents committing code containing critical security bugs or unverified flaws.

echo "🛡️ [Bug Hunter Hook] Running pre-commit autonomous verification..."

if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "⚠️ Python not found in PATH. Skipping Bug Hunter pre-commit check."
    exit 0
fi

$PY_CMD main.py --pre-commit
RESULT=$?

if [ $RESULT -ne 0 ]; then
    echo "❌ [Bug Hunter Hook] Critical flaws detected. Commit aborted."
    echo "👉 Run 'python main.py' to review or auto-patch before committing."
    exit 1
fi

echo "✅ [Bug Hunter Hook] Codebase clean. Proceeding with commit."
exit 0
"""

    @classmethod
    def install_pre_commit_hook(cls, repo_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        Installs the pre-commit hook script into the repository's .git/hooks directory.

        :param repo_dir: Path to git repository root (default: current working directory)
        :return: (is_success, message)
        """
        cwd = repo_dir or os.getcwd()
        git_dir = os.path.join(cwd, ".git")

        if not os.path.exists(git_dir):
            return False, f"Not a git repository: '{cwd}' (.git directory not found)."

        hooks_dir = os.path.join(git_dir, "hooks")
        os.makedirs(hooks_dir, exist_ok=True)
        hook_path = os.path.join(hooks_dir, "pre-commit")

        try:
            with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(cls.HOOK_SCRIPT_CONTENT)

            # Make hook executable on POSIX systems
            if hasattr(os, "chmod"):
                st = os.stat(hook_path)
                os.chmod(hook_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

            msg = f"Pre-commit hook successfully installed at: {hook_path}"
            return True, msg
        except Exception as e:
            return False, f"Failed to install pre-commit hook: {str(e)}"

    @classmethod
    def uninstall_pre_commit_hook(cls, repo_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        Removes the pre-commit hook from .git/hooks.

        :param repo_dir: Path to git repository root
        :return: (is_success, message)
        """
        cwd = repo_dir or os.getcwd()
        hook_path = os.path.join(cwd, ".git", "hooks", "pre-commit")

        if not os.path.exists(hook_path):
            return True, "No pre-commit hook was found to uninstall."

        try:
            os.remove(hook_path)
            return True, f"Pre-commit hook removed from: {hook_path}"
        except Exception as e:
            return False, f"Failed to uninstall pre-commit hook: {str(e)}"
