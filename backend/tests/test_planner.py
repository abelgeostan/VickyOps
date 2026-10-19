import pytest
from app.agent.planner import planner

@pytest.mark.asyncio
async def test_planner_update_vickyai():
    services = [{
        "id": "vickyai",
        "name": "VickyAI",
        "path": "/home/stan/VickyAI",
        "branch": "main",
        "compose_file": "docker-compose.yml",
        "health_url": "http://localhost:8000/api/health",
        "deployment_type": "git_compose"
    }]
    plan = await planner.create_plan("Update VickyAI", services)
    assert plan.service_id == "vickyai"
    assert plan.requires_approval is True
    assert len(plan.steps) == 5
    step_tools = [s.tool_name for s in plan.steps]
    assert "git.status" in step_tools
    assert "git.check_updates" in step_tools
    assert "git.pull" in step_tools
    assert "service.deploy" in step_tools
    assert "service.health_check" in step_tools

@pytest.mark.asyncio
async def test_planner_ram_query():
    plan = await planner.create_plan("Show me what's using the most RAM", [])
    assert plan.requires_approval is False
    assert any(s.tool_name == "server.get_resources" for s in plan.steps)

@pytest.mark.asyncio
async def test_planner_restart_requires_approval():
    services = [{
        "id": "standrive",
        "name": "StanDrive",
        "path": "/home/stan/stancloud",
        "compose_file": "docker-compose.yml"
    }]
    plan = await planner.create_plan("Restart StanDrive", services)
    assert plan.requires_approval is True
    assert "restart" in plan.title.lower()
