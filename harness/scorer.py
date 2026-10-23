"""The scorer. One set of metrics, applied identically to every system.

This is the whole point of the repo: the numbers are only comparable if
the judging is the same. If a system's API returns its own "relevance"
score, we ignore it and re-derive relevance from ground truth.

No per-system grading logic. None.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScoredRun:
    system: str
    dataset: str
    available: bool = True
    note: str = ""
    metrics: dict[str, float] = field(default_factory=dict)
    per_question: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "system": self.system,
            "dataset": self.dataset,
            "available": self.available,
        }
        if not self.available:
            d["note"] = self.note
            return d
        d.update(self.metrics)
        return d


def hit_at_k(recalled: list[str], gold: set[str], k: int) -> bool:
    """True if at least one gold item is in the top-k recalled.

    ``recalled`` is in rank order (best first). ``gold`` is the set of
    correct answer identifiers.
    """
    head = recalled[:k]
    return any(x in gold for x in head)


def recall_at_k(recalled: list[str], gold: set[str], k: int) -> float:
    """Fraction of gold items present in the top-k.

    1.0 if all gold items are in the top-k, 0.0 if none, and the ratio
    in between.
    """
    if not gold:
        return 0.0
    head = set(recalled[:k])
    return len(head & gold) / len(gold)


def mrr_at_k(recalled: list[str], gold: set[str], k: int) -> float:
    """Mean reciprocal rank of the first hit, within top-k.

    0.0 if no gold item appears in the top-k.
    """
    for i, x in enumerate(recalled[:k], start=1):
        if x in gold:
            return 1.0 / i
    return 0.0


def score_question(
    recalled: list[str],
    gold: set[str],
) -> dict[str, float]:
    """Score one question. Returns per-metric values."""
    return {
        "hit@5": 1.0 if hit_at_k(recalled, gold, 5) else 0.0,
        "hit@10": 1.0 if hit_at_k(recalled, gold, 10) else 0.0,
        "recall@5": recall_at_k(recalled, gold, 5),
        "recall@10": recall_at_k(recalled, gold, 10),
        "mrr@10": mrr_at_k(recalled, gold, 10),
    }


def aggregate(per_question: list[dict[str, Any]]) -> dict[str, float]:
    """Average per-question scores into dataset-level metrics.

    All metrics are on a 0-100 scale for the report table; the per-question
    values stay 0-1 so a reader can inspect them.
    """
    if not per_question:
        return {}
    keys = per_question[0].get("metrics", {})
    out: dict[str, float] = {}
    for key in keys:
        vals = [q.get("metrics", {}).get(key, 0.0) for q in per_question]
        out[key] = round(100.0 * (sum(vals) / len(vals)), 1)
    out["questions"] = len(per_question)
    return out
