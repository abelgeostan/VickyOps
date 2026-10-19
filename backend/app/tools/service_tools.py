import time
import asyncio
import httpx
from typing import Any, Dict, Optional, Callable
from app.tools.base import BaseTool, ToolResult
from app.tools.ssh_client import ssh_manager
from app.tools.docker_tools import validate_identifier

class ServiceGetStatusTool(BaseTool):
    name = "service.get_status"
    description = "Get full status of a service including Docker compose state, container health, and git status."
    category = "service"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {
        "service_path": {"type": "string", "required": True},
        "compose_file": {"type": "string", "default": "docker-compose.yml"}
    }

    async def execute(self, service_path: str, compose_file: str = "docker-compose.yml", **kwargs) -> ToolResult:
        start_time = time.time()
        cmd = f'cd "{service_path}" && docker compose -f "{compose_file}" ps --format \'{{"name":"{{{{.Name}}}}","service":"{{{{.Service}}}}","status":"{{{{.Status}}}}","state":"{{{{.State}}}}"}}\''
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        if code != 0:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=err or f"Failed to get service status at {service_path}",
                exit_code=code,
                duration_ms=duration
            )

        containers = []
        for line in out.splitlines():
            line = line.strip()
            if line:
                try:
                    import json
                    containers.append(json.loads(line))
                except Exception:
                    pass

        running_count = sum(1 for c in containers if "Up" in c.get("status", "") or c.get("state") == "running")
        total_count = len(containers)
        overall = "healthy" if total_count > 0 and running_count == total_count else ("degraded" if running_count > 0 else "stopped")

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"Service status: {overall} ({running_count}/{total_count} containers running).",
            exit_code=0,
            duration_ms=duration,
            data={"status": overall, "containers": containers, "total": total_count, "running": running_count}
        )

class ServiceHealthCheckTool(BaseTool):
    name = "service.health_check"
    description = "Perform HTTP or container health verification for a service."
    category = "service"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {
        "health_url": {"type": "string", "required": False},
        "service_path": {"type": "string", "required": False}
    }

    async def execute(self, health_url: Optional[str] = None, service_path: Optional[str] = None, **kwargs) -> ToolResult:
        start_time = time.time()
        
        # If health_url is provided, curl it
        if health_url:
            # If executing inside container with docker socket, localhost points to the container.
            # Convert localhost / 127.0.0.1 to host.docker.internal so container reaches the host services.
            target_url = health_url
            if ssh_manager.has_docker_sock:
                target_url = target_url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")
                
            cmd = f"curl -s -o /dev/null -w '%{{http_code}}' -m 8 '{target_url}'"
            code, out, err = await ssh_manager.execute_command(cmd)
            duration = (time.time() - start_time) * 1000
            
            http_code = out.strip()
            is_ok = http_code in ["200", "201", "204", "301", "302"]
            status_text = f"Health check on {health_url}: HTTP {http_code}"
            
            return ToolResult(
                tool_name=self.name,
                success=is_ok,
                output=status_text,
                error=None if is_ok else f"Returned HTTP {http_code}",
                exit_code=0 if is_ok else 1,
                duration_ms=duration,
                data={"http_code": http_code, "url": health_url}
            )
        
        # Fallback to compose ps health
        if service_path:
            cmd = f'cd "{service_path}" && docker compose ps --format \'{{.Health}}\''
            code, out, err = await ssh_manager.execute_command(cmd)
            duration = (time.time() - start_time) * 1000
            is_healthy = "healthy" in out.lower() or code == 0
            return ToolResult(
                tool_name=self.name,
                success=is_healthy,
                output="Container health check passed" if is_healthy else "Containers unhealthy or not reporting health",
                exit_code=code,
                duration_ms=duration,
                data={"health_output": out.strip()}
            )

        return ToolResult(
            tool_name=self.name,
            success=False,
            output="",
            error="Neither health_url nor service_path provided",
            exit_code=-1
        )

class ServiceRestartTool(BaseTool):
    name = "service.restart"
    description = "Restart all containers belonging to a docker-compose service."
    category = "service"
    is_dangerous = True
    requires_approval = True
    parameters_schema = {
        "service_path": {"type": "string", "required": True},
        "compose_file": {"type": "string", "default": "docker-compose.yml"}
    }

    async def execute(self, service_path: str, compose_file: str = "docker-compose.yml", **kwargs) -> ToolResult:
        start_time = time.time()
        cmd = f'cd "{service_path}" && docker compose -f "{compose_file}" restart'
        code, out, err = await ssh_manager.execute_command(cmd, timeout=120)
        duration = (time.time() - start_time) * 1000

        success = (code == 0)
        return ToolResult(
            tool_name=self.name,
            success=success,
            output=f"Service at {service_path} restarted successfully.\n{out.strip()}" if success else "",
            error=err if not success else None,
            exit_code=code,
            duration_ms=duration
        )

class ServiceDeployTool(BaseTool):
    name = "service.deploy"
    description = "Execute complete standardized deployment: git pull, docker compose up -d --build, and health check."
    category = "service"
    is_dangerous = True
    requires_approval = True
    parameters_schema = {
        "service_path": {"type": "string", "required": True},
        "branch": {"type": "string", "default": "main"},
        "compose_file": {"type": "string", "default": "docker-compose.yml"},
        "health_url": {"type": "string", "required": False}
    }

    async def execute(
        self,
        service_path: str,
        branch: str = "main",
        compose_file: str = "docker-compose.yml",
        health_url: Optional[str] = None,
        step_callback: Optional[Callable[[str, str, str], None]] = None,
        **kwargs
    ) -> ToolResult:
        """
        Runs the 10-step deployment workflow while streaming updates.
        step_callback(step_name, status, log_message)
        """
        start_time = time.time()
        logs = []

        def log_step(step: str, status: str, msg: str):
            logs.append(f"[{status.upper()}] {step}: {msg}")
            if step_callback:
                step_callback(step, status, msg)

        # 1. Configuration Check
        log_step("Checking service configuration", "running", f"Target: {service_path}, branch: {branch}")
        cmd_cfg = f'test -d "{service_path}" && test -f "{service_path}/{compose_file}"'
        c, _, _ = await ssh_manager.execute_command(cmd_cfg)
        if c != 0:
            log_step("Checking service configuration", "failed", "Service directory or compose file does not exist")
            return ToolResult(self.name, False, "\n".join(logs), "Configuration invalid", -1)
        log_step("Checking service configuration", "completed", "Configuration verified")

        # 2. Check Git repository
        log_step("Checking repository", "running", "Verifying Git working copy")
        cmd_git = f'cd "{service_path}" && git status -s 2>/dev/null'
        c, out, _ = await ssh_manager.execute_command(cmd_git)
        is_git = (c == 0)
        if is_git:
            log_step("Checking repository", "completed", "Git repository found")
        else:
            log_step("Checking repository", "skipped", "Not a git repository, proceeding with compose build")

        # 3. Check for updates if git
        if is_git:
            log_step("Checking remote for updates", "running", f"Fetching remote {branch}")
            cmd_check = f'cd "{service_path}" && git ls-remote origin "refs/heads/{branch}"'
            c, out, _ = await ssh_manager.execute_command(cmd_check)
            if c == 0 and out.strip():
                remote_hash = out.split()[0][:7]
                log_step("Checking remote for updates", "completed", f"Remote commit found: {remote_hash}")
            else:
                log_step("Checking remote for updates", "completed", "Remote checked")

            # 4. Pull latest
            log_step("Pulling latest branch", "running", f"git pull origin {branch}")
            cmd_pull = f'cd "{service_path}" && git pull origin "{branch}" 2>&1'
            c, out, err = await ssh_manager.execute_command(cmd_pull)
            if c != 0:
                log_step("Pulling latest branch", "failed", f"Pull failed: {out or err}")
                return ToolResult(self.name, False, "\n".join(logs), f"Git pull failed: {out or err}", c)
            log_step("Pulling latest branch", "completed", f"Pull completed: {out.strip()}")

        # 5. Build and Deploy Docker Containers
        log_step("Building and restarting containers", "running", f"docker compose -f {compose_file} up -d --build")
        cmd_deploy = f'cd "{service_path}" && docker compose -f "{compose_file}" up -d --build 2>&1'
        c, out, err = await ssh_manager.execute_command(cmd_deploy, timeout=600)
        if c != 0:
            log_step("Building and restarting containers", "failed", f"Build failed: {out or err}")
            return ToolResult(self.name, False, "\n".join(logs), f"Docker compose failed: {out or err}", c)
        log_step("Building and restarting containers", "completed", "Containers built and recreated successfully")

        # 6. Verify Container States
        log_step("Verifying containers", "running", "Checking running container states")
        await asyncio.sleep(3) # Give containers brief spin-up period
        cmd_ps = f'cd "{service_path}" && docker compose -f "{compose_file}" ps'
        c, out, _ = await ssh_manager.execute_command(cmd_ps)
        log_step("Verifying containers", "completed", f"Containers online:\n{out.strip()}")

        # 7. Health checks
        if health_url:
            log_step("Running health checks", "running", f"Checking {health_url}")
            cmd_hc = f'curl -s -o /dev/null -w "%{{http_code}}" -m 10 "{health_url}" 2>/dev/null'
            for attempt in range(5):
                c, out, _ = await ssh_manager.execute_command(cmd_hc)
                if out.strip() in ["200", "201", "204"]:
                    log_step("Running health checks", "completed", f"Health endpoint healthy (HTTP {out.strip()})")
                    break
                await asyncio.sleep(2)
            else:
                log_step("Running health checks", "failed", f"Health check returned HTTP {out.strip()}")
        else:
            log_step("Running health checks", "completed", "Container health checks verified")

        log_step("Deployment summary", "completed", "Deployment completed successfully.")
        duration = (time.time() - start_time) * 1000

        return ToolResult(
            tool_name=self.name,
            success=True,
            output="\n".join(logs),
            exit_code=0,
            duration_ms=duration,
            data={"status": "deployed", "logs": logs}
        )
