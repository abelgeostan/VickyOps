import os
import yaml
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.models.service import ServiceModel
from app.models.user import User
from app.api.auth import router as auth_router, get_password_hash
from app.api.services import router as services_router
from app.api.operations import router as operations_router
from app.api.chat import router as chat_router
from app.api.metrics import router as metrics_router
from app.api.audit import router as audit_router
from app.api.backups import router as backups_router
from app.api.ws import router as ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("vickyops")

async def seed_data():
    async with AsyncSessionLocal() as session:
        # 1. Admin user
        user_stmt = select(User).where(User.username == settings.ADMIN_USERNAME)
        user_res = await session.execute(user_stmt)
        if not user_res.scalar_one_or_none():
            admin = User(
                username=settings.ADMIN_USERNAME,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                role="admin"
            )
            session.add(admin)
            logger.info(f"Default admin user created: {settings.ADMIN_USERNAME}")

        # 2. Seed services from yaml
        seed_path = os.path.join(os.path.dirname(__file__), "services_seed.yaml")
        if os.path.exists(seed_path):
            with open(seed_path, "r", encoding="utf-8") as f:
                seed_data = yaml.safe_load(f) or {}
                services = seed_data.get("services", [])
                for s in services:
                    s_id = s.get("id")
                    s_stmt = select(ServiceModel).where(ServiceModel.id == s_id)
                    s_res = await session.execute(s_stmt)
                    if not s_res.scalar_one_or_none():
                        new_s = ServiceModel(
                            id=s_id,
                            name=s.get("name"),
                            description=s.get("description"),
                            repository=s.get("repository"),
                            branch=s.get("branch", "main"),
                            path=s.get("path"),
                            compose_file=s.get("compose_file", "docker-compose.yml"),
                            health_url=s.get("health_url"),
                            deployment_type=s.get("deployment_type", "git_compose"),
                            requires_approval=s.get("requires_approval", True),
                            status="running" if s_id == "vickyai" else "unknown"
                        )
                        session.add(new_s)
                        logger.info(f"Seeded service: {s.get('name')}")
        await session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    await init_db()
    await seed_data()
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(services_router, prefix="/api")
app.include_router(operations_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(backups_router, prefix="/api")
app.include_router(ws_router)

@app.get("/")
async def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "mode": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}
