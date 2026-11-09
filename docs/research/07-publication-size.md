# Publication size incident — 2026-11-08

[Run 42522875765](https://github.com/0xRadikal/Free-Telegram-Proxy/actions/runs/42522875765)
collected 5,587 links, verified 2,637, and passed `validate_outputs.py`.
Publication stopped because 4,197,053 B exceeded the project's 4,194,304 B
aggregate budget by 2,749 B. This was not a GitHub upload limit or a probe
failure. Later runs succeeded as the set of live proxies fluctuated.

The original budgets were calibrated on about 1.6 MiB. At main commit
`03c4e9ee54c4b9670c06acc5dc44e042d8d374c4` (2026-11-09), published outputs
occupied 4,140,254 B. The largest files were:

| File | Bytes |
|---|---:|
| state.json | 972,860 |
| verified/proxies.json | 721,635 |
| all/tg.txt | 564,838 |
| verified/tme.txt | 308,323 |
| verified/tg.txt | 287,539 |

Between the published Nov 1 and Nov 9 snapshots, collected links grew from
3,408 to 5,257 and retained proxy histories from 4,122 to 5,402. Histories
remained at most 96 observations and no entries exceeded the existing
seven-day last-seen retention window. The checked state entries contained
only the expected fields. This is measured data growth, not evidence that
the history cap failed.

## Policy and diagnostics

The guard now allows **8 MiB total / 2 MiB per file**, approximately twice
the observed footprint. It warns at **80%** of either budget, still refuses
larger outputs, and reports exact totals and the largest files in the log
and job summary. `--report` writes per-file JSON diagnostics; the publication
workflow retains them as an artifact on a size failure. Review that report
before changing budgets again. Limits are not automatically enlarged.

This preserves complete verified lists, all output formats and cross-run
history. No output is truncated to make a check pass. The structural and
minimum-proxy validators still run before publishing.

CI now seeds the end-to-end run with the checked-out `state.json`, so the
size check includes retained history and eligible stable proxies. Its
summary also runs the Python heredoc on Python, not `tee`; the old command
returned success while displaying Python source instead of results.

## Reproduction and validation

Before the fix, five files of `[839410, 839410, 839410, 839410, 839413]` bytes
reproduce the same aggregate failure without any network or testing library.
Both filesystem stat and `wc -c` total 4,197,053 B. Executing the original
Summary step in Bash likewise reproduces the unexecuted Python text.

`tests/test_check_size.py` checks the observed size, exact boundaries, hard
failures, early warnings, invalid limits, missing/empty output directories,
hidden parent directories, and diagnostics on failure. The original walker
also incorrectly skipped *all* files when an absolute path contained a
hidden ancestor. `tests/test_workflow_summary.py` executes the actual YAML
step in Bash with present and absent pipeline outputs.

Run `python -m pytest -q -rs` and the live `CI` workflow. Run a normal
`Update proxies` on main after merge and verify its publish and freshness
checks. Network availability remains an external dependency; a successful
run is evidence for that run, not a guarantee about future upstream services.
