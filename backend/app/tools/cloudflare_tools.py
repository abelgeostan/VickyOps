import time
import json
from typing import Any, Dict, List
from app.tools.base import BaseTool, ToolResult
from app.tools.ssh_client import ssh_manager

class CloudflareGetStatusTool(BaseTool):
    name = "cloudflare.get_status"
    description = "Check Cloudflare Tunnel daemon and container connectivity without exposing tokens."
    category = "cloudflare"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {}

    async def execute(self, **kwargs) -> ToolResult:
        start_time = time.time()
        # Query containers with cloudflared image safely
        cmd = """
        docker ps -a --filter ancestor=cloudflare/cloudflared:latest --format '{"name":"{{.Names}}","status":"{{.Status}}","running":"{{.State}}"}'
        """
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        if code != 0:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=err or "Failed to query Cloudflare tunnels",
                exit_code=code,
                duration_ms=duration
            )

        tunnels = []
        for line in out.splitlines():
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    # Redact any sensitive command flags; only display container name and sanitized status
                    is_running = "Up" in data.get("status", "")
                    tunnels.append({
                        "name": data.get("name"),
                        "status": data.get("status"),
                        "is_connected": is_running,
                        "health": "healthy" if is_running else "disconnected"
                    })
                except Exception:
                    pass

        active_count = sum(1 for t in tunnels if t.get("is_connected"))
        summary = f"Cloudflare Tunnels: {active_count}/{len(tunnels)} active and connected."

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=summary,
            exit_code=0,
            duration_ms=duration,
            data={
                "tunnel_count": len(tunnels),
                "active_count": active_count,
                "overall_status": "operational" if active_count > 0 else "offline",
                "tunnels": tunnels
            }
        )
