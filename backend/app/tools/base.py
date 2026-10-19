from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
import time

@dataclass
class ToolResult:
    tool_name: str
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    duration_ms: float = 0.0
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "data": self.data or {}
        }

class BaseTool:
    name: str = ""
    description: str = ""
    category: str = "general" # server, docker, git, service, backup, cloudflare
    is_dangerous: bool = False
    requires_approval: bool = False
    parameters_schema: Dict[str, Any] = {}

    async def execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError
