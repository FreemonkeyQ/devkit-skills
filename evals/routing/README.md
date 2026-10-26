# Full routing matrix

Deterministic lexical check over all 19 skill descriptions. It is a pre-filter,
not a model or host run: use real Skill invocation logs as authoritative
evidence.

## Run

```bash
python3 evals/routing/matrix.py --check   # schema + skill coverage only
python3 evals/routing/matrix.py           # full matrix, writes results/
python3 evals/routing/matrix.py --min-top1 0.7   # optional gate
```

`results/` is a runtime artefact and stays untracked.

Host confirmation (paid model calls, explicit approval required):

```bash
python3 evals/routing/host_matrix.py --dry-run
python3 evals/routing/host_matrix.py --limit 1     # smoke
python3 evals/routing/host_matrix.py               # 19 positives + 12 hard negatives
python3 evals/routing/host_matrix.py --ids P-arch-1 --explicit   # Skill tool control
python3 evals/routing/host_matrix.py --reanalyze <run-dir>       # no new model calls
python3 evals/routing/host_matrix.py --resume <run-dir> --workers 4
```

`host_matrix.py` copies `fixtures/sandbox` to a temporary directory, runs the
prompt verbatim with `--plugin-dir` and records actual `Skill` tool calls. It
uses plan mode and denies `Write`, `Edit`, `Bash`, `WebFetch`, `WebSearch`; a
positive control with `--explicit` proves the Skill tool itself is available.

Two hosts are supported (`--host claude` default, `--host qoder`):

```bash
python3 evals/routing/host_matrix.py --model 'claude[1M]'            # Claude Code
python3 evals/routing/host_matrix.py --host qoder -m claude-fable-5 --workers 1
```

The Qoder arm is **experimental**: it depends on the CLI's internal env vars
and versioned binary path, and its channel content filter deterministically
refuses many short Chinese prompts. Keep it single-worker and treat partial
results as a sample, not a baseline.

The dataset is guarded by `tests/test_routing_evals.py`, which CI already runs
via `unittest discover`; `matrix.py --check` is the same validation for manual
use and does not need a separate workflow step.

## Dataset

`scenarios.json` has 87 cases:

- 57 positives: 3 per skill, written as user speech rather than copied from
  `description`, so the matrix does not reward description echo.
- 18 negatives: adjacent-skill confusions; each names the expected skill and a
  `trap` skill that lexical matching tends to pick.
- 12 hard negatives: prompts containing another skill's trigger words while the
  intended skill is different.

Every case has `primary`, `want` and optionally `trap`; `want` may hold more
than one acceptable skill. `matrix.py --check` fails when a skill has fewer
than 3 positives, ids/prompts repeat, or a referenced skill does not exist.

## Baseline (2026-10-26, first run)

- Overall top-1: 64/87 (73.6%); top-3: 78/87 (89.7%)
- Positives: 44/57 top-1, 52/57 top-3
- Negatives: 13/18 top-1; hard negatives: 7/12 top-1
- `dv-build` false positives: 0
- Weakest positives: `dv-author`, `dv-build`, `dv-research`, `dv-route`,
  `dv-done` (1/3 each)
- Most frequent confusions: `dv-author -> dv-context/dv-help`,
  `dv-research -> dv-help`, `dv-build -> dv-plan/dv-context`,
  `dv-done -> dv-grill/dv-browser`

## Host confirmation baseline (2026-10-26)

Run `results/host-20261026T080219Z-natural` (untracked). Host Claude Code
2.1.267, model `deepseek-v4.1-flash-1017`, plan mode, 31 cases (19 first
positives + 12 hard negatives), 4 workers, stopped 5s after the first Skill
call.

- Any-hit: 10/31; positives: 7/19; hard negatives: 3/12; trap leaks: 0
- 19 cases invoked no skill; 3 invoked an external skill (`skill-creator`,
  `orca-cli`); 2 invoked the wrong devkit skill (`dv-research` for
  `dv-browser`/`dv-build`)
- Positives hit: `dv-arch`, `dv-commit`, `dv-context`, `dv-help`, `dv-plan`,
  `dv-route`, `dv-upgrade`
- Positives missed: `dv-audit`, `dv-author`, `dv-browser`, `dv-build`,
  `dv-debug`, `dv-design`, `dv-done`, `dv-grill`, `dv-push`, `dv-research`,
  `dv-review`, `dv-test`
- Explicit controls: `dv-audit` and `dv-author` invoked 2/2 in about 8s each,
  so natural misses are routing choices, not missing or broken skills
- On the same 31 cases, lexical top-1 was 22/31 while host any-hit was 10/31;
  agreement was 8/31. The lexical matrix is a coverage pre-filter, not a proxy
  for host behavior.

## Model rerun (2026-10-26, claude-opus-5-5 and claude-fable-5)

After the user switched session models, both layers were rerun. The lexical
matrix is model-independent and reproduced exactly (64/87 top-1, 78/87 top-3).

Claude Code arm, `--model 'claude[1M]'` resolving to `claude-opus-5-5`
(run `results/host-20261026T092633Z-fable-natural`, untracked):

- Any-hit: 14/31; positives: 11/19; hard negatives: 3/12; trap leaks: 0
- Versus the deepseek baseline (10/31): newly hit `dv-audit`, `dv-design`,
  `dv-done`, `dv-grill`, `dv-review`, `dv-test`; newly missed `dv-commit`,
  `dv-help` (both answered directly without tools in plan mode)
- `P-author-1` was again taken by the external `skill-creator`
- Per-case latency 7-40s, much faster than deepseek (9-150s)

Qoder CLI CN arm (`--host qoder -m claude-fable-5`, the user's actual host,
run `results/host-20261026T094953Z-qoder-fable-natural`, untracked):

- 17/31 prompts were deterministically refused by the channel content filter
  ("This conversation contains sensitive content"), including plain requests
  like "把当前分支推上去"; retries confirmed the refusals are stable. These
  cases measure the channel, not the skills, and are excluded from scoring.
- Scorable 14 cases: positives 8/10 (missed `P-author-1` to `skill-creator`,
  `P-build-1` no call), hard negatives correct-invoke 2/4, trap leaks 0
- Notably `dv-browser`, `dv-commit`, `dv-debug`, `dv-test`, `dv-push` hit here
  but not on the Claude Code arm: routing outcomes are host+model specific

Use `--host qoder` only with serial workers; parallel runs raise the refusal
rate further.

Open issue: `dv-author` loses to the external `skill-creator` on both hosts.
That is skill competition, not a description miss; fix it before widening the
matrix.

## Limits

- TF-IDF with Chinese character bigrams is shallow; a miss here is a hypothesis,
  not proof that a host model would miss. Do not rewrite descriptions from this
  result alone.
- The dataset is synthetic and small per skill (3 positives), so per-skill
  percentages are coarse.
- This matrix does not test skill execution, authorization boundaries or
  evidence quality.
- Host confirmation is a point-in-time run; rerun after description changes
  with the host version, model and invocation logs recorded.
- No-skill cases measure invocation, not task quality. A direct answer can be
  useful while still being a routing miss.
- The host arm uses the local Claude Code configuration. User-level skills and
  plugins are not isolated, so an external skill can win a prompt (for example
  `skill-creator` competing with `dv-author`). Those calls are recorded as
  external skills, not counted as devkit hits.
- The model is whatever the host configuration selects, not necessarily a
  Claude model; record it with the run and do not generalize across hosts.
- The host arm is read-only and runs in plan mode. It can observe invocation
  but cannot exercise action skills (`dv-commit`, `dv-push`, `dv-upgrade`,
  `dv-browser`) end to end. A refusal caused by missing tools is a harness
  bias, not proof that the description is wrong.
