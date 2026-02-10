from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .llm import OllamaLLM
from .prompts import improve_tests_prompt, program_prompt, tests_prompt
from .tools import Tools
from .types import AgentConfig, RunResult
from .utils import clamp, parse_coverage_total, strip_code_fences


def _missing_lines_summary(cov_json: Dict, module_rel: str) -> str:
    files = cov_json.get("files", {})
    target = module_rel.replace("\\", "/")
    matches = [k for k in files.keys() if k.replace("\\", "/").endswith(target)]
    if not matches:
        return "[No per-file coverage details found for target module.]"
    entry = files[matches[0]]
    missing = entry.get("missing_lines", []) or []
    if not missing:
        return "[none]"
    return "Missing lines: " + ", ".join(str(x) for x in missing)


class Agent:
    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg
        self.repo = Path(cfg.repo).resolve()
        self.tools = Tools(self.repo)
        self.llm = OllamaLLM(model=cfg.model, host=cfg.host, temperature=cfg.temperature)

    def create_program(self, desc: str, module_path: str) -> RunResult:
        existing = self.tools.read(module_path)
        raw = self.llm.generate(program_prompt(desc, existing))
        content = strip_code_fences(raw)
        print(content)
        if not content:
            return RunResult(False, "Model returned empty module after sanitization.")
        self.tools.write(module_path, content + "\n")
        return RunResult(True, f"Wrote module: {module_path}")

    def create_tests(self, desc: str, module_path: str, tests_path: str) -> RunResult:
        module_code = self.tools.read(module_path)
        existing_tests = self.tools.read(tests_path)

        raw = self.llm.generate(tests_prompt(desc, module_path, module_code, existing_tests))
        content = strip_code_fences(raw)
        print(content)
        if not content:
            return RunResult(False, "Model returned empty tests after sanitization.")
        self.tools.write(tests_path, content + "\n")
        return RunResult(True, f"Wrote tests: {tests_path}")

    def tests_exist(self, tests_path: str) -> bool:
        return bool(self.tools.read(tests_path, max_chars=1))

    def _run_tests_with_coverage(self) -> Dict[str, Any]:
        cov_json_path = self.repo / ".coverage.json"
        cmd = f"coverage run -m pytest -q && coverage json -o {cov_json_path.name}"
        ok, out = self.tools.run(cmd)

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

    # Optional legacy method (no longer used by the two-step CLI).
    def improve_tests_to_target(
        self,
        desc: str,
        module_path: str,
        tests_path: str,
        max_iters: int,
        target_coverage: float,
    ) -> RunResult:
        for i in range(1, max_iters + 1):
            res = self._run_tests_with_coverage()
            ok = bool(res.get("ok"))
            out = str(res.get("pytest_output") or "")
            total = float(res.get("total_coverage_percent") or 0.0)
            cov_data = res.get("coverage_data", {}) or {}
            missing = _missing_lines_summary(cov_data, module_path)
            print(ok, out, total, cov_data)
            if ok and total >= target_coverage:
                return RunResult(
                    True,
                    f"Tests passed and coverage reached {total:.1f}%, target was {target_coverage:.1f}%. Iterations used: {i}.",
                    coverage=total,
                )

            module_code = self.tools.read(module_path)
            current_tests = self.tools.read(tests_path)
            prompt = improve_tests_prompt(desc, module_path, module_code, current_tests, out, missing)

            raw = self.llm.generate(prompt)
            content = strip_code_fences(raw)

            if not content:
                return RunResult(
                    False,
                    f"Iteration {i}: model returned empty tests after sanitization. Coverage={total:.1f}%.",
                    coverage=total,
                )

            self.tools.write(tests_path, content + "\n")

        res = self._run_tests_with_coverage()
        ok = bool(res.get("ok"))
        out = str(res.get("pytest_output") or "")
        total = float(res.get("total_coverage_percent") or 0.0)
        status = "passed" if ok else "failed"
        return RunResult(
            False,
            f"Stopped at max iterations. Final tests {status}. Coverage={total:.1f}%, target was {target_coverage:.1f}%.\nLast output:\n{out}",
            coverage=total,
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
