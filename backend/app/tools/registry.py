import logging
from typing import Dict, Any, List, Optional
from app.tools.base import BaseTool, ToolResult
from app.tools.server_tools import ServerGetStatusTool, ServerGetResourcesTool
from app.tools.docker_tools import (
    DockerListContainersTool,
    DockerContainerStatusTool,
    DockerLogsTool,
    DockerRestartTool,
    DockerStopTool,
    DockerStartTool,
)
from app.tools.git_tools import GitStatusTool, GitCheckUpdatesTool, GitPullTool
from app.tools.service_tools import (
    ServiceGetStatusTool,
    ServiceHealthCheckTool,
    ServiceRestartTool,
    ServiceDeployTool,
)
from app.tools.backup_tools import BackupCreateTool, BackupListTool, BackupRestoreTool
from app.tools.cloudflare_tools import CloudflareGetStatusTool

logger = logging.getLogger("vickyops.tools")

class ToolRegistry:
    _instance: Optional["ToolRegistry"] = None

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = ToolRegistry()
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name} (dangerous={tool.is_dangerous})")

    def _register_default_tools(self) -> None:
        # Server
        self.register(ServerGetStatusTool())
        self.register(ServerGetResourcesTool())
        # Docker
        self.register(DockerListContainersTool())
        self.register(DockerContainerStatusTool())
        self.register(DockerLogsTool())
        self.register(DockerRestartTool())
        self.register(DockerStopTool())
        self.register(DockerStartTool())
        # Git
        self.register(GitStatusTool())
        self.register(GitCheckUpdatesTool())
        self.register(GitPullTool())
        # Service
        self.register(ServiceGetStatusTool())
        self.register(ServiceHealthCheckTool())
        self.register(ServiceRestartTool())
        self.register(ServiceDeployTool())
        # Backup
        self.register(BackupCreateTool())
        self.register(BackupListTool())
        self.register(BackupRestoreTool())
        # Cloudflare
        self.register(CloudflareGetStatusTool())

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "is_dangerous": tool.is_dangerous,
                "requires_approval": tool.requires_approval,
                "parameters_schema": tool.parameters_schema
            }
            for tool in self._tools.values()
        ]

    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=f"Tool '{tool_name}' is not in the allowlist of controlled backend tools.",
                exit_code=-1
            )
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=str(e),
                exit_code=-1
            )

tool_registry = ToolRegistry.get_instance()
