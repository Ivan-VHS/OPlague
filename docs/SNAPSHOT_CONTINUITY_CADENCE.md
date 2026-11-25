# OPlague — Snapshot Continuity and Cadence

## New read-only capability

`tools.snapshot_history` adds longitudinal analysis for saved OPlague inventory snapshots. It validates every snapshot against the existing v1 schema, derived counters and canonical SHA-256 digest before comparing its metrics.

The report covers three dimensions:

- **Quality:** only structurally valid, digest-consistent snapshots enter the analysis.
- **Cohesion:** metric names and dimensions must remain consistent across the history; missing/extra dimensions are rejected rather than silently aligned.
- **Cadence:** capture intervals are measured for spread, mean-period bias and first-half/second-half drift. The expected period defaults to the observed median.

Per-metric output includes mean, sample deviation, range, first-to-last change and a bounded descriptive stability score.

## CLI

Provide at least three snapshot files in chronological order:

```bash
python -m tools.snapshot_history --snapshot baseline.json --snapshot followup-1.json --snapshot followup-2.json --expected-interval-seconds 3600 --output history-report.json
```

Omit `--expected-interval-seconds` to use the observed median interval.

## Safety and interpretation

The tool reads saved JSON only. It does not query devices, install or change drivers, modify snapshots, rank driver packages or produce compatibility/safety verdicts. A stable metric indicates only that the declared normalized value remained similar across the supplied captures.

## Verification

Run `python -m unittest tests.test_snapshot_history -v`. Coverage includes stable histories, changing device metrics, chronology errors, tampered fingerprints and input bounds.
