"""One-shot verification that the harness imports and runs end-to-end.

Run from the repo root:
    python scripts/verify_harness.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    from harness.scorer import score_question, aggregate
    from harness.run import run_one

    # scorer sanity
    m = score_question(["a", "b", "c"], {"b"})
    assert m["hit@5"] == 1.0, m
    assert m["hit@10"] == 1.0, m
    assert m["mrr@10"] == 1.0 / 2, m
    agg = aggregate([{"metrics": m}, {"metrics": m}])
    assert agg["hit@5"] == 100.0, agg
    assert agg["questions"] == 2, agg
    print("scorer ok")

    # naive adapter round-trip
    from systems.naive import NaiveBaselineAdapter
    a = NaiveBaselineAdapter(workspace="./tmp/verify_harness")
    a.reset("u1")
    a.add([{"content": "the cat is on the mat"}, {"content": "the dog barks"}], "u1")
    hits = a.search("cat", "u1", top_k=2)
    assert any("cat" in h["memory"] for h in hits), hits
    a.reset("u1")
    assert a.search("cat", "u1", top_k=2) == []
    print("naive adapter ok")

    # run_one on the generated CN dataset must score 0 for the naive
    # baseline on the preference-flip question (the correct answer, index
    # 0 and 3, is not in the tail window). A non-zero score would mean
    # the scorer is not actually grading.
    r = run_one("naive", "cn", workspace="./tmp/verify_harness")
    assert r.available, r.note
    assert r.metrics.get("hit@5") == 0.0, r.metrics
    assert r.metrics.get("questions") == 6, r.metrics
    print(f"run_one naive/cn -> hit@5={r.metrics.get('hit@5')} n={r.metrics.get('questions')}")
    print("verify_harness PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
