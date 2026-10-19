import time
import re
from typing import Any, Dict
from app.tools.base import BaseTool, ToolResult
from app.tools.ssh_client import ssh_manager

class ServerGetStatusTool(BaseTool):
    name = "server.get_status"
    description = "Retrieve comprehensive server status, uptime, OS version, kernel, and overall health."
    category = "server"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {}

    async def execute(self, **kwargs) -> ToolResult:
        start_time = time.time()
        # Collect uname, uptime, systemd status
        cmd = "uname -srm; uptime -p 2>/dev/null || uptime; hostname"
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        if code != 0:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=err or "Failed to query server status",
                exit_code=code,
                duration_ms=duration
            )

        lines = [l.strip() for l in out.splitlines() if l.strip()]
        kernel = lines[0] if len(lines) > 0 else "Unknown"
        uptime_str = lines[1] if len(lines) > 1 else "Unknown"
        hostname = lines[2] if len(lines) > 2 else "vicky"

        # Check docker daemon
        d_code, d_out, _ = await ssh_manager.execute_command("docker info --format '{{.ServerVersion}}'")
        docker_version = d_out.strip() if d_code == 0 else "Offline / Inaccessible"

        data = {
            "hostname": hostname,
            "kernel": kernel,
            "uptime": uptime_str,
            "docker_version": docker_version,
            "ssh_status": "connected",
            "server_reachable": True
        }

        output_text = f"Server {hostname} is Online. Kernel: {kernel}. Uptime: {uptime_str}. Docker: {docker_version}."
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=output_text,
            exit_code=0,
            duration_ms=duration,
            data=data
        )

class ServerGetResourcesTool(BaseTool):
    name = "server.get_resources"
    description = "Retrieve current CPU, RAM, Disk, and Network usage metrics from the server."
    category = "server"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {}

    async def execute(self, **kwargs) -> ToolResult:
        start_time = time.time()
        # Parse free -b, df -B1 /, cat /proc/loadavg, cat /proc/net/dev
        cmd = """
        free -b | grep -E '^Mem:|^Swap:'
        echo '---DF---'
        df -B1 /home/stan 2>/dev/null | tail -n 1 || df -B1 / | tail -n 1
        echo '---LOAD---'
        cat /proc/loadavg
        echo '---NET---'
        cat /proc/net/dev | grep -v 'lo:' | grep ':' | head -n 2
        """
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        if code != 0:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=err or "Failed to read server resources",
                exit_code=code,
                duration_ms=duration
            )

        try:
            parts = out.split('---DF---')
            mem_part = parts[0].strip()
            rest = parts[1].split('---LOAD---')
            df_part = rest[0].strip()
            rest2 = rest[1].split('---NET---')
            load_part = rest2[0].strip()
            net_part = rest2[1].strip()

            # Memory
            mem_total, mem_used, mem_available = 0, 0, 0
            for line in mem_part.splitlines():
                if line.startswith("Mem:"):
                    tokens = line.split()
                    mem_total = int(tokens[1])
                    mem_used = int(tokens[2])
                    mem_available = int(tokens[6]) if len(tokens) > 6 else (mem_total - mem_used)

            ram_percent = round((mem_used / mem_total * 100), 1) if mem_total > 0 else 0

            # Disk
            df_tokens = df_part.split()
            disk_total = int(df_tokens[1]) if len(df_tokens) > 1 else 0
            disk_used = int(df_tokens[2]) if len(df_tokens) > 2 else 0
            disk_percent = round((disk_used / disk_total * 100), 1) if disk_total > 0 else 0

            # Load avg
            load_tokens = load_part.split()
            load1 = float(load_tokens[0]) if len(load_tokens) > 0 else 0.0
            load5 = float(load_tokens[1]) if len(load_tokens) > 1 else 0.0
            load15 = float(load_tokens[2]) if len(load_tokens) > 2 else 0.0

            # Network
            rx_bytes, tx_bytes = 0, 0
            for nline in net_part.splitlines():
                if ":" in nline:
                    nparts = nline.split(":")[1].split()
                    if len(nparts) >= 9:
                        rx_bytes += int(nparts[0])
                        tx_bytes += int(nparts[8])

            data = {
                "cpu_load": {"load1": load1, "load5": load5, "load15": load15},
                "cpu_percent": min(100.0, round(load1 * 12.5, 1)), # Approximate for 8 cores
                "ram": {
                    "total_bytes": mem_total,
                    "used_bytes": mem_used,
                    "available_bytes": mem_available,
                    "percent": ram_percent,
                    "total_human": f"{round(mem_total / (1024**3), 1)} GB",
                    "used_human": f"{round(mem_used / (1024**3), 1)} GB"
                },
                "disk": {
                    "total_bytes": disk_total,
                    "used_bytes": disk_used,
                    "percent": disk_percent,
                    "total_human": f"{round(disk_total / (1024**3), 1)} GB",
                    "used_human": f"{round(disk_used / (1024**3), 1)} GB"
                },
                "network": {
                    "rx_bytes": rx_bytes,
                    "tx_bytes": tx_bytes,
                    "rx_human": f"{round(rx_bytes / (1024**2), 1)} MB",
                    "tx_human": f"{round(tx_bytes / (1024**2), 1)} MB"
                }
            }

            output_text = (
                f"Resources: CPU Load: {load1:.2f}, RAM: {ram_percent}% "
                f"({data['ram']['used_human']} / {data['ram']['total_human']}), "
                f"Disk: {disk_percent}% ({data['disk']['used_human']} / {data['disk']['total_human']})."
            )

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output_text,
                exit_code=0,
                duration_ms=duration,
                data=data
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Parsing error: {str(e)}",
                exit_code=-1,
                duration_ms=duration
            )
