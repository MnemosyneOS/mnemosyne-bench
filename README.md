# mnemosyne-bench

**Reproducible benchmarks for AI agent memory systems.**

Every memory engine claims high recall. None of them ships the harness.
This repository does: run it, change the dataset, add your own system,
publish your own table.

## Results

Latest run: **2026-10-24** · full log in
[results/2026-10-24.md](results/2026-10-24.md)

| System | LongMemEval | LoCoMo | BEAM 1M | BEAM 10M |
|---|---|---|---|---|
| **Mnemosyne OS 8.1.0** | **96.2** | **94.8** | **68.5** | **53.9** |
| Mem0 (as published) | 94.4 | 92.5 | 64.1 | 48.6 |
| Naive baseline (full-context injection) | — | — | — | — |

> Mem0's figures are the ones Mem0 publishes at
> [mem0.ai/research](https://mem0.ai/research). We did not re-run Mem0; the
> adapter in `systems/mem0.py` exists so you can.
>
> Scores out of 100. `—` means "not yet measured". We do not fill cells we
> have not actually run.

## Run it

```bash
git clone https://github.com/MnemosyneOS/mnemosyne-bench
cd mnemosyne-bench
python -m harness.run --systems mnemosyne,naive --datasets longmemeval
```

Output lands in `results/` as a human-readable `.md` and a machine-readable
`.json`.

## What's in the box

- **One scorer for every system** — `harness/scorer.py`. No per-system
  grading logic. Every system is judged by the same metric.
- **Adapters, not forks** — each system in `systems/` implements the same
  three-method interface (`add`, `search`, `reset`) from `systems/base.py`.
- **A naive baseline that matters** — `systems/naive.py` is full-context
  injection. It is what most people actually ship. If a memory system cannot
  beat it, the system is the problem.
- **Machine-readable output** — `results/*.json`. Diff two runs directly.

## Datasets

| Dataset | What it tests | Source |
|---|---|---|
| LongMemEval | Long-horizon conversational recall | [research repo](https://github.com/longmemeval/longmemeval) |
| LoCoMo | Multi-session dialogue memory | [locomo](https://github.com/snap-research/locomo) |
| BEAM (1M / 10M) | Recall under a 1M / 10M-token context budget | this repo, `datasets/beam/` |
| CN-Scenarios | Chinese preference / temporal / code-evolution / sensitivity | this repo, `datasets/cn/` |

Download scripts and checksums live in `datasets/`. We do not commit raw
datasets to git; the scripts fetch them and verify integrity.

## Why this exists

Recall numbers in READMEs are marketing. Recall numbers with a harness are
engineering. The gap between those two things is this repository.

## Contributing a system

1. Implement the three methods in `systems/base.py`.
2. Add your system to `harness/run.py`'s registry.
3. Run the full suite and attach the JSON output to your PR.
4. We re-run it before merging. If it does not reproduce, it does not go in.

## The three red lines

1. **No cells we have not measured.** Empty is better than wrong.
2. **Reproducible by a stranger.** `git clone` + one command must work.
3. **Open adapters.** Anyone can add a system. That is the difference
   between a benchmark and an advertisement.

## License

MIT — see [LICENSE](LICENSE).
