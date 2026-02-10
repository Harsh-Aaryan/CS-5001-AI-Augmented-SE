from __future__ import annotations

import argparse
import os

from .agent import Agent
from .types import AgentConfig
from .utils import (
    ensure_model_available,
    ensure_ollama_available,
    ensure_repo_path,
    parse_coverage_target,
)

DEFAULT_MODEL = "devstral-small-2:24b-cloud"
DEFAULT_HOST = "http://localhost:11434"


def main() -> None:
    p = argparse.ArgumentParser(
        prog="cca",
        description=(
            "Classroom CLI agent (Ollama-only). Generates code and tests with an Ollama model. "
            "Two-step workflow: generate tests, then generate a test report."
        ),
    )
    p.add_argument("--repo", required=True, help="Repository path")
    p.add_argument(
        "--model",
        default=os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL),
        help=f"Ollama model (default: {DEFAULT_MODEL})",
    )
    p.add_argument(
        "--host",
        default=os.environ.get("OLLAMA_HOST", DEFAULT_HOST),
        help=f"Ollama host (default: {DEFAULT_HOST})",
    )
    p.add_argument(
        "--temperature",
        type=float,
        default=float(os.environ.get("OLLAMA_TEMPERATURE", "0.0")),
        help="Sampling temperature (default: 0.0)",
    )
    # Kept for backward compatibility with existing configs; not used by the two-step flow.
    p.add_argument("--max-iters", type=int, default=6, help="(Unused) Max iterations for test improvement")
    p.add_argument("--verbose", action="store_true", help="Verbose output")

    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create", help="Create/update a program module from a description")
    c.add_argument("--desc", required=True, help="Natural language description/spec")
    c.add_argument("--module", required=True, help="Relative path to module file, e.g., src/program.py")

    gt = sub.add_parser("gen-tests", help="Step 1: Generate/update pytest tests for a module (no execution)")
    gt.add_argument("--desc", required=True, help="Natural language description/spec")
    gt.add_argument("--module", required=True, help="Relative path to module file, e.g., src/program.py")
    gt.add_argument("--tests", required=True, help="Relative path to tests file, e.g., tests/test_program.py")
    gt.add_argument("--overwrite", action="store_true", help="Overwrite tests file if it already exists")

    rp = sub.add_parser("report", help="Step 2: Run pytest with coverage and write a structured report")
    rp.add_argument(
        "--module",
        default=None,
        help="Relative module path to include per-file coverage details (optional)",
    )
    rp.add_argument(
        "--report-out",
        default="reports/test_report.json",
        help="Relative path for JSON report output (default: reports/test_report.json)",
    )
    rp.add_argument(
        "--report-md",
        default=None,
        help="Optional relative path for a Markdown report (e.g., reports/test_report.md)",
    )
    rp.add_argument(
        "--fail-on-coverage",
        default=None,
        help="If set, fail (exit non-zero) when total coverage is below this target (e.g., '95%').",
    )
    rp.add_argument(
        "--fail-on-tests",
        action="store_true",
        help="If set, fail (exit non-zero) when pytest fails.",
    )

    cm = sub.add_parser("commit", help="Commit and optionally push changes")
    cm.add_argument("--message", required=True, help="Commit message")
    cm.add_argument("--push", action="store_true", help="Also run git push")

    # Note: the prior "full" command was removed because it mixed generation, execution, and iteration.

    args = p.parse_args()

    ensure_repo_path(args.repo)
    ensure_ollama_available()
    ensure_model_available(args.model)

    cfg = AgentConfig(
        repo=args.repo,
        model=args.model,
        host=args.host,
        temperature=args.temperature,
        max_iters=args.max_iters,
        verbose=args.verbose,
    )
    agent = Agent(cfg)

    if args.cmd == "create":
        r = agent.create_program(args.desc, args.module)

    elif args.cmd == "gen-tests":
        if (not args.overwrite) and agent.tests_exist(args.tests):
            raise SystemExit(
                f"Tests file already exists: {args.tests}. Use --overwrite to replace it."
            )
        r = agent.create_tests(args.desc, args.module, args.tests)

    elif args.cmd == "report":
        cov_target = parse_coverage_target(args.fail_on_coverage) if args.fail_on_coverage else None
        r = agent.generate_test_report(
            module_path=args.module,
            report_out_path=args.report_out,
            report_md_path=args.report_md,
            fail_on_tests=args.fail_on_tests,
            fail_on_coverage=cov_target,
        )

    else:  # commit
        r = agent.commit_and_push(args.message, args.push)

    raise SystemExit(0 if r.ok else r.details)
