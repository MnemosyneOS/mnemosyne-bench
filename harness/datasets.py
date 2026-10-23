"""Dataset loaders. Each dataset exposes:

    load_questions() -> list[Question]

where ``Question`` is a dict with:
    - ``user_id``: str
    - ``entries``: list[dict] — what to add() before asking
    - ``query``: str
    - ``gold``: set[str] — identifiers of the correct memories

No dataset-specific logic leaks into the harness or the scorer.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Question:
    user_id: str
    entries: list[dict[str, Any]]
    query: str
    gold: set[str] = field(default_factory=set)
    dataset: str = ""


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _datasets_dir() -> str:
    return os.path.join(_repo_root(), "datasets")


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load(dataset_name: str, limit: int = 0) -> list[Question]:
    """Load questions for a dataset by name.

    Supported names: ``longmemeval``, ``locomo``, ``beam_1m``, ``beam_10m``,
    ``cn``. If the local dataset files are missing, returns an empty list
    (the runner records "dataset not downloaded" in the JSON output).
    """
    root = _datasets_dir()
    base = os.path.join(root, dataset_name)

    if dataset_name == "longmemeval":
        return _load_dir(base, root_name="longmemeval", dataset_label="longmemeval")
    if dataset_name == "locomo":
        return _load_dir(base, root_name="locomo", dataset_label="locomo")
    if dataset_name in ("beam_1m", "beam_10m"):
        return _load_dir(base, root_name=dataset_name, dataset_label=dataset_name)
    if dataset_name == "cn":
        return _load_dir(base, root_name="cn", dataset_label="cn")
    raise KeyError(f"unknown dataset: {dataset_name!r}")


def _load_dir(base: str, root_name: str, dataset_label: str) -> list[Question]:
    """A dataset directory holds ``questions.jsonl`` — one Question per line."""
    qpath = os.path.join(base, "questions.jsonl")
    raw = _load_jsonl(qpath)
    out: list[Question] = []
    for item in raw:
        q = Question(
            user_id=item.get("user_id", "default"),
            entries=item.get("entries", []),
            query=item.get("query", ""),
            gold=set(item.get("gold", [])),
            dataset=dataset_label,
        )
        out.append(q)
    return out
