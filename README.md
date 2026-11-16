# Cardinal calendar audit — Hermes skill tap

A read-only, local calendar audit for conflicts, busy time, and free focus windows.
The included example is fictional. No Google account, API key, network request, or
third-party Python dependency is needed. Python 3.11+ with IANA timezone data is required.

## Install in Hermes

```bash
hermes skills tap add PragyaDhawan/cardinal-hermes-skills
hermes skills install PragyaDhawan/cardinal-hermes-skills/cardinal-calendar-audit
hermes skills list
```

The installed skill is available as `/cardinal-calendar-audit`. Ask Hermes to run its
bundled fictional example and explain the conflict and free windows. Enable the
`skills` and `terminal` toolsets in the isolated profile used for that demonstration.
For real private input, use local inference and an appropriately restricted terminal.
This skill does not supply a sandbox or configure model routing.

## Reproduce the deterministic example

```bash
python3 skills/cardinal-calendar-audit/scripts/review_day.py \
  skills/cardinal-calendar-audit/examples/synthetic_day.json
python3 -m unittest discover -s tests -v
```

Expected: one overlap, 150 busy minutes, 330 free minutes, and three focus windows.
The script handles timezone conversion, work-window clipping, exclusive all-day end
dates, cancellation, transparency, nested overlaps, and adjacent meetings. It rejects
naive timestamps, duplicate IDs, invalid intervals, and oversized inputs. It does not
expand recurrence, query a live account, modify events, or send notifications.

## Attribution and version

Version 1.0.0. Created for CSCI 599 by Pragya Dhawan with Codex assistance; the initial
skill instructions, Python implementation, tests, and documentation were AI-assisted.
Hermes is a separate MIT-licensed project by Nous Research, not bundled here.
The tap layout follows the [official Hermes skills documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/#publishing-a-custom-skill-tap).
The repository contains only this portable skill, fictional data, and its tests.
No coursework credentials or private runtime state are included.
