"""Naive baseline: full-context injection, no retrieval.

This is what most production deployments actually do today — stuff every
memory into the context window. If a memory system cannot beat this, it is
not earning its complexity.
"""
from __future__ import annotations

import os
from typing import Any

from systems.base import MemoryAdapter


class NaiveBaselineAdapter(MemoryAdapter):
    """Retrieval = return everything, in ingestion order.

    ``search()`` returns the last ``top_k`` entries for the user, with a
    uniform score of 1.0. No filtering, no ranking, no graph.
    """

    name = "naive"

    def __init__(self, workspace: str = "./tmp/bench") -> None:
        super().__init__(workspace)
        os.makedirs(self.workspace, exist_ok=True)

    def _path(self, user_id: str) -> str:
        return os.path.join(self.workspace, f"{user_id}.jsonl")

    def add(self, entries: list[dict[str, Any]], user_id: str) -> None:
        path = self._path(user_id)
        with open(path, "a", encoding="utf-8") as f:
            for e in entries:
                f.write(
                    __import__("json").dumps(
                        {"content": e.get("content", ""), "observation_date": e.get("observation_date", "")},
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    def search(self, query: str, user_id: str, top_k: int = 5) -> list[dict[str, Any]]:
        path = self._path(user_id)
        if not os.path.exists(path):
            return []
        lines = []
        with open(path, encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        import json as _json
        items = [_json.loads(ln) for ln in lines]
        tail = items[-top_k:] if len(items) > top_k else items
        return [
            {"memory": it.get("content", ""), "score": 1.0, "source": "naive-full-context"}
            for it in tail
        ]

    def reset(self, user_id: str) -> None:
        path = self._path(user_id)
        if os.path.exists(path):
            os.remove(path)
