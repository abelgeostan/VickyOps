import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "VickyOps"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    
    # Security & Auth
    SECRET_KEY: str = "vickyops_super_secret_jwt_key_production_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./vickyops.db"
    
    # External Ollama AI
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:latest"
    
    # Remote Server SSH Configuration
    SSH_HOST: str = "vicky"
    SSH_PORT: int = 22
    SSH_USER: str = "vickyops"
    SSH_PASSWORD: Optional[str] = "vickythegoat"
    SSH_KEY_PATH: Optional[str] = os.path.expanduser("~/.ssh/id_ed25519")
    SSH_TIMEOUT: int = 15
    
    # Security controls
    ENABLE_REAL_SSH: bool = True
    AUTO_APPROVE_SAFE: bool = True
    REQUIRE_APPROVAL_DESTRUCTIVE: bool = True
    
    # Services configuration file
    SERVICES_CONFIG_PATH: str = "services.yaml"
    BACKUP_DIR: str = "/var/backups/vickyops"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
