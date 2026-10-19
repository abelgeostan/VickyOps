import time
import os
import datetime
from typing import Any, Dict, Optional, List
from app.tools.base import BaseTool, ToolResult
from app.tools.ssh_client import ssh_manager
from app.tools.docker_tools import validate_identifier

BACKUP_DIR = "/home/vickyops/backups"

class BackupCreateTool(BaseTool):
    name = "backup.create"
    description = "Create a timestamped compressed backup archive of a service directory before updates."
    category = "backup"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {
        "service_path": {"type": "string", "required": True},
        "service_name": {"type": "string", "required": True}
    }

    async def execute(self, service_path: str, service_name: str, **kwargs) -> ToolResult:
        validate_identifier(service_name, "service_name")
        start_time = time.time()
        
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{service_name}_backup_{timestamp}.tar.gz"
        backup_full_path = f"{BACKUP_DIR}/{backup_file}"

        cmd = f"""
        mkdir -p "{BACKUP_DIR}"
        tar --exclude='.git' --exclude='node_modules' --exclude='venv' -czf "{backup_full_path}" -C "{os.path.dirname(service_path)}" "{os.path.basename(service_path)}" 2>&1
        stat -c%s "{backup_full_path}" 2>/dev/null || wc -c < "{backup_full_path}"
        """
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        if code != 0:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=err or f"Backup creation failed: {out}",
                exit_code=code,
                duration_ms=duration
            )

        lines = out.strip().splitlines()
        size_bytes = int(lines[-1].strip()) if lines and lines[-1].strip().isdigit() else 0
        size_mb = round(size_bytes / (1024 * 1024), 2)

        data = {
            "backup_file": backup_file,
            "backup_path": backup_full_path,
            "size_bytes": size_bytes,
            "size_mb": size_mb,
            "service_name": service_name,
            "created_at": datetime.datetime.utcnow().isoformat()
        }

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"Backup for {service_name} created successfully: {backup_file} ({size_mb} MB).",
            exit_code=0,
            duration_ms=duration,
            data=data
        )

class BackupListTool(BaseTool):
    name = "backup.list"
    description = "List all stored backup archives."
    category = "backup"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {}

    async def execute(self, **kwargs) -> ToolResult:
        start_time = time.time()
        cmd = f'mkdir -p "{BACKUP_DIR}" && ls -lh --time-style=+"%Y-%m-%d %H:%M:%S" "{BACKUP_DIR}" | grep -E "\\.tar\\.gz$"'
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        backups = []
        for line in out.splitlines():
            tokens = line.strip().split()
            if len(tokens) >= 7:
                size_str = tokens[4]
                dt_str = f"{tokens[5]} {tokens[6]}"
                filename = tokens[7]
                backups.append({
                    "filename": filename,
                    "size": size_str,
                    "date": dt_str,
                    "path": f"{BACKUP_DIR}/{filename}"
                })

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"Found {len(backups)} backups.",
            exit_code=0,
            duration_ms=duration,
            data={"backups": backups, "count": len(backups)}
        )

class BackupRestoreTool(BaseTool):
    name = "backup.restore"
    description = "Restore a service from a backup archive. Replaces files and requires downtime."
    category = "backup"
    is_dangerous = True
    requires_approval = True
    parameters_schema = {
        "backup_filename": {"type": "string", "required": True},
        "target_path": {"type": "string", "required": True}
    }

    async def execute(self, backup_filename: str, target_path: str, **kwargs) -> ToolResult:
        validate_identifier(backup_filename.replace(".", "_").replace("-", "_"), "backup_filename")
        start_time = time.time()

        cmd = f'tar -xzf "{BACKUP_DIR}/{backup_filename}" -C "{os.path.dirname(target_path)}" 2>&1'
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        success = (code == 0)
        return ToolResult(
            tool_name=self.name,
            success=success,
            output=f"Restored {backup_filename} to {target_path} successfully." if success else "",
            error=err if not success else None,
            exit_code=code,
            duration_ms=duration
        )
