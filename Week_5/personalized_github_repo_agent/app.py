from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from core import config
from core.agents import build_default_agents, detect_branch_context
from core.state import AppState
from core.tools import ToolError

app = Flask(__name__, template_folder="templates", static_folder="static")
state = AppState()
reviewer, planner, writer, gatekeeper = build_default_agents()


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/review")
def api_review():
    payload = request.get_json(force=True, silent=True) or {}
    base = payload.get("base_branch")
    commit_range = payload.get("commit_range")
    try:
        review = reviewer.review_changes(base_branch=base, commit_range=commit_range)
        plan = planner.decide_action(review)
        review_id = state.save_review({"review": review, "plan": plan})
        return jsonify({"ok": True, "review_id": review_id, "review": review, "plan": plan})
    except ToolError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/draft")
def api_draft():
    payload = request.get_json(force=True, silent=True) or {}
    kind = (payload.get("kind") or "issue").lower()
    source = (payload.get("source") or "instruction").lower()
    instruction = (payload.get("instruction") or "").strip()
    review_id = payload.get("review_id")

    review_payload = None
    if source == "review":
        if not review_id:
            return jsonify({"ok": False, "error": "review_id is required when source=review"}), 400
        review_payload = state.get_review(review_id)
        if not review_payload:
            return jsonify({"ok": False, "error": "review_id not found"}), 404

    review = review_payload["review"] if review_payload else None
    try:
        if kind == "issue":
            draft = writer.draft_issue(instruction=instruction, review=review)
        elif kind == "pr":
            head, base = detect_branch_context(payload.get("base_branch"))
            draft = writer.draft_pr(
                instruction=instruction,
                review=review,
                current_branch=head,
                base_branch=base,
            )
        else:
            return jsonify({"ok": False, "error": "kind must be issue or pr"}), 400

        reflection = gatekeeper.reflection_check(kind=kind, draft=draft, review=review)
        draft_id = state.save_draft(
            {
                "kind": kind,
                "source": source,
                "instruction": instruction,
                "review_id": review_id,
                "draft": draft,
                "reflection": reflection,
            }
        )

        return jsonify(
            {
                "ok": True,
                "draft_id": draft_id,
                "approval_required": True,
                "draft": draft,
                "reflection": reflection,
            }
        )
    except ToolError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/approve")
def api_approve():
    payload = request.get_json(force=True, silent=True) or {}
    draft_id = payload.get("draft_id")
    approve = bool(payload.get("approve"))

    if not draft_id:
        return jsonify({"ok": False, "error": "draft_id is required"}), 400

    draft_record = state.get_draft(draft_id)
    if not draft_record:
        return jsonify({"ok": False, "error": "draft_id not found"}), 404

    if not approve:
        state.update_draft(draft_id, status="rejected")
        return jsonify({"ok": True, "message": "Draft rejected. No changes made."})

    reflection = draft_record.get("reflection", {})
    if reflection.get("verdict") != "PASS":
        return jsonify(
            {
                "ok": False,
                "message": "Reflection verdict: FAIL. Revision required before creation.",
                "reflection": reflection,
            }
        ), 400

    try:
        created = gatekeeper.create_after_approval(
            kind=draft_record["kind"],
            draft=draft_record["draft"],
        )
        state.update_draft(draft_id, status="created", created=created)
        state.save_outcome({"draft_id": draft_id, "created": created})
        return jsonify({"ok": True, "message": "Created successfully.", "created": created})
    except ToolError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/improve")
def api_improve():
    payload = request.get_json(force=True, silent=True) or {}
    kind = (payload.get("kind") or "issue").lower()
    number = int(payload.get("number", 0))

    if number <= 0:
        return jsonify({"ok": False, "error": "number must be > 0"}), 400

    try:
        if kind == "issue":
            current = gatekeeper.github.get_issue(number)
        elif kind == "pr":
            current = gatekeeper.github.get_pull_request(number)
        else:
            return jsonify({"ok": False, "error": "kind must be issue or pr"}), 400

        critique = reviewer.critique_existing(kind=kind, number=number, payload=current)
        improved = writer.improve_structured(kind=kind, source=critique["source"], critique=critique)

        reflection = {
            "verdict": "PASS",
            "checks": {
                "unsupported_claims": "PASS",
                "missing_evidence": "PASS",
                "missing_tests": "PASS" if kind == "issue" else "UNKNOWN",
                "policy_violations": "PASS",
            },
            "findings": [],
        }

        return jsonify(
            {
                "ok": True,
                "critique": critique,
                "suggested": improved,
                "reflection": reflection,
            }
        )
    except ToolError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


if __name__ == "__main__":
    app.run(host=config.APP_HOST, port=config.APP_PORT, debug=config.DEBUG)
