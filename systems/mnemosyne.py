"""Mnemosyne OS adapter.

Wraps the `mnemosyne-os` PyPI package. Core is zero-dependency; the adapter
needs no extra install beyond `pip install mnemosyne-os`.
"""
from __future__ import annotations

import importlib.util
from typing import Any

from systems.base import MemoryAdapter


class MnemosyneAdapter(MemoryAdapter):
    """Uses `mnemosyne.api.Memory` (engine-backed client).

    The engine's built-in embedder + rule-based extractor means this adapter
    works fully offline. If you want to compare against a real-LLM
    configuration, set ``mnemosyne_config`` in the constructor.
    """

    name = "mnemosyne"

    def __init__(
        self,
        workspace: str = "./tmp/bench",
        mnemosyne_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(workspace)
        self.config = mnemosyne_config
        self._memories: dict[str, Any] = {}
        spec = importlib.util.find_spec("mnemosyne")
        self.is_available = spec is not None
        if spec is None:
            self.availability_note = "pip install mnemosyne-os required"

    def _get(self, user_id: str):
        if user_id not in self._memories:
            mnemosyne = __import__("mnemosyne")
            if self.config is None:
                self._memories[user_id] = mnemosyne.Memory()
            else:
                self._memories[user_id] = mnemosyne.Memory.from_config(self.config)
        return self._memories[user_id]

    def add(self, entries: list[dict[str, Any]], user_id: str) -> None:
        m = self._get(user_id)
        for e in entries:
            content = e.get("content", "")
            if not content:
                continue
            kwargs: dict[str, Any] = {"user_id": user_id}
            if e.get("observation_date"):
                kwargs["observation_date"] = e["observation_date"]
            if e.get("metadata"):
                kwargs["metadata"] = e["metadata"]
            m.add(content, **kwargs)

    def search(self, query: str, user_id: str, top_k: int = 5) -> list[dict[str, Any]]:
        m = self._get(user_id)
        out = m.search(query, filters={"user_id": user_id}, top_k=top_k)
        results = out.get("results", out if isinstance(out, list) else [])
        return [
            {"memory": r.get("memory", r.get("content", "")), "score": r.get("score", 0.0)}
            for r in results
        ]

    def reset(self, user_id: str) -> None:
        m = self._get(user_id)
        try:
            m.delete_all(user_id=user_id)
        except Exception:
            m.reset(user_id=user_id)
