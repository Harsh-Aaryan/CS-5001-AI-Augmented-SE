from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import requests

from . import config


class ToolError(RuntimeError):
    pass


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    if config.DEPLOY_KEY_PATH:
        env["GIT_SSH_COMMAND"] = f'ssh -i "{config.DEPLOY_KEY_PATH}" -o IdentitiesOnly=yes'
    return env


def run_git(args: list[str], repo_path: Path | None = None) -> str:
    target = repo_path or config.REPO_PATH
    proc = subprocess.run(
        ["git", *args],
        cwd=str(target),
        env=_git_env(),
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise ToolError(proc.stderr.strip() or proc.stdout.strip() or f"git command failed: {' '.join(args)}")
    return proc.stdout


def get_current_branch() -> str:
    return run_git(["rev-parse", "--abbrev-ref", "HEAD"]).strip()


def get_default_branch() -> str:
    refs = run_git(["symbolic-ref", "refs/remotes/origin/HEAD"]).strip()
    return refs.rsplit("/", 1)[-1]


def collect_diff(base_branch: str | None = None, commit_range: str | None = None) -> dict[str, Any]:
    if commit_range:
        ref = commit_range
    elif base_branch:
        try:
            run_git(["fetch", "origin", base_branch])
        except ToolError:
            pass
        ref = f"{base_branch}...HEAD"
    else:
        ref = "HEAD"

    diff = run_git(["diff", "--unified=3", ref])
    files_raw = run_git(["diff", "--name-only", ref])
    numstat_raw = run_git(["diff", "--numstat", ref])

    files = [line.strip() for line in files_raw.splitlines() if line.strip()]
    numstat = []
    for line in numstat_raw.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        try:
            added_count = int(added)
        except ValueError:
            added_count = 0
        try:
            deleted_count = int(deleted)
        except ValueError:
            deleted_count = 0
        numstat.append({"path": path, "added": added_count, "deleted": deleted_count})

    return {
        "reference": ref,
        "diff": diff,
        "files": files,
        "numstat": numstat,
        "total_added": sum(item["added"] for item in numstat),
        "total_deleted": sum(item["deleted"] for item in numstat),
    }


def read_changed_file_snippets(files: list[str], max_files: int = 6, max_chars: int = 1200) -> list[dict[str, str]]:
    snippets: list[dict[str, str]] = []
    for path in files[:max_files]:
        full = config.REPO_PATH / path
        if not full.exists() or not full.is_file():
            continue
        try:
            content = full.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        snippets.append({
            "path": path,
            "excerpt": content[:max_chars],
        })
    return snippets


def extract_diff_evidence(diff_text: str, max_items: int = 8) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    current_file = "unknown"
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line.replace("+++ b/", "", 1)
            continue
        if line.startswith("+") and not line.startswith("+++"):
            snippet = line[1:].strip()
            if snippet:
                evidence.append({"source": current_file, "type": "added", "snippet": snippet[:200]})
        elif line.startswith("-") and not line.startswith("---"):
            snippet = line[1:].strip()
            if snippet:
                evidence.append({"source": current_file, "type": "removed", "snippet": snippet[:200]})
        if len(evidence) >= max_items:
            break
    return evidence


def contains_test_file(files: list[str]) -> bool:
    return any(re.search(r"(test|spec)", file_path, flags=re.IGNORECASE) for file_path in files)


class GitHubClient:
    def __init__(self) -> None:
        self.owner = config.GITHUB_OWNER
        self.repo = config.GITHUB_REPO
        self.token = config.GITHUB_TOKEN

    def _check_ready(self) -> None:
        if not self.owner or not self.repo:
            raise ToolError("GITHUB_OWNER and GITHUB_REPO are required for GitHub operations.")
        if not self.token:
            raise ToolError("GITHUB_TOKEN is required for GitHub create/fetch operations.")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _url(self, suffix: str) -> str:
        return f"{config.GITHUB_API_BASE}/repos/{self.owner}/{self.repo}{suffix}"

    def get_issue(self, number: int) -> dict[str, Any]:
        self._check_ready()
        resp = requests.get(self._url(f"/issues/{number}"), headers=self._headers(), timeout=30)
        if resp.status_code >= 400:
            raise ToolError(f"GitHub get_issue failed: {resp.status_code} {resp.text}")
        return resp.json()

    def get_pull_request(self, number: int) -> dict[str, Any]:
        self._check_ready()
        resp = requests.get(self._url(f"/pulls/{number}"), headers=self._headers(), timeout=30)
        if resp.status_code >= 400:
            raise ToolError(f"GitHub get_pull_request failed: {resp.status_code} {resp.text}")
        return resp.json()

    def create_issue(self, title: str, body: str) -> dict[str, Any]:
        self._check_ready()
        resp = requests.post(
            self._url("/issues"),
            headers=self._headers(),
            json={"title": title, "body": body},
            timeout=30,
        )
        if resp.status_code >= 400:
            raise ToolError(f"GitHub create_issue failed: {resp.status_code} {resp.text}")
        return resp.json()

    def create_pull_request(self, title: str, body: str, head: str, base: str, draft: bool = True) -> dict[str, Any]:
        self._check_ready()
        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
            "draft": draft,
        }
        resp = requests.post(self._url("/pulls"), headers=self._headers(), json=payload, timeout=30)
        if resp.status_code >= 400:
            raise ToolError(f"GitHub create_pull_request failed: {resp.status_code} {resp.text}")
        return resp.json()
