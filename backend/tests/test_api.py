import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app, seed_data
from app.database import init_db

@pytest.fixture(scope="module", autouse=True)
def anyio_backend():
    return "asyncio"

@pytest.mark.asyncio
async def test_api_endpoints():
    await init_db()
    await seed_data()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Root and health
        r = await client.get("/")
        assert r.status_code == 200
        assert r.json()["app"] == "VickyOps"

        r = await client.get("/health")
        assert r.status_code == 200

        # 2. Services list
        r = await client.get("/api/services")
        assert r.status_code == 200
        services = r.json()
        assert len(services) > 0
        vickyai = next((s for s in services if s["id"] == "vickyai"), None)
        assert vickyai is not None

        # 3. VickyAI compatibility (Phase 2 & 3 verification)
        r = await client.get("/api/services/vickyai/compat")
        assert r.status_code == 200
        compat = r.json()
        assert compat["compatible"] is True

        # StanDrive compatibility (shows required changes)
        r = await client.get("/api/services/standrive/compat")
        assert r.status_code == 200
        sd_compat = r.json()
        assert len(sd_compat["required_changes"]) > 0

        # 4. Chat endpoint
        r = await client.post("/api/chat", json={"message": "Show me what's using the most RAM"})
        assert r.status_code == 200
        chat_data = r.json()
        assert "operation_id" in chat_data
        assert chat_data["requires_approval"] is False

        # Chat endpoint with dangerous command
        r = await client.post("/api/chat", json={"message": "Update VickyAI"})
        assert r.status_code == 200
        deploy_chat = r.json()
        assert deploy_chat["requires_approval"] is True
        assert "operation_id" in deploy_chat

        # 5. Operations endpoint
        op_id = deploy_chat["operation_id"]
        r = await client.get(f"/api/operations/{op_id}")
        assert r.status_code == 200
        op = r.json()
        assert op["id"] == op_id
        assert op["approval_status"] == "awaiting"

        # Reject operation
        r = await client.post(f"/api/operations/{op_id}/decision", json={"decision": "reject"})
        assert r.status_code == 200
        assert r.json()["status"] == "cancelled"
