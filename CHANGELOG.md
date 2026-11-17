# Changelog

## 0.2.0 — 2026-11-17

### Added

- Exact evidence-field references for conditional recommendations and summaries;
  separate request-error identifiers and concrete version citation checks.
- CSV/JSON asset inventory, source-driven PAN-OS version assessment, and current
  official Palo Alto advisory retrieval.
- A localhost analyst workbench with queued investigations, source inspection,
  execution events, and artifact downloads.
- Reviewable remediation task drafts with owner/status/notes and CSV export.
- SQLite investigation history, interrupted-run labeling, edit-and-rerun inputs,
  and saved-source/asset comparisons.
- Unit/API regression coverage, real upgraded demonstrations, architecture and
  design documentation, source packaging, and repository CI.

### Changed

- Bounded provider retries distinguish daily quota exhaustion from temporary rate
  limits and protocol/schema failures.
- GPT-OSS 20B provides a smaller alternative using JSON mode with the same local
  Pydantic validation; GPT-OSS 120B remains the default.
- Report generation uses original observations and a separate grounding review;
  unvalidated prose at the decision boundary is discarded.

### Verification and limits

The retained local suite records 46 passing tests. Three selected real upgraded
runs cover normal investigation, injected timeout recovery, and missing data.
They are engineering demonstrations, not a production reliability benchmark.
Browser visual verification remains incomplete. See
[evaluation](artifacts/evaluation-summary.md) and
[source review](docs/source-review.md).

## 0.1 — retained development baseline

Initial bounded LangGraph investigation loop with live CVE, CISA KEV and FIRST
EPSS tools, JSON/Markdown reporting, public execution traces, and explicit fault
injection. Baseline and unsuccessful development runs remain in `artifacts/` for
review; their outputs were not retroactively rewritten to the 0.2 schema.
