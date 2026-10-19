from fastapi import APIRouter
from app.tools.registry import tool_registry

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/server")
async def get_server_metrics():
    res_tool = tool_registry.get_tool("server.get_resources")
    stat_tool = tool_registry.get_tool("server.get_status")
    
    res_data = {}
    stat_data = {}
    if res_tool:
        r = await res_tool.execute()
        if r.success:
            res_data = r.data
    if stat_tool:
        s = await stat_tool.execute()
        if s.success:
            stat_data = s.data

    return {
        "hostname": stat_data.get("hostname", "vicky"),
        "uptime": stat_data.get("uptime", "Unknown"),
        "kernel": stat_data.get("kernel", "Linux"),
        "docker_version": stat_data.get("docker_version", "Online"),
        "cpu_percent": res_data.get("cpu_percent", 0.0),
        "cpu_load": res_data.get("cpu_load", {"load1": 0.0, "load5": 0.0, "load15": 0.0}),
        "ram": res_data.get("ram", {"percent": 0.0, "used_human": "0 GB", "total_human": "0 GB"}),
        "disk": res_data.get("disk", {"percent": 0.0, "used_human": "0 GB", "total_human": "0 GB"}),
        "network": res_data.get("network", {"rx_human": "0 MB", "tx_human": "0 MB"})
    }

@router.get("/cloudflare")
async def get_cloudflare_status():
    cf_tool = tool_registry.get_tool("cloudflare.get_status")
    if cf_tool:
        res = await cf_tool.execute()
        if res.success:
            return res.data
    return {
        "tunnel_count": 0,
        "active_count": 0,
        "overall_status": "offline",
        "tunnels": []
    }
