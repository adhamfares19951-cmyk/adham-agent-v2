"""System & Workspace Monitor Agent for adham-agent.

Features:
- Monitors workspace health, disk usage, and host diagnostics.
- Inspects workspace_data/youtube_ready/ for rendered MP4 video drops ready for upload.
- Checks SQLite database state and row statistics across all 5 core tables.
- Cleans and rotates execution logs in workspace_data/logs/.
- Processes blackboard tasks for sys_agent.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from config.settings import settings
from core.database import db_manager, DatabaseManager

logger = logging.getLogger("adham_agent.agents.sys")


# =============================================================================
# Pydantic Schemas for Strict Structured Output
# =============================================================================

class SystemHealthReport(BaseModel):
    """Structured report of workspace and host operational metrics."""
    timestamp: str = Field(description="ISO timestamp of health snapshot")
    workspace_status: str = Field(description="Operational health indicator (e.g., 'HEALTHY', 'DEGRADED', 'ACTION_REQUIRED')")
    ready_videos_count: int = Field(description="Number of rendered MP4 videos in youtube_ready directory")
    ready_video_files: List[str] = Field(description="List of filenames waiting for YouTube upload")
    database_stats: Dict[str, int] = Field(description="Table row counts across all 5 core SQLite tables")
    system_resources: Dict[str, Any] = Field(description="Operating system, platform, CPU, and disk metrics")
    logs_status: str = Field(description="Summary of rotating log volume and status")


class SysAgent:
    """Workspace Operations & Infrastructure Monitor Agent."""

    def __init__(
        self,
        db: Optional[DatabaseManager] = None,
    ) -> None:
        self.db = db or db_manager
        self.ready_dir = settings.youtube_ready_dir
        self.logs_dir = settings.logs_dir
        self.data_dir = settings.WORKSPACE_DATA_DIR

    async def get_database_stats(self) -> Dict[str, int]:
        """Query row counts across all 5 core tables."""
        stats: Dict[str, int] = {}
        tables = [
            "memory_profile",
            "leads_and_jobs",
            "youtube_characters",
            "youtube_videos",
            "agent_tasks",
        ]

        async with self.db.get_connection() as conn:
            for table in tables:
                try:
                    async with conn.execute(f"SELECT COUNT(*) FROM {table}") as cursor:
                        row = await cursor.fetchone()
                        stats[table] = row[0] if row else 0
                except Exception as e:
                    logger.warning("Could not query table %s count: %s", table, e)
                    stats[table] = -1

        return stats

    def get_system_resources(self) -> Dict[str, Any]:
        """Gather platform and disk utilization metrics."""
        disk_usage = shutil.disk_usage(str(self.data_dir))
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "disk_total_gb": round(disk_usage.total / (1024**3), 2),
            "disk_used_gb": round(disk_usage.used / (1024**3), 2),
            "disk_free_gb": round(disk_usage.free / (1024**3), 2),
            "disk_free_percent": round((disk_usage.free / disk_usage.total) * 100, 1),
        }

    def rotate_logs(self, max_size_mb: int = 10) -> str:
        """Rotate and prune log files exceeding max_size_mb threshold."""
        rotated_count = 0
        max_bytes = max_size_mb * 1024 * 1024

        for log_file in self.logs_dir.glob("*.log"):
            try:
                if log_file.stat().st_size > max_bytes:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    archived = self.logs_dir / f"{log_file.stem}_{timestamp}.log.bak"
                    log_file.rename(archived)
                    # Re-create empty file
                    log_file.touch()
                    rotated_count += 1
                    logger.info("Rotated log file: %s -> %s", log_file.name, archived.name)
            except Exception as e:
                logger.error("Error rotating log file %s: %s", log_file, e)

        return f"Rotated {rotated_count} log files exceeding {max_size_mb}MB."

    async def check_system_health(self) -> SystemHealthReport:
        """Run a full health check across storage, pipeline directories, and database."""
        ready_files = [f.name for f in self.ready_dir.glob("*.mp4")]
        db_stats = await self.get_database_stats()
        resources = self.get_system_resources()
        logs_info = self.rotate_logs()

        status = "HEALTHY"
        if resources.get("disk_free_percent", 100) < 10.0:
            status = "ACTION_REQUIRED: LOW_DISK_SPACE"

        report = SystemHealthReport(
            timestamp=datetime.utcnow().isoformat(),
            workspace_status=status,
            ready_videos_count=len(ready_files),
            ready_video_files=ready_files,
            database_stats=db_stats,
            system_resources=resources,
            logs_status=logs_info,
        )
        return report

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch blackboard task assigned to sys_agent."""
        task_type = task.get("task_type", "").upper().strip()

        logger.info("SysAgent processing task_type: %s", task_type)

        if task_type in ("MONITOR_HEALTH", "CHECK_HEALTH", "SYS_REPORT"):
            report = await self.check_system_health()
            return {
                "status": "SUCCESS",
                "workspace_status": report.workspace_status,
                "ready_videos": report.ready_videos_count,
                "database_stats": report.database_stats,
                "report": report.model_dump(),
            }

        elif task_type in ("INSPECT_READY_VIDEOS", "SCAN_VIDEOS"):
            ready_files = [str(f) for f in self.ready_dir.glob("*.mp4")]
            return {
                "status": "SUCCESS",
                "count": len(ready_files),
                "ready_videos": ready_files,
            }

        elif task_type in ("ROTATE_LOGS", "CLEAN_LOGS"):
            result_str = self.rotate_logs()
            return {
                "status": "SUCCESS",
                "message": result_str,
            }

        else:
            raise ValueError(f"SysAgent does not support task_type: '{task_type}'")


# Singleton instance
sys_agent = SysAgent()
