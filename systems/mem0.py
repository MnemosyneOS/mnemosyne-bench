"""Mem0 adapter — provided so you can re-run Mem0 yourself.

We do not claim Mem0 numbers from their README. This adapter exists so a
stranger can run the same harness against their own Mem0 installation and
publish their own row.

Requires: `pip install mem0ai` and a configured LLM + vector store. Without
those, `is_available` stays False and the harness records the reason
instead of crashing.
"""
from __future__ import annotations

import importlib.util
from typing import Any

from systems.base import MemoryAdapter


class Mem0Adapter(MemoryAdapter):
    name = "mem0"

    def __init__(
        self,
        workspace: str = "./tmp/bench",
        mem0_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(workspace)
        self.config = mem0_config
        self._memories: dict[str, Any] = {}
        spec = importlib.util.find_spec("mem0")
        self.is_available = spec is not None
        if spec is None:
            self.availability_note = (
                "pip install mem0ai required, plus a configured LLM + vector store"
            )

    def _get(self, user_id: str):
        if user_id not in self._memories:
            mem0 = __import__("mem0")
            cls = getattr(mem0, "Memory", None) or getattr(mem0, "MemoryClient", None)
            if cls is None:
                raise RuntimeError("mem0 package imported but no Memory/MemoryClient found")
            self._memories[user_id] = cls(**(self.config or {}))
        return self._memories[user_id]

    def add(self, entries: list[dict[str, Any]], user_id: str) -> None:
        m = self._get(user_id)
        for e in entries:
            content = e.get("content", "")
            if not content:
                continue
            m.add(content, user_id=user_id)

    def search(self, query: str, user_id: str, top_k: int = 5) -> list[dict[str, Any]]:
        m = self._get(user_id)
        out = m.search(query, user_id=user_id, top_k=top_k)
        # mem0 returns {"results": [...]} in recent versions; older ones return a list
        if isinstance(out, dict):
            items = out.get("results", out.get("memories", []))
        elif isinstance(out, list):
            items = out
        else:
            items = []
        return [
            {
                "memory": r.get("memory", r.get("text", "")),
                "score": r.get("score", 0.0),
            }
            for r in items
        ]

    def reset(self, user_id: str) -> None:
        m = self._get(user_id)
        try:
            m.delete_all(user_id=user_id)
        except Exception:
            # older mem0: reset the whole client
            del self._memories[user_id]
