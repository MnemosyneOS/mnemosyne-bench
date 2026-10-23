"""Zep (Graphiti) adapter.

Requires: `pip install zep-python` plus a running Zep server or Graphiti
endpoint. Without a reachable server, `is_available()` returns False and
the harness records the reason.
"""
from __future__ import annotations

import importlib.util
from typing import Any

from systems.base import MemoryAdapter


class ZepAdapter(MemoryAdapter):
    name = "zep"

    def __init__(
        self,
        workspace: str = "./tmp/bench",
        zep_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(workspace)
        self.config = zep_config or {}
        self._clients: dict[str, Any] = {}
        import importlib.util as _ilu
        spec = _ilu.find_spec("zep")
        self.is_available = spec is not None
        if spec is None:
            self.availability_note = "pip install zep-python required, plus a running Zep/Graphiti endpoint"

    def _get(self, user_id: str):
        if user_id not in self._clients:
            zep = importlib.import_module("zep")
            cls = getattr(zep, "Zep", None) or getattr(zep, "ZepClient", None)
            if cls is None:
                raise RuntimeError("zep package imported but no Zep/ZepClient found")
            kwargs = dict(self.config)
            self._clients[user_id] = cls(**kwargs)
        return self._clients[user_id]

    def add(self, entries: list[dict[str, Any]], user_id: str) -> None:
        c = self._get(user_id)
        for e in entries:
            content = e.get("content", "")
            if not content:
                continue
            # Zep's session API varies by version; use the most common shape
            session = c.create_session(user_id=user_id) if hasattr(c, "create_session") else None
            if session is not None and hasattr(session, "add_message"):
                session.add_message("user", content)
            else:
                # fall back to a direct add if the version exposes one
                add_fn = getattr(c, "add", None) or getattr(c, "add_memory", None)
                if add_fn:
                    add_fn(content, user_id=user_id)
                else:
                    raise RuntimeError("zep client exposes neither session nor add()")

    def search(self, query: str, user_id: str, top_k: int = 5) -> list[dict[str, Any]]:
        c = self._get(user_id)
        search_fn = getattr(c, "search", None) or getattr(c, "search_memories", None)
        if search_fn is None:
            raise RuntimeError("zep client exposes no search()")
        out = search_fn(query, user_id=user_id, top_k=top_k)
        if isinstance(out, dict):
            items = out.get("results", out.get("memories", []))
        elif isinstance(out, list):
            items = out
        else:
            items = []
        return [
            {"memory": r.get("memory", r.get("text", "")), "score": r.get("score", 0.0)}
            for r in items
        ]

    def reset(self, user_id: str) -> None:
        c = self._get(user_id)
        for attr in ("delete_all", "reset", "clear"):
            fn = getattr(c, attr, None)
            if callable(fn):
                fn(user_id=user_id)
                break
        self._clients.pop(user_id, None)
