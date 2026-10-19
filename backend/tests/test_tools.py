import pytest
from app.tools.registry import tool_registry
from app.tools.docker_tools import validate_identifier

def test_registry_contains_required_tools():
    tools = tool_registry.list_tools()
    tool_names = [t["name"] for t in tools]
    
    expected = [
        "server.get_status",
        "server.get_resources",
        "docker.list_containers",
        "docker.container_status",
        "docker.logs",
        "docker.restart",
        "docker.start",
        "docker.stop",
        "git.status",
        "git.check_updates",
        "git.pull",
        "service.get_status",
        "service.deploy",
        "service.restart",
        "service.health_check",
        "backup.create",
        "backup.list",
        "backup.restore",
        "cloudflare.get_status"
    ]
    for exp in expected:
        assert exp in tool_names, f"Expected tool {exp} not registered"

def test_dangerous_tool_classification():
    # Verify destructive tools are strictly marked dangerous and require approval
    dangerous_tools = [
        "docker.restart",
        "docker.stop",
        "git.pull",
        "service.deploy",
        "service.restart",
        "backup.restore"
    ]
    for d in dangerous_tools:
        tool = tool_registry.get_tool(d)
        assert tool is not None, f"Tool {d} not found"
        assert tool.is_dangerous is True, f"Tool {d} should be marked dangerous"
        assert tool.requires_approval is True, f"Tool {d} should require approval"

def test_safe_tool_classification():
    safe_tools = [
        "server.get_status",
        "server.get_resources",
        "docker.list_containers",
        "docker.logs",
        "git.status",
        "git.check_updates",
        "service.health_check",
        "cloudflare.get_status"
    ]
    for s in safe_tools:
        tool = tool_registry.get_tool(s)
        assert tool is not None, f"Tool {s} not found"
        assert tool.is_dangerous is False, f"Tool {s} should not be marked dangerous"
        assert tool.requires_approval is False, f"Tool {s} should not require approval"

def test_identifier_sanitization():
    # Valid
    validate_identifier("vickyai_backend")
    validate_identifier("docker-compose.yml")
    validate_identifier("standrive-1.0")

    # Invalid - should raise ValueError to prevent command injection
    with pytest.raises(ValueError):
        validate_identifier("service; rm -rf /")
    with pytest.raises(ValueError):
        validate_identifier("test | cat /etc/passwd")
    with pytest.raises(ValueError):
        validate_identifier("$(whoami)")
