"""Adapter base interface for benchmarked memory systems.

Every adapter implements the same three methods. The harness is
system-agnostic: it drives add(), search(), reset() and lets the scorer
judge the results. No per-system logic anywhere else in this repo.

NOTE: `is_available` and `availability_note` are plain attributes, not
methods, so the harness can read them without instantiation tricks.
"""
from __future__ import annotations

import abc
from typing import Any


class MemoryAdapter(abc.ABC):
    """The contract every benchmarked system must implement.

    Attributes
    ----------
    name:
        Human-readable system name, used in result tables.
    is_available:
        Whether the underlying system can run in this environment.
        Adapters that need a pip package or a server set this in
        ``__init__`` based on what they can actually import / reach.
    availability_note:
        A one-line reason for is_available == False, or "" otherwise.
    """

    name: str = "base"
    is_available: bool = True
    availability_note: str = ""

    def __init__(self, workspace: str = "./tmp/bench") -> None:
        self.workspace = workspace

    @abc.abstractmethod
    def add(self, entries: list[dict[str, Any]], user_id: str) -> None:
        """Ingest memory entries.

        ``entries`` is a list of dicts, each with at least:
          - ``content``: str, the raw text
          - ``observation_date``: str (ISO-8601), optional
          - ``metadata``: dict, optional

        Implementations may batch internally; the harness does not care.
        """

    @abc.abstractmethod
    def search(self, query: str, user_id: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Retrieve memories relevant to ``query``.

        Returns a list of dicts, each with at least:
          - ``memory`` or ``content``: str, the recalled text
          - ``score``: float, in [0, 1] or the system's native scale

        The scorer normalises scores; adapters must not pre-filter by
        threshold.
        """

    @abc.abstractmethod
    def reset(self, user_id: str) -> None:
        """Clear all memories for ``user_id``. Must be a clean state."""
