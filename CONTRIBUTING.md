# Contributing a system to mnemosyne-bench

## The contract

A system is a `MemoryAdapter` subclass in `systems/` with three methods:

```python
from systems.base import MemoryAdapter

class MyAdapter(MemoryAdapter):
    name = "mysystem"

    def add(self, entries, user_id): ...
    def search(self, query, user_id, top_k=5): ...
    def reset(self, user_id): ...
```

`add()` ingests, `search()` returns a ranked list of dicts
(`{"memory": ..., "score": ...}`), `reset()` clears the user's state.
The scorer does the judging — your adapter must not grade itself.

## The three red lines

1. **No cells you have not measured.** Run the full suite before
   attaching results to your PR.
2. **Reproducible by a stranger.** `pip install <your-package>` must be
   the only prerequisite, or `is_available()` returns False with a clear
   note.
3. **Open adapter.** Implement the base interface; do not special-case
   your system in `harness/`. If you need to, the interface is missing
   something — fix the interface.

## PR checklist

- [ ] `systems/<name>.py` added, three methods implemented
- [ ] `is_available()` works (returns False + note when the dep is missing)
- [ ] Full suite run, `results/*.json` attached to the PR
- [ ] A row for your system in `README.md`'s results table
- [ ] No change to `harness/scorer.py` or `harness/run.py`
