from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AppState:
    reviews: dict[str, dict[str, Any]] = field(default_factory=dict)
    drafts: dict[str, dict[str, Any]] = field(default_factory=dict)
    outcomes: dict[str, dict[str, Any]] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def save_review(self, payload: dict[str, Any]) -> str:
        review_id = f"rvw_{uuid.uuid4().hex[:10]}"
        with self.lock:
            self.reviews[review_id] = {"id": review_id, "created_at": _now_iso(), **payload}
        return review_id

    def get_review(self, review_id: str) -> dict[str, Any] | None:
        with self.lock:
            return self.reviews.get(review_id)

    def save_draft(self, payload: dict[str, Any]) -> str:
        draft_id = f"drf_{uuid.uuid4().hex[:10]}"
        with self.lock:
            self.drafts[draft_id] = {
                "id": draft_id,
                "created_at": _now_iso(),
                "status": "pending_approval",
                **payload,
            }
        return draft_id

    def get_draft(self, draft_id: str) -> dict[str, Any] | None:
        with self.lock:
            return self.drafts.get(draft_id)

    def update_draft(self, draft_id: str, **updates: Any) -> dict[str, Any] | None:
        with self.lock:
            if draft_id not in self.drafts:
                return None
            self.drafts[draft_id].update(updates)
            return self.drafts[draft_id]

    def save_outcome(self, payload: dict[str, Any]) -> str:
        outcome_id = f"out_{uuid.uuid4().hex[:10]}"
        with self.lock:
            self.outcomes[outcome_id] = {"id": outcome_id, "created_at": _now_iso(), **payload}
        return outcome_id
