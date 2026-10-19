import json
import re
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.tools.registry import tool_registry
from app.agent.llm_client import ollama_client

logger = logging.getLogger("vickyops.planner")

class PlanStep(BaseModel):
    step_index: int
    name: str
    tool_name: str
    parameters: Dict[str, Any]
    description: str
    is_dangerous: bool = False
    requires_approval: bool = False
    status: str = "pending" # pending, running, completed, failed, skipped, awaiting_approval

class ExecutionPlan(BaseModel):
    title: str
    user_request: str
    service_id: Optional[str] = None
    steps: List[PlanStep]
    requires_approval: bool = False
    approval_prompt: Optional[str] = None
    explanation: Optional[str] = None

class DevOpsPlanner:
    def __init__(self):
        pass

    def _match_service(self, text: str, services: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        text_lower = text.lower()
        for s in services:
            s_name = s.get("name", "").lower()
            s_id = s.get("id", "").lower()
            if s_id in text_lower or s_name in text_lower:
                return s
        return None

    async def create_plan(self, user_request: str, services: List[Dict[str, Any]]) -> ExecutionPlan:
        """
        Analyzes the user's intent and creates a step-by-step execution plan using
        Ollama (if available) or rule-based DevOps intent matching.
        """
        req_lower = user_request.lower().strip()
        matched_service = self._match_service(req_lower, services)
        s_id = matched_service.get("id") if matched_service else None
        s_name = matched_service.get("name") if matched_service else None
        s_path = matched_service.get("path") if matched_service else None
        s_branch = matched_service.get("branch", "main") if matched_service else "main"
        s_compose = matched_service.get("compose_file", "docker-compose.yml") if matched_service else "docker-compose.yml"
        s_health = matched_service.get("health_url") if matched_service else None

        # 1. Update / Deploy service
        if any(w in req_lower for w in ["update", "deploy", "upgrade", "pull & build"]) and matched_service:
            # Check if this service is ready for standardized git deployment
            is_git_service = (s_id == "vickyai" or matched_service.get("deployment_type") == "git_compose")
            
            steps = [
                PlanStep(
                    step_index=0,
                    name="Checking repository",
                    tool_name="git.status" if is_git_service else "service.get_status",
                    parameters={"service_path": s_path} if is_git_service else {"service_path": s_path, "compose_file": s_compose},
                    description=f"Inspect working copy and branch for {s_name}",
                    is_dangerous=False,
                    requires_approval=False
                ),
                PlanStep(
                    step_index=1,
                    name="Checking GitHub for updates",
                    tool_name="git.check_updates" if is_git_service else "service.get_status",
                    parameters={"service_path": s_path, "branch": s_branch} if is_git_service else {"service_path": s_path},
                    description=f"Check remote repository changes on branch '{s_branch}'",
                    is_dangerous=False,
                    requires_approval=False
                ),
                PlanStep(
                    step_index=2,
                    name="Pulling latest branch",
                    tool_name="git.pull" if is_git_service else "service.get_status",
                    parameters={"service_path": s_path, "branch": s_branch} if is_git_service else {"service_path": s_path},
                    description=f"Fetch and merge latest changes from origin/{s_branch}",
                    is_dangerous=True,
                    requires_approval=True
                ),
                PlanStep(
                    step_index=3,
                    name="Building Docker images",
                    tool_name="docker.build" if is_git_service else "service.get_status",
                    parameters={"service_path": s_path, "compose_file": s_compose} if is_git_service else {"service_path": s_path},
                    description=f"Build and compile Docker images for {s_name}",
                    is_dangerous=True,
                    requires_approval=True
                ),
                PlanStep(
                    step_index=4,
                    name="Restarting services",
                    tool_name="docker.deploy" if is_git_service else "service.restart",
                    parameters={"service_path": s_path, "compose_file": s_compose},
                    description=f"Recreate and start updated containers for {s_name}",
                    is_dangerous=True,
                    requires_approval=True
                ),
                PlanStep(
                    step_index=5,
                    name="Running health checks",
                    tool_name="service.health_check",
                    parameters={"health_url": s_health, "service_path": s_path},
                    description=f"Verify operational health of {s_name}",
                    is_dangerous=False,
                    requires_approval=False
                )
            ]
            return ExecutionPlan(
                title=f"Deploy Update for {s_name}",
                user_request=user_request,
                service_id=s_id,
                steps=steps,
                requires_approval=True,
                approval_prompt=f"⚠️ This operation will deploy the latest update to {s_name} and briefly recreate its containers. Proceed with deployment?",
                explanation=f"Planned 6-step standardized deployment workflow for {s_name}."
            )

        # 2. Restart service / container
        if "restart" in req_lower:
            target_name = s_name or "container"
            step = PlanStep(
                step_index=0,
                name=f"Restarting {target_name}",
                tool_name="service.restart" if s_path else "docker.restart",
                parameters={"service_path": s_path, "compose_file": s_compose} if s_path else {"container_name": matched_service.get("id", "container") if matched_service else "container"},
                description=f"Restart services for {target_name}",
                is_dangerous=True,
                requires_approval=True
            )
            return ExecutionPlan(
                title=f"Restart {target_name}",
                user_request=user_request,
                service_id=s_id,
                steps=[step],
                requires_approval=True,
                approval_prompt=f"⚠️ Restarting {target_name} may cause temporary downtime. Do you want to proceed?",
                explanation=f"Restart action requested for {target_name}."
            )

        # 3. Stop service / container
        if "stop" in req_lower:
            target_name = s_name or "container"
            step = PlanStep(
                step_index=0,
                name=f"Stopping {target_name}",
                tool_name="docker.stop",
                parameters={"container_name": s_id or target_name},
                description=f"Stop {target_name}",
                is_dangerous=True,
                requires_approval=True
            )
            return ExecutionPlan(
                title=f"Stop {target_name}",
                user_request=user_request,
                service_id=s_id,
                steps=[step],
                requires_approval=True,
                approval_prompt=f"⚠️ Stopping {target_name} will take it offline. Proceed?",
                explanation=f"Stop action requested for {target_name}."
            )

        # 4. Backup service
        if "backup" in req_lower and matched_service:
            step = PlanStep(
                step_index=0,
                name=f"Creating backup for {s_name}",
                tool_name="backup.create",
                parameters={"service_path": s_path, "service_name": s_id},
                description=f"Archive files for {s_name}",
                is_dangerous=False,
                requires_approval=False
            )
            return ExecutionPlan(
                title=f"Backup {s_name}",
                user_request=user_request,
                service_id=s_id,
                steps=[step],
                requires_approval=False,
                explanation=f"Creating safe compressed backup archive for {s_name}."
            )

        # 5. Health check / status for service
        if matched_service and any(w in req_lower for w in ["health", "healthy", "status", "check"]):
            step = PlanStep(
                step_index=0,
                name=f"Checking health for {s_name}",
                tool_name="service.health_check",
                parameters={"health_url": s_health, "service_path": s_path},
                description=f"Run diagnostics on {s_name}",
                is_dangerous=False,
                requires_approval=False
            )
            return ExecutionPlan(
                title=f"Health Check: {s_name}",
                user_request=user_request,
                service_id=s_id,
                steps=[step],
                requires_approval=False,
                explanation=f"Verifying live health status of {s_name}."
            )

        # 6. Resource usage / RAM / CPU / Server status
        if any(w in req_lower for w in ["ram", "cpu", "memory", "resource", "load", "traffic", "disk", "usage"]):
            step = PlanStep(
                step_index=0,
                name="Inspecting system resources",
                tool_name="server.get_resources",
                parameters={},
                description="Query server CPU, RAM, Disk, and Network telemetry",
                is_dangerous=False,
                requires_approval=False
            )
            return ExecutionPlan(
                title="System Resource Inspection",
                user_request=user_request,
                service_id=None,
                steps=[step],
                requires_approval=False,
                explanation="Reading live hardware metrics from server."
            )

        # 7. Cloudflare tunnels status
        if any(w in req_lower for w in ["cloudflare", "tunnel"]):
            step = PlanStep(
                step_index=0,
                name="Inspecting Cloudflare tunnels",
                tool_name="cloudflare.get_status",
                parameters={},
                description="Check status of all configured tunnels",
                is_dangerous=False,
                requires_approval=False
            )
            return ExecutionPlan(
                title="Cloudflare Status Check",
                user_request=user_request,
                service_id=None,
                steps=[step],
                requires_approval=False,
                explanation="Inspecting Cloudflare Zero Trust tunnel containers."
            )

        # 8. Check updates for all services
        if "outdated" in req_lower or ("update" in req_lower and "all" in req_lower):
            steps = []
            for idx, s in enumerate(services):
                if s.get("id") == "vickyai" or s.get("deployment_type") == "git_compose":
                    steps.append(PlanStep(
                        step_index=idx,
                        name=f"Check updates for {s.get('name')}",
                        tool_name="git.check_updates",
                        parameters={"service_path": s.get("path"), "branch": s.get("branch", "main")},
                        description=f"Check git remote for {s.get('name')}",
                        is_dangerous=False,
                        requires_approval=False
                    ))
            return ExecutionPlan(
                title="Check Service Updates",
                user_request=user_request,
                steps=steps if steps else [PlanStep(step_index=0, name="Check containers", tool_name="docker.list_containers", parameters={}, description="List containers")],
                requires_approval=False,
                explanation="Scanning configured git-backed services for available remote updates."
            )

        # Default fallback: General server and container status inspection
        steps = [
            PlanStep(
                step_index=0,
                name="Checking server status",
                tool_name="server.get_status",
                parameters={},
                description="Check system uptime and core health",
                is_dangerous=False,
                requires_approval=False
            ),
            PlanStep(
                step_index=1,
                name="Listing active containers",
                tool_name="docker.list_containers",
                parameters={"all": True},
                description="List all running docker workloads",
                is_dangerous=False,
                requires_approval=False
            )
        ]
        return ExecutionPlan(
            title="Server Diagnostic",
            user_request=user_request,
            steps=steps,
            requires_approval=False,
            explanation="Running general diagnostic on server and Docker containers."
        )

planner = DevOpsPlanner()
