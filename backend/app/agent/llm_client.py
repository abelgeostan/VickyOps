import logging
import httpx
from typing import Any, Dict, List, Optional
from app.config import settings

logger = logging.getLogger("vickyops.ai")

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL

    async def check_health(self) -> Dict[str, Any]:
        """Check if external Ollama server is reachable and list models."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    return {
                        "online": True,
                        "url": self.base_url,
                        "current_model": self.model,
                        "available_models": models
                    }
        except Exception as e:
            logger.debug(f"Ollama server check failed: {e}")
        
        return {
            "online": False,
            "url": self.base_url,
            "current_model": self.model,
            "available_models": [],
            "error": "Ollama server unreachable or offline"
        }

    async def generate_response(self, system_prompt: str, prompt: str, timeout: float = 30.0) -> Optional[str]:
        """Call Ollama /api/generate or /api/chat."""
        try:
            payload = {
                "model": self.model,
                "prompt": f"{system_prompt}\n\nUser: {prompt}\nAssistant:",
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            }
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
        return None

ollama_client = OllamaClient()
