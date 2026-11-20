import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.config import settings

class SnapshotMetadata(BaseModel):
    snapshot_id: str
    description: str
    timestamp: str
    file_count: int
    total_size_bytes: int
    files: List[str]

class SnapshotManager:
    """Manages point-in-time workspace rollback checkpoints."""

    def __init__(self, workspace_dir: Optional[str] = None, storage_dir: Optional[str] = None):
        self.workspace_root = Path(workspace_dir or settings.workspace_dir).resolve()
        base_dir = Path(storage_dir or os.path.join(os.path.dirname(self.workspace_root), ".tripwire_snapshots"))
        self.storage_root = base_dir.resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, description: str = "Pre-execution checkpoint") -> SnapshotMetadata:
        """Create a point-in-time filesystem snapshot of the workspace."""
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        snapshot_id = f"snap_{timestamp_str}"
        target_dir = self.storage_root / snapshot_id
        target_dir.mkdir(parents=True, exist_ok=True)

        files_copied: List[str] = []
        total_size = 0

        # Recursively copy all non-hidden workspace files
        for item in self.workspace_root.rglob("*"):
            if item.is_file():
                # Skip caches or temp files
                rel_path = item.relative_to(self.workspace_root)
                if "__pycache__" in rel_path.parts or any(p.startswith(".") for p in rel_path.parts):
                    continue

                dest = target_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
                files_copied.append(str(rel_path).replace("\\", "/"))
                total_size += item.stat().st_size

        meta = SnapshotMetadata(
            snapshot_id=snapshot_id,
            description=description,
            timestamp=datetime.now(timezone.utc).isoformat(),
            file_count=len(files_copied),
            total_size_bytes=total_size,
            files=files_copied,
        )

        return meta

    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Rollback workspace to a previous snapshot state."""
        source_dir = self.storage_root / snapshot_id
        if not source_dir.exists() or not source_dir.is_dir():
            raise FileNotFoundError(f"Snapshot '{snapshot_id}' does not exist")

        # Clear existing workspace non-hidden files
        for item in self.workspace_root.iterdir():
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

        # Copy back from snapshot
        for item in source_dir.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(source_dir)
                dest = self.workspace_root / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

        return True

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all available snapshots."""
        results = []
        for snap_dir in sorted(self.storage_root.iterdir(), reverse=True):
            if snap_dir.is_dir() and snap_dir.name.startswith("snap_"):
                files = [str(f.relative_to(snap_dir)).replace("\\", "/") for f in snap_dir.rglob("*") if f.is_file()]
                results.append({
                    "snapshot_id": snap_dir.name,
                    "created_at": snap_dir.stat().st_mtime,
                    "file_count": len(files),
                })
        return results

