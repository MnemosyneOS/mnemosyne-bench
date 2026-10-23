"""Dataset download + integrity check.

We do not commit raw datasets to git — they are third-party assets and
often large. This script fetches them once and verifies SHA-256.

Usage:
    python scripts/download_dataset.py longmemeval
    python scripts/download_dataset.py cn        # no download needed; generated locally
"""
from __future__ import annotations

import hashlib
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(ROOT, "datasets")

# url + expected sha256. sha256 = "" means "not yet pinned" — the first
# download records the hash and prints it for the maintainer to pin.
SOURCES: dict[str, dict] = {
    "longmemeval": {
        # LongMemEval is distributed via Hugging Face; replace with the
        # canonical URL you verify in 2026. We deliberately do not guess.
        "url": "",
        "sha256": "",
        "note": "Set the canonical dataset URL before first use.",
    },
    "locomo": {
        "url": "",
        "sha256": "",
        "note": "Set the canonical dataset URL before first use.",
    },
    "beam_1m": {
        "url": "",
        "sha256": "",
        "note": "BEAM is generated locally by scripts/generate_beam.py.",
    },
    "beam_10m": {
        "url": "",
        "sha256": "",
        "note": "BEAM is generated locally by scripts/generate_beam.py.",
    },
    "cn": {
        "url": "",
        "sha256": "",
        "note": "CN-Scenarios is generated locally by scripts/generate_cn.py.",
    },
}


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/download_dataset.py <name>")
        print("known:", ", ".join(SOURCES))
        return 1
    name = sys.argv[1]
    if name not in SOURCES:
        print(f"unknown dataset {name!r}; known: {', '.join(SOURCES)}")
        return 1
    src = SOURCES[name]
    target_dir = os.path.join(DATASETS_DIR, name)
    os.makedirs(target_dir, exist_ok=True)

    if not src["url"]:
        print(f"[{name}] no download URL pinned yet.")
        print(f"  note: {src['note']}")
        print(f"  expected local file: {os.path.join(target_dir, 'questions.jsonl')}")
        return 0

    dest = os.path.join(target_dir, "raw.jsonl")
    print(f"downloading {src['url']} -> {dest}")
    urllib.request.urlretrieve(src["url"], dest)
    got = sha256_of(dest)
    if src["sha256"] and got != src["sha256"]:
        print(f"SHA-256 MISMATCH:\n  expected {src['sha256']}\n  got      {got}")
        return 2
    if not src["sha256"]:
        print(f"pinned (first run): sha256={got}")
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
