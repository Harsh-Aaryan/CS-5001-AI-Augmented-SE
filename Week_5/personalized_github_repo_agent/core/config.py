from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]

REPO_PATH = Path(os.getenv("AGENT_REPO_PATH", str(DEFAULT_REPO_ROOT))).resolve()
DEPLOY_KEY_PATH = os.getenv("AGENT_DEPLOY_KEY_PATH", "").strip()

GITHUB_OWNER = os.getenv("GITHUB_OWNER", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPO", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_API_BASE = os.getenv("GITHUB_API_BASE", "https://api.github.com").rstrip("/")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
USE_OLLAMA = os.getenv("USE_OLLAMA", "1") == "1"

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "5055"))
DEBUG = os.getenv("APP_DEBUG", "1") == "1"
