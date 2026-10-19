import time
import re
from typing import Any, Dict, Optional
from app.tools.base import BaseTool, ToolResult
from app.tools.ssh_client import ssh_manager
from app.tools.docker_tools import validate_identifier

class GitStatusTool(BaseTool):
    name = "git.status"
    description = "Check git status, current branch, and HEAD commit for a configured service."
    category = "git"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {
        "service_path": {"type": "string", "required": True, "description": "Filesystem path to git repo"}
    }

    async def execute(self, service_path: str, **kwargs) -> ToolResult:
        start_time = time.time()
        # Security: sanitize service_path
        if ";" in service_path or "&" in service_path or "|" in service_path or "`" in service_path:
            return ToolResult(tool_name=self.name, success=False, output="", error="Invalid characters in path", exit_code=-1)

        cmd = f"""
        git config --global --add safe.directory "{service_path}" 2>/dev/null || true
        cd "{service_path}" || exit 1
        echo "===BRANCH==="
        git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown"
        echo "===COMMIT==="
        git rev-parse HEAD 2>/dev/null || echo "unknown"
        echo "===COMMIT_SHORT==="
        git rev-parse --short HEAD 2>/dev/null || echo "unknown"
        echo "===STATUS==="
        git status --porcelain 2>/dev/null || true
        """
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        if code != 0:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=err or f"Not a git repository at {service_path}",
                exit_code=code,
                duration_ms=duration
            )

        try:
            branch = out.split("===BRANCH===")[1].split("===COMMIT===")[0].strip()
            commit = out.split("===COMMIT===")[1].split("===COMMIT_SHORT===")[0].strip()
            commit_short = out.split("===COMMIT_SHORT===")[1].split("===STATUS===")[0].strip()
            status_clean = len(out.split("===STATUS===")[1].strip()) == 0

            data = {
                "branch": branch,
                "commit": commit,
                "commit_short": commit_short,
                "is_clean": status_clean,
                "path": service_path
            }
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Git Repo at {service_path}: Branch '{branch}', Commit: {commit_short} ({'clean' if status_clean else 'modified'}).",
                exit_code=0,
                duration_ms=duration,
                data=data
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Error parsing git status: {e}",
                exit_code=-1,
                duration_ms=duration
            )

class GitCheckUpdatesTool(BaseTool):
    name = "git.check_updates"
    description = "Check if remote git repository has new commits without modifying local working copy."
    category = "git"
    is_dangerous = False
    requires_approval = False
    parameters_schema = {
        "service_path": {"type": "string", "required": True},
        "branch": {"type": "string", "default": "main"}
    }

    async def execute(self, service_path: str, branch: str = "main", **kwargs) -> ToolResult:
        start_time = time.time()
        if ";" in service_path or "&" in service_path or "|" in service_path:
            return ToolResult(tool_name=self.name, success=False, output="", error="Invalid characters in path", exit_code=-1)

        validate_identifier(branch, "branch")

        cmd = f"""
        cd "{service_path}" || exit 1
        LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "none")
        REMOTE=$(git ls-remote origin "refs/heads/{branch}" | cut -f1)
        echo "$LOCAL|$REMOTE"
        """
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        if code != 0:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=err or f"Failed to check remote updates for {service_path}",
                exit_code=code,
                duration_ms=duration
            )

        line = out.strip().splitlines()[-1] if out.strip() else ""
        if "|" in line:
            local_commit, remote_commit = line.split("|", 1)
            local_commit = local_commit.strip()
            remote_commit = remote_commit.strip()
            
            has_updates = bool(remote_commit and remote_commit != local_commit)
            data = {
                "has_updates": has_updates,
                "local_commit": local_commit,
                "remote_commit": remote_commit,
                "branch": branch
            }
            if has_updates:
                msg = f"Updates found for branch '{branch}'. Local: {local_commit[:7]}, Remote: {remote_commit[:7]}."
            else:
                msg = f"Service is up to date on branch '{branch}' (commit: {local_commit[:7]})."

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=msg,
                exit_code=0,
                duration_ms=duration,
                data=data
            )

        return ToolResult(
            tool_name=self.name,
            success=False,
            output="",
            error="Could not parse remote git hashes",
            exit_code=-1,
            duration_ms=duration
        )

class GitPullTool(BaseTool):
    name = "git.pull"
    description = "Pull latest changes from remote git repository."
    category = "git"
    is_dangerous = True
    requires_approval = True
    parameters_schema = {
        "service_path": {"type": "string", "required": True},
        "branch": {"type": "string", "default": "main"}
    }

    async def execute(self, service_path: str, branch: str = "main", **kwargs) -> ToolResult:
        start_time = time.time()
        if ";" in service_path or "&" in service_path or "|" in service_path:
            return ToolResult(tool_name=self.name, success=False, output="", error="Invalid characters in path", exit_code=-1)
        validate_identifier(branch, "branch")

        cmd = f'cd "{service_path}" && git pull origin "{branch}" 2>&1'
        code, out, err = await ssh_manager.execute_command(cmd)
        duration = (time.time() - start_time) * 1000

        success = (code == 0)
        return ToolResult(
            tool_name=self.name,
            success=success,
            output=out.strip() if success else "",
            error=err or out.strip() if not success else None,
            exit_code=code,
            duration_ms=duration
        )
