from __future__ import annotations

import requests

from . import config


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.enabled = config.USE_OLLAMA

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        if not self.enabled:
            return ""
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
            resp.raise_for_status()
            return resp.json().get("message", {}).get("content", "").strip()
        except Exception:
            return ""
