"""
snapshot_manager.py - Safe Snapshot & Automated Rollback System

This module creates isolated backups of files before any modifications occur.
If repairs fail, are rejected by the Verifier Agent, or trigger unhandled errors,
the codebase can be automatically or manually restored to its exact pristine state.
"""

import os
import shutil
import time
from typing import Dict, List, Optional
from tools import read_file, write_file

class SnapshotManager:
    """Manages file snapshots and safe rollback states."""

    SNAPSHOT_DIR_NAME = ".hunter_snapshots"

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.getcwd()
        self.snapshot_dir = os.path.join(self.base_dir, self.SNAPSHOT_DIR_NAME)
        self.active_snapshots: Dict[str, Dict[str, str]] = {}

    def create_snapshot(self, file_paths: List[str]) -> str:
        """
        Creates an in-memory and disk snapshot of specified files.

        :param file_paths: List of file paths to back up
        :return: Unique snapshot identifier
        """
        snapshot_id = f"snap_{int(time.time() * 1000)}"
        target_snapshot_path = os.path.join(self.snapshot_dir, snapshot_id)
        os.makedirs(target_snapshot_path, exist_ok=True)

        snapshot_store = {}
        for file_path in file_paths:
            if os.path.exists(file_path):
                content = read_file(file_path)
                snapshot_store[file_path] = content
                
                # Also save to disk backup
                rel_path = os.path.relpath(file_path, self.base_dir).replace("..", "_")
                backup_file = os.path.join(target_snapshot_path, rel_path)
                os.makedirs(os.path.dirname(os.path.abspath(backup_file)), exist_ok=True)
                with open(backup_file, "w", encoding="utf-8") as f:
                    f.write(content)

        self.active_snapshots[snapshot_id] = snapshot_store
        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        Restores files from a specific snapshot ID.

        :param snapshot_id: ID of the snapshot to restore
        :return: True if restored successfully
        """
        if snapshot_id not in self.active_snapshots:
            # Check if exists on disk
            disk_path = os.path.join(self.snapshot_dir, snapshot_id)
            if not os.path.exists(disk_path):
                return False

        files_to_restore = self.active_snapshots.get(snapshot_id, {})
        for file_path, content in files_to_restore.items():
            write_file(file_path, content)

        print(f"🔙 [SnapshotManager] Rolled back {len(files_to_restore)} file(s) from snapshot '{snapshot_id}'.")
        return True

    def cleanup_snapshot(self, snapshot_id: str):
        """Removes a snapshot after successful verification."""
        if snapshot_id in self.active_snapshots:
            del self.active_snapshots[snapshot_id]
        disk_path = os.path.join(self.snapshot_dir, snapshot_id)
        if os.path.exists(disk_path):
            shutil.rmtree(disk_path, ignore_errors=True)
