from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .llm import OllamaLLM
from .prompts import program_prompt, tests_prompt, scaffold_prompt
from .tools import Tools
from .types import AgentConfig, RunResult
from .utils import clamp, parse_coverage_total, strip_code_fences


class Agent:
    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg
        self.repo = Path(cfg.repo).resolve()
        self.tools = Tools(self.repo)
        self.llm = OllamaLLM(model=cfg.model, host=cfg.host, temperature=cfg.temperature)

    def _log(self, message: Any) -> None:
        if self.cfg.verbose:
            print(message)

    def create_program(self, desc: str, module_path: str) -> RunResult:
        existing = self.tools.read(module_path)
        prompt = program_prompt(desc, existing)
        self._log(prompt)
        raw = self.llm.generate(prompt)
        self._log(raw)
        content = strip_code_fences(raw)
        self._log(content)
        if not content:
            return RunResult(False, "Model returned empty module after sanitization.")
        self.tools.write(module_path, content + "\n")
        return RunResult(True, f"Wrote module: {module_path}")

    def scaffold_project(self, desc: str, out_dir: str = ".", overwrite: bool = False) -> RunResult:
        """Generate a multi-file project scaffold.

        The model must return JSON with a top-level key "files":
        [{"path": "relative/path", "content": "..."}, ...]
        """

        out_dir_norm = (out_dir or ".").strip().replace("\\", "/")
        if out_dir_norm in ("", "./"):
            out_dir_norm = "."

        tree = self.tools.list_tree(out_dir_norm, max_files=200, max_chars=12000)
        prompt = scaffold_prompt(desc, out_dir_norm, tree)
        self._log(prompt)
        raw = self.llm.generate(prompt)
        self._log(raw)

        # Scaffold must be JSON. If the model violates this, fail fast.
        try:
            payload = json.loads(raw)
        except Exception:
            return RunResult(
                False,
                "Scaffold generation failed: model did not return valid JSON.",
            )

        files = payload.get("files") if isinstance(payload, dict) else None
        if not isinstance(files, list) or not files:
            return RunResult(
                False,
                "Scaffold generation failed: JSON must contain a non-empty 'files' list.",
            )

        written = []
        skipped = []
        rejected = []

        for item in files:
            if not isinstance(item, dict):
                rejected.append("[invalid item]")
                continue

            rel_path = str(item.get("path") or "").strip().replace("\\", "/")
            content = item.get("content")

            if not rel_path or not isinstance(content, str):
                rejected.append(rel_path or "[missing path]")
                continue

            # Normalize and block path traversal.
            rel_path = rel_path.lstrip("/")
            if ".." in rel_path.split("/"):
                rejected.append(rel_path)
                continue

            final_rel = self._scaffold_target_path(out_dir_norm, rel_path)

            if (not overwrite) and self.tools.exists(final_rel):
                skipped.append(final_rel)
                continue

            self.tools.write(final_rel, content.rstrip() + "\n")
            written.append(final_rel)

        summary = {
            "out_dir": out_dir_norm,
            "written": written,
            "skipped": skipped,
            "rejected": rejected,
        }
        self.tools.write_json(str(Path(out_dir_norm) / "reports" / "scaffold_summary.json"), summary)

        details = (
            f"Scaffold complete. Written: {len(written)}, skipped: {len(skipped)}, rejected: {len(rejected)}. "
            f"Summary: {Path(out_dir_norm) / 'reports' / 'scaffold_summary.json'}"
        )
        ok = len(written) > 0 and len(rejected) == 0
        if not ok and len(written) > 0:
            # Partial success.
            return RunResult(True, details)
        return RunResult(ok, details)

    @staticmethod
    def _scaffold_target_path(out_dir_norm: str, rel_path: str) -> str:
        out_dir_norm = out_dir_norm.strip().replace("\\", "/")
        if out_dir_norm in ("", ".", "./"):
            return rel_path
        out_dir_norm = out_dir_norm.rstrip("/")
        if rel_path.startswith(out_dir_norm + "/"):
            return rel_path
        return f"{out_dir_norm}/{rel_path}"

    def create_tests(self, desc: str, module_path: str, tests_path: str) -> RunResult:
        module_code = self.tools.read(module_path)
        existing_tests = self.tools.read(tests_path)
        prompt = tests_prompt(desc, module_path, module_code, existing_tests)
        self._log(prompt)
        raw = self.llm.generate(prompt)
        self._log(raw)
        content = strip_code_fences(raw)
        self._log(content)
        if not content:
            return RunResult(False, "Model returned empty tests after sanitization.")
        self.tools.write(tests_path, content + "\n")
        return RunResult(True, f"Wrote tests: {tests_path}")

    def tests_exist(self, tests_path: str) -> bool:
        return bool(self.tools.read(tests_path, max_chars=1))

    def _run_tests_with_coverage(self) -> Dict[str, Any]:
        cov_json_path = self.repo / ".coverage.json"
        cmd = f"coverage run -m pytest -q && coverage json -o {cov_json_path.name}"
        self._log(cmd)
        ok, out = self.tools.run(cmd)
        self._log(ok)
        self._log(out)
        total: float = 0.0
        data: Dict[str, Any] = {}
        if cov_json_path.exists():
            total, data = parse_coverage_total(cov_json_path)

        return {
            "ok": ok,
            "command": cmd,
            "pytest_output": out,
            "total_coverage_percent": total,
            "coverage_json_path": str(cov_json_path),
            "coverage_data": data,
        }

    def generate_test_report(
        self,
        module_path: Optional[str],
        report_out_path: str,
        report_md_path: Optional[str],
        fail_on_tests: bool,
        fail_on_coverage: Optional[float],
    ) -> RunResult:
        result = self._run_tests_with_coverage()
        cov_data = result.get("coverage_data", {}) or {}
        self._log(result)
        module_summary: Dict[str, Any] = {}
        if module_path:
            module_summary = self._module_coverage_summary(cov_data, module_path)

        report: Dict[str, Any] = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "agent_config": asdict(self.cfg),
            "module_path": module_path,
            "command": result.get("command"),
            "tests_passed": bool(result.get("ok")),
            "total_coverage_percent": float(result.get("total_coverage_percent") or 0.0),
            "module_coverage": module_summary,
            "pytest_output": clamp(str(result.get("pytest_output") or ""), 20000),
        }

        self.tools.write_json(report_out_path, report)

        if report_md_path:
            self.tools.write(report_md_path, self._render_markdown_report(report) + "\n")

        tests_passed = bool(report["tests_passed"])
        total_cov = float(report["total_coverage_percent"])

        should_fail = False
        fail_reasons = []

        if fail_on_tests and not tests_passed:
            should_fail = True
            fail_reasons.append("pytest failed")

        if fail_on_coverage is not None and total_cov < float(fail_on_coverage):
            should_fail = True
            fail_reasons.append(
                f"coverage {total_cov:.1f}% below target {float(fail_on_coverage):.1f}%"
            )

        details = f"Wrote report: {report_out_path}"
        if report_md_path:
            details += f" (and {report_md_path})"

        if should_fail:
            return RunResult(False, details + "; " + ", ".join(fail_reasons), coverage=total_cov)

        return RunResult(True, details, coverage=total_cov)

    def _module_coverage_summary(self, cov_json: Dict[str, Any], module_rel: str) -> Dict[str, Any]:
        files = cov_json.get("files", {}) or {}
        target = module_rel.replace("\\", "/")
        matches = [k for k in files.keys() if k.replace("\\", "/").endswith(target)]
        if not matches:
            return {"found": False, "note": "No per-file coverage details found for target module."}

        entry = files[matches[0]] or {}
        summary = entry.get("summary", {}) or {}
        missing = entry.get("missing_lines", []) or []
        return {
            "found": True,
            "file": matches[0],
            "percent_covered": summary.get("percent_covered"),
            "num_statements": summary.get("num_statements"),
            "missing_lines": missing,
        }

    def _render_markdown_report(self, report: Dict[str, Any]) -> str:
        tests_passed = "PASS" if report.get("tests_passed") else "FAIL"
        total_cov = float(report.get("total_coverage_percent") or 0.0)

        module_cov = report.get("module_coverage") or {}
        module_line = ""
        if module_cov.get("found"):
            pct = module_cov.get("percent_covered")
            missing = module_cov.get("missing_lines") or []
            module_line = (
                f"\n## Module coverage\n\n"
                f"- File: `{module_cov.get('file')}`\n"
                f"- Percent covered: {pct}\n"
                f"- Missing lines: {', '.join(str(x) for x in missing) if missing else '[none]'}\n"
            )

        out = report.get("pytest_output") or ""
        return (
            f"# Test Report\n\n"
            f"- Timestamp (UTC): {report.get('timestamp_utc')}\n"
            f"- Result: {tests_passed}\n"
            f"- Total coverage: {total_cov:.1f}%\n"
            f"- Command: `{report.get('command')}`\n"
            f"{module_line}\n"
            f"## Pytest output\n\n"
            f"```\n{out}\n```\n"
        )

    def commit_and_push(self, message: str, push: bool) -> RunResult:
        ok, out = self.tools.git_commit(message)
        if not ok:
            return RunResult(False, out)
        if push:
            ok2, out2 = self.tools.git_push()
            if not ok2:
                return RunResult(False, "Commit succeeded, but push failed:\n" + out2)
            return RunResult(True, "Commit and push succeeded.")
        return RunResult(True, "Commit succeeded.")
