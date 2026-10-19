import time
import re
import json
from typing import Any, Dict, List
from app.tools.base import BaseTool, ToolResult
from app.tools.ssh_client import ssh_manager

SAFE_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]+$")

def validate_identifier(name: str, field_name: str = "identifier") -> None:
    if not name or not SAFE_NAME_REGEX.match(name):
        raise ValueError(f"Invalid {field_name}: '{name}'. Only alphanumeric characters, dashes, underscores, and dots are permitted.")

class DockerListContainersTool(BaseTool):
    name = "docker.list_containers"
    description = "List all running and stopped Docker containers with their status, ports, and images."
    category = "docker"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {
        "all": {"type": "boolean", "default": True, "description": "Include stopped containers"}
    }

    async def execute(self, all: bool = True, **kwargs) -> ToolResult:
        start_time = time.time()
        flag = "-a" if all else ""
        cmd = f'docker ps {flag} --format \'{{"id":"{{{{.ID}}}}","name":"{{{{.Names}}}}","image":"{{{{.Image}}}}","status":"{{{{.Status}}}}","state":"{{{{.State}}}}","ports":"{{{{.Ports}}}}","created":"{{{{.CreatedAt}}}}"}}\''
        
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        if code != 0:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=err or "Failed to list containers",
                exit_code=code,
                duration_ms=duration
            )

        containers = []
        for line in out.splitlines():
            line = line.strip()
            if line:
                try:
                    containers.append(json.loads(line))
                except Exception:
                    pass

        summary = f"Found {len(containers)} containers ({sum(1 for c in containers if 'Up' in c.get('status', ''))} running)."
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=summary,
            exit_code=0,
            duration_ms=duration,
            data={"containers": containers, "count": len(containers)}
        )

class DockerContainerStatusTool(BaseTool):
    name = "docker.container_status"
    description = "Get detailed status, health, and inspect info for a specific container."
    category = "docker"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {
        "container_name": {"type": "string", "required": True, "description": "Name or ID of container"}
    }

    async def execute(self, container_name: str, **kwargs) -> ToolResult:
        validate_identifier(container_name, "container_name")
        start_time = time.time()
        cmd = f'docker inspect {container_name} --format \'{{"id":"{{{{.Id}}}}","name":"{{{{.Name}}}}","status":"{{{{.State.Status}}}}","running":{{{{.State.Running}}}},"health":"{{{{if .State.Health}}}}{{{{.State.Health.Status}}}}{{{{else}}}}none{{{{end}}}}","restart_count":{{{{.RestartCount}}}},"started_at":"{{{{.State.StartedAt}}}}"}}\''
        
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        if code != 0:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=err or f"Container '{container_name}' not found",
                exit_code=code,
                duration_ms=duration
            )

        try:
            inspect_data = json.loads(out.strip())
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Container {container_name}: status={inspect_data.get('status')}, health={inspect_data.get('health')}",
                exit_code=0,
                duration_ms=duration,
                data=inspect_data
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Failed to parse inspect output: {e}",
                exit_code=-1,
                duration_ms=duration
            )

class DockerLogsTool(BaseTool):
    name = "docker.logs"
    description = "Fetch recent logs for a container."
    category = "docker"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {
        "container_name": {"type": "string", "required": True},
        "tail": {"type": "integer", "default": 100, "description": "Number of lines to return"}
    }

    async def execute(self, container_name: str, tail: int = 100, **kwargs) -> ToolResult:
        validate_identifier(container_name, "container_name")
        tail = max(1, min(1000, int(tail)))
        start_time = time.time()
        
        cmd = f"docker logs --tail {tail} {container_name} 2>&1"
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        return ToolResult(
            tool_name=self.name,
            success=(code == 0),
            output=out.strip(),
            error=err if code != 0 else None,
            exit_code=code,
            duration_ms=duration,
            data={"lines_returned": len(out.splitlines())}
        )

class DockerRestartTool(BaseTool):
    name = "docker.restart"
    description = "Restart a Docker container or compose service. Potentially causes momentary downtime."
    category = "docker"
    is_dangerous = True
    requires_approval = True
    parameters_schema = {
        "container_name": {"type": "string", "required": True}
    }

    async def execute(self, container_name: str, **kwargs) -> ToolResult:
        validate_identifier(container_name, "container_name")
        start_time = time.time()
        
        cmd = f"docker restart {container_name}"
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        success = (code == 0)
        return ToolResult(
            tool_name=self.name,
            success=success,
            output=f"Container {container_name} restarted successfully." if success else "",
            error=err if not success else None,
            exit_code=code,
            duration_ms=duration
        )

class DockerStopTool(BaseTool):
    name = "docker.stop"
    description = "Stop a running Docker container. Causes service downtime."
    category = "docker"
    is_dangerous = True
    requires_approval = True
    parameters_schema = {
        "container_name": {"type": "string", "required": True}
    }

    async def execute(self, container_name: str, **kwargs) -> ToolResult:
        validate_identifier(container_name, "container_name")
        start_time = time.time()
        
        cmd = f"docker stop {container_name}"
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        success = (code == 0)
        return ToolResult(
            tool_name=self.name,
            success=success,
            output=f"Container {container_name} stopped successfully." if success else "",
            error=err if not success else None,
            exit_code=code,
            duration_ms=duration
        )

class DockerStartTool(BaseTool):
    name = "docker.start"
    description = "Start a stopped Docker container."
    category = "docker"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {
        "container_name": {"type": "string", "required": True}
    }

    async def execute(self, container_name: str, **kwargs) -> ToolResult:
        validate_identifier(container_name, "container_name")
        start_time = time.time()
        
        cmd = f"docker start {container_name}"
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        success = (code == 0)
        return ToolResult(
            tool_name=self.name,
            success=success,
            output=f"Container {container_name} started successfully." if success else "",
            error=err if not success else None,
            exit_code=code,
            duration_ms=duration
        )
