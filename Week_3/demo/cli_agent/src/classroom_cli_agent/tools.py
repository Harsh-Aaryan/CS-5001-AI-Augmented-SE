from __future__ import annotations

import subprocess
import json
from pathlib import Path
from typing import Any, Dict, Tuple

from .utils import clamp


class Tools:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path.resolve()

    def _safe(self, rel_path: str) -> Path:
        p = (self.repo_path / rel_path).resolve()
        if not str(p).startswith(str(self.repo_path)):
            raise ValueError("Unsafe path traversal blocked.")
        return p

    def read(self, rel_path: str, max_chars: int = 14000) -> str:
        p = self._safe(rel_path)
        if not p.exists():
            return ""
        return clamp(p.read_text(encoding="utf-8", errors="replace"), max_chars)

    def write(self, rel_path: str, content: str) -> None:
        p = self._safe(rel_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def write_json(self, rel_path: str, payload: Dict[str, Any]) -> None:
        p = self._safe(rel_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def run(self, cmd: str) -> Tuple[bool, str]:
        proc = subprocess.run(cmd, cwd=self.repo_path, shell=True, capture_output=True, text=True)
        out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        return proc.returncode == 0, clamp(out.strip() if out.strip() else "[NO OUTPUT]", 20000)

    def git_commit(self, message: str) -> Tuple[bool, str]:
        ok1, out1 = self.run("git add -A")
        if not ok1:
            return False, out1
        safe_msg = message.replace('"', "'")
        return self.run(f'git commit -m "{safe_msg}"')

    def git_push(self) -> Tuple[bool, str]:
        return self.run("git push")
