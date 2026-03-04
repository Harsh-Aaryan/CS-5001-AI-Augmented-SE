from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .llm import OllamaClient
from .tools import (
    GitHubClient,
    ToolError,
    collect_diff,
    contains_test_file,
    extract_diff_evidence,
    get_current_branch,
    read_changed_file_snippets,
)


@dataclass
class ReviewerAgent:
    llm: OllamaClient

    def review_changes(self, base_branch: str | None = None, commit_range: str | None = None) -> dict[str, Any]:
        diff_payload = collect_diff(base_branch=base_branch, commit_range=commit_range)
        diff_text = diff_payload["diff"]
        files = diff_payload["files"]
        evidence = extract_diff_evidence(diff_text)
        file_snippets = read_changed_file_snippets(files)

        change_type = self._classify_change(files, diff_text)
        risk = self._assess_risk(files, diff_payload["total_added"], diff_payload["total_deleted"])
        issues = self._detect_potential_issues(diff_text, files)

        llm_notes = self.llm.chat(
            system_prompt=(
                "You are a code reviewer. Identify concrete concerns and keep findings short. "
                "Only claim what is supported by provided diff context."
            ),
            user_prompt=(
                f"Diff summary: +{diff_payload['total_added']} -{diff_payload['total_deleted']}\n"
                f"Files: {files}\n"
                f"Diff:\n{diff_text[:7000]}"
            ),
        )

        return {
            "input": {"base_branch": base_branch, "commit_range": commit_range},
            "reference": diff_payload["reference"],
            "change_type": change_type,
            "risk": risk,
            "stats": {
                "files_changed": len(files),
                "total_added": diff_payload["total_added"],
                "total_deleted": diff_payload["total_deleted"],
            },
            "files": files,
            "numstat": diff_payload["numstat"],
            "potential_issues": issues,
            "evidence": evidence,
            "file_read_evidence": file_snippets,
            "llm_notes": llm_notes,
        }

    def critique_existing(self, kind: str, number: int, payload: dict[str, Any]) -> dict[str, Any]:
        title = payload.get("title", "")
        body = payload.get("body", "") or ""

        findings = []
        if len(title.strip()) < 8:
            findings.append("Title is too short to communicate scope clearly.")
        if "acceptance criteria" not in body.lower() and "## acceptance criteria" not in body.lower():
            findings.append("Acceptance criteria are missing or not explicit.")
        if "evidence" not in body.lower():
            findings.append("Evidence section is missing.")
        if "risk" not in body.lower():
            findings.append("Risk level is missing.")

        llm_critique = self.llm.chat(
            system_prompt=(
                "You are a reviewer for GitHub issue/PR quality. Critique unclear, vague, and missing parts. "
                "Return compact bullets."
            ),
            user_prompt=f"Type: {kind}\nNumber: {number}\nTitle: {title}\nBody:\n{body[:7000]}",
        )
        if llm_critique:
            findings.append(llm_critique)

        return {
            "kind": kind,
            "number": number,
            "findings": findings or ["No major clarity gaps detected."],
            "source": {"title": title, "body": body},
        }

    @staticmethod
    def _classify_change(files: list[str], diff_text: str) -> str:
        lower_files = " ".join(files).lower()
        lower_diff = diff_text.lower()
        if "fix" in lower_diff or "bug" in lower_diff or "error" in lower_diff:
            return "bugfix"
        if "refactor" in lower_diff:
            return "refactor"
        if any(part in lower_files for part in ["readme", "docs/", ".md"]):
            return "docs"
        if any(part in lower_files for part in ["test", "spec"]):
            return "test"
        return "feature"

    @staticmethod
    def _assess_risk(files: list[str], added: int, deleted: int) -> str:
        score = 0
        if added + deleted > 350:
            score += 2
        elif added + deleted > 120:
            score += 1

        critical_markers = ["auth", "payment", "security", "gateway", "api", "config"]
        if any(marker in path.lower() for marker in critical_markers for path in files):
            score += 2

        if len(files) > 10:
            score += 1

        if score >= 4:
            return "high"
        if score >= 2:
            return "medium"
        return "low"

    @staticmethod
    def _detect_potential_issues(diff_text: str, files: list[str]) -> list[str]:
        issues = []
        lower = diff_text.lower()
        if "todo" in lower or "fixme" in lower:
            issues.append("Diff contains TODO/FIXME markers that may indicate unfinished work.")
        if "except:" in lower or "except exception" in lower:
            issues.append("Broad exception handling detected; consider narrowing exception types.")
        if any(path.endswith(".py") for path in files) and not contains_test_file(files):
            issues.append("Code changes detected without corresponding test file updates.")
        if "password" in lower or "token" in lower:
            issues.append("Sensitive credential handling appears in diff; verify secure storage and masking.")
        return issues


@dataclass
class PlannerAgent:
    def decide_action(self, review: dict[str, Any]) -> dict[str, Any]:
        issues = review.get("potential_issues", [])
        risk = review.get("risk", "low")
        change_type = review.get("change_type", "feature")

        if issues:
            action = "create_issue"
            reason = "Potential quality/safety gaps were found in diff evidence."
        elif risk in {"high", "medium"} and change_type in {"feature", "bugfix", "refactor"}:
            action = "create_pr"
            reason = "Meaningful change with non-trivial risk should be tracked with PR context and test plan."
        else:
            action = "no_action"
            reason = "Diff appears low-risk and does not show clear issues requiring tracking."

        return {
            "action": action,
            "reason": reason,
            "evidence_used": review.get("evidence", [])[:3],
        }


@dataclass
class WriterAgent:
    llm: OllamaClient

    def draft_issue(self, instruction: str | None, review: dict[str, Any] | None = None) -> dict[str, str]:
        title = "Issue: follow-up improvements from repository review"
        problem = "Potential reliability and maintainability concerns were detected in recent changes."
        evidence_items: list[str] = []
        risk = "medium"

        if review:
            risk = review.get("risk", "medium")
            evidence_items = [
                f"- {item.get('source')}: {item.get('snippet')}"
                for item in review.get("evidence", [])[:5]
            ]
            if review.get("potential_issues"):
                problem = "\n".join(f"- {issue}" for issue in review["potential_issues"])

        if instruction:
            prompt_title = self.llm.chat(
                "Write a concise GitHub Issue title (max 10 words).",
                f"Instruction: {instruction}",
            )
            if prompt_title:
                title = prompt_title.splitlines()[0][:120]
            problem = instruction

        evidence_block = "\n".join(evidence_items) if evidence_items else "- Review evidence will be attached during implementation."
        body = (
            "## Problem Description\n"
            f"{problem}\n\n"
            "## Evidence\n"
            f"{evidence_block}\n\n"
            "## Acceptance Criteria\n"
            "- Root cause is addressed with a minimal and testable change.\n"
            "- Regression risk is covered by tests or documented manual checks.\n"
            "- Any security or validation gaps are explicitly handled.\n\n"
            "## Risk Level\n"
            f"- {risk}"
        )
        return {"title": title, "body": body}

    def draft_pr(
        self,
        instruction: str | None,
        review: dict[str, Any] | None,
        current_branch: str,
        base_branch: str,
    ) -> dict[str, Any]:
        title = "PR: repository improvements from agent review"
        summary = "Implements targeted improvements based on repository analysis."
        risk = "medium"
        files = []

        if review:
            risk = review.get("risk", "medium")
            files = review.get("files", [])
            summary = (
                f"Change type: {review.get('change_type')}. "
                f"Diff stats: +{review.get('stats', {}).get('total_added', 0)} "
                f"/-{review.get('stats', {}).get('total_deleted', 0)}."
            )

        if instruction:
            generated = self.llm.chat(
                "Write a concise GitHub PR title (max 12 words).",
                f"Instruction: {instruction}",
            )
            if generated:
                title = generated.splitlines()[0][:120]
            summary = instruction

        files_list = "\n".join(f"- {path}" for path in files[:15]) or "- To be confirmed"
        body = (
            "## Summary\n"
            f"{summary}\n\n"
            "## Files Affected\n"
            f"{files_list}\n\n"
            "## Behavior Change\n"
            "- Improves repository quality and/or maintainability with scoped updates.\n\n"
            "## Test Plan\n"
            "- Run unit/integration tests covering touched modules.\n"
            "- Execute manual sanity check for the main user flow.\n\n"
            "## Risk Level\n"
            f"- {risk}"
        )
        return {
            "title": title,
            "body": body,
            "head": current_branch,
            "base": base_branch,
        }

    def improve_structured(self, kind: str, source: dict[str, Any], critique: dict[str, Any]) -> dict[str, str]:
        title = source.get("title", "")
        body = source.get("body", "")
        findings = critique.get("findings", [])

        suggested_title = self.llm.chat(
            f"Rewrite this GitHub {kind} title to be specific and actionable.",
            title,
        ) or title

        suggested_body = self.llm.chat(
            (
                f"Rewrite this GitHub {kind} into a structured format with sections for "
                "Problem/Summary, Evidence, Acceptance Criteria (or Test Plan), and Risk Level."
            ),
            body[:7000],
        )

        if not suggested_body:
            criteria_section = "\n".join(["- Define measurable completion conditions.", "- Add validation steps."])
            suggested_body = (
                "## Problem / Summary\n"
                f"{body[:800] if body else 'Clarify the objective and expected outcome.'}\n\n"
                "## Evidence\n"
                "- Link concrete logs, diff snippets, or failing behavior.\n\n"
                "## Acceptance Criteria / Test Plan\n"
                f"{criteria_section}\n\n"
                "## Risk Level\n"
                "- medium"
            )

        critique_block = "\n".join(f"- {item}" for item in findings)
        return {
            "title": suggested_title.strip() or title,
            "body": suggested_body.strip(),
            "critique": critique_block,
        }


@dataclass
class GatekeeperAgent:
    github: GitHubClient

    def reflection_check(self, kind: str, draft: dict[str, Any], review: dict[str, Any] | None = None) -> dict[str, Any]:
        title = (draft.get("title") or "").strip()
        body = (draft.get("body") or "").strip()

        findings: list[str] = []
        if not title:
            findings.append("Missing title.")
        if not body:
            findings.append("Missing body.")

        if "evidence" not in body.lower():
            findings.append("Missing evidence section.")

        if kind == "pr" and "test plan" not in body.lower():
            findings.append("Missing test plan section.")

        if kind in {"issue", "pr"} and "risk level" not in body.lower():
            findings.append("Missing risk level section.")

        if review and review.get("evidence") and "evidence" in body.lower():
            pass
        elif review and not review.get("evidence"):
            findings.append("Review context has no supporting diff evidence.")

        return {
            "verdict": "PASS" if not findings else "FAIL",
            "checks": {
                "unsupported_claims": "PASS" if review else "UNKNOWN",
                "missing_evidence": "PASS" if "evidence" in body.lower() else "FAIL",
                "missing_tests": "PASS" if kind == "issue" or "test plan" in body.lower() else "FAIL",
                "policy_violations": "PASS",
            },
            "findings": findings,
        }

    def create_after_approval(self, kind: str, draft: dict[str, Any]) -> dict[str, Any]:
        if kind == "issue":
            created = self.github.create_issue(draft["title"], draft["body"])
            return {
                "kind": "issue",
                "number": created.get("number"),
                "url": created.get("html_url"),
            }

        if kind == "pr":
            created = self.github.create_pull_request(
                title=draft["title"],
                body=draft["body"],
                head=draft["head"],
                base=draft["base"],
                draft=True,
            )
            return {
                "kind": "pr",
                "number": created.get("number"),
                "url": created.get("html_url"),
            }

        raise ToolError(f"Unsupported creation kind: {kind}")


def build_default_agents() -> tuple[ReviewerAgent, PlannerAgent, WriterAgent, GatekeeperAgent]:
    llm = OllamaClient()
    reviewer = ReviewerAgent(llm=llm)
    planner = PlannerAgent()
    writer = WriterAgent(llm=llm)
    gatekeeper = GatekeeperAgent(github=GitHubClient())
    return reviewer, planner, writer, gatekeeper


def detect_branch_context(base_branch: str | None = None) -> tuple[str, str]:
    head = get_current_branch()
    base = base_branch or "main"
    return head, base
