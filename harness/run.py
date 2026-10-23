"""The runner. Drives every adapter through every dataset with the same
scorer, and writes results out as JSON + a markdown table.

Usage:
    python -m harness.run --systems mnemosyne,naive --datasets longmemeval,cn
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import time

from harness.datasets import load
from harness.scorer import ScoredRun, aggregate, score_question
from systems import available, build


def run_one(system_name: str, dataset_name: str, workspace: str,
            mem0_config: dict | None = None,
            zep_config: dict | None = None,
            limit: int = 0) -> ScoredRun:
    adapter = _instantiate(system_name, workspace, mem0_config, zep_config)
    if not adapter.is_available:
        return ScoredRun(
            system=system_name,
            dataset=dataset_name,
            available=False,
            note=adapter.availability_note,
        )

    questions = load(dataset_name, limit=limit)
    if not questions:
        return ScoredRun(
            system=system_name,
            dataset=dataset_name,
            available=True,
            note="dataset not downloaded (run scripts/download_dataset.py)",
        )

    per_q = []
    for q in questions:
        # reset the user's state for this question
        adapter.reset(q.user_id)
        adapter.add(q.entries, q.user_id)
        recalled = adapter.search(q.query, q.user_id, top_k=10)
        texts = [r.get("memory", r.get("content", "")) for r in recalled]
        metrics = score_question(texts, q.gold)
        per_q.append(
            {
                "query": q.query,
                "user_id": q.user_id,
                "metrics": metrics,
                "top5": texts[:5],
            }
        )

    return ScoredRun(
        system=system_name,
        dataset=dataset_name,
        available=True,
        metrics=aggregate(per_q),
        per_question=per_q,
    )


def _instantiate(system_name: str, workspace: str,
                 mem0_config: dict | None, zep_config: dict | None):
    kwargs = {"workspace": workspace}
    if system_name == "mem0" and mem0_config:
        kwargs["mem0_config"] = mem0_config
    if system_name == "zep" and zep_config:
        kwargs["zep_config"] = zep_config
    return build(system_name, **kwargs)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", default="mnemosyne,naive")
    ap.add_argument("--datasets", default="longmemeval")
    ap.add_argument("--workspace", default="./tmp/bench")
    ap.add_argument("--limit", type=int, default=0,
                    help="max questions per dataset (0 = all)")
    ap.add_argument("--out", default="./results",
                    help="output directory for .json + .md")
    args = ap.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    stamp = _dt.date.today().isoformat()
    run_id = f"{stamp}-{int(time.time()) % 1000000:06d}"

    systems = [s.strip() for s in args.systems.split(",") if s.strip()]
    datasets = [d.strip() for d in args.datasets.split(",") if d.strip()]

    runs: list[ScoredRun] = []
    for sys_name in systems:
        for ds in datasets:
            print(f"running {sys_name} on {ds} ...")
            runs.append(run_one(sys_name, ds, args.workspace, limit=args.limit))

    # ---- JSON output -------------------------------------------------
    json_path = os.path.join(args.out, f"{run_id}.json")
    payload = {
        "run_id": run_id,
        "date": stamp,
        "systems": systems,
        "datasets": datasets,
        "results": [r.to_dict() for r in runs],
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"wrote {json_path}")

    # ---- markdown table -------------------------------------------
    md_path = os.path.join(args.out, f"{run_id}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        _write_markdown(f, payload)
    print(f"wrote {md_path}")

    # ---- quick console summary --------------------------------------
    print("\n--- summary ---")
    for r in runs:
        if not r.available:
            print(f"  {r.system:12s} {r.dataset:12s}  UNAVAILABLE: {r.note}")
            continue
        if "hit@5" in r.metrics:
            print(
                f"  {r.system:12s} {r.dataset:12s}  "
                f"hit@5={r.metrics['hit@5']:.1f}  "
                f"recall@10={r.metrics['recall@10']:.1f}  "
                f"mrr@10={r.metrics['mrr@10']:.1f}  "
                f"n={r.metrics.get('questions', '?')}"
            )
        else:
            print(f"  {r.system:12s} {r.dataset:12s}  {r.metrics}")
    return 0


def _write_markdown(f, payload: dict) -> None:
    print_table = [
        "hit@5", "hit@10", "recall@5", "recall@10", "mrr@10",
    ]
    f.write(f"# Run {payload['run_id']}\n\n")
    f.write(f"- date: {payload['date']}\n")
    f.write(f"- systems: {', '.join(payload['systems'])}\n")
    f.write(f"- datasets: {', '.join(payload['datasets'])}\n\n")
    f.write("| System | Dataset | " + " | ".join(print_table) + " | n |\n")
    f.write("|---|---|" + "---|" * len(print_table) + "---|\n")
    for r in payload["results"]:
        if not r.get("available"):
            f.write(
                f"| {r['system']} | {r['dataset']} | "
                + " — | " * 5 + f"| {r.get('note', '')} |\n"
            )
            continue
        row = [f"{r.get(k, '—')}" if k in r else "—" for k in print_table]
        f.write(f"| {r['system']} | {r['dataset']} | " + " | ".join(row) + f" | {r.get('questions', '—')} |\n")


if __name__ == "__main__":
    sys.exit(main())
