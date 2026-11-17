# Changelog

## 0.3.0 - 2026-11-17

### Added

- Dated recorded-run cards and an accessible six-step reviewer tour that starts no
  LLM calls; new live investigations remain explicitly separate.
- A read-only exact-field citation inspector with source dates, original values,
  linked report claims, keyboard focus return and visible null observations.
- Filterable history, selected-run task views, observed execution phases and
  desktop/tablet/phone refinements.
- Eight presentation regressions and nine Playwright/axe browser checks, with a
  dedicated browser CI job and genuine screenshots/video.
- An eight-case live evaluation harness with bounded repeated trials, actual
  source/model calls, runtime fingerprints and unedited failed outcomes.

### Fixed

- Missing or conflicting KEV evidence shows Unknown instead of a zero count.
- Windows serves JavaScript modules with the required MIME type; table headings
  meet the automated contrast checks on the tested pages.
- Initial plan-schema failures receive one bounded correction. A selected but
  unread/unassessed inventory prevents complete report status.
- Common named upgrade/install targets require exact current vendor candidate
  citations rather than inference from an affected-version description.

### Verification and limits

57 Python/API tests, eight presentation tests and nine Chromium browser checks
passed locally. Real UI screenshots and video frames were inspected. Repeated
live trials exposed model/tool-use and citation failures; see
[the findings](docs/evaluation-findings-v03.md). Automated accessibility checks,
structural validation and LLM review do not prove full accessibility, semantic
accuracy or production readiness. The source ZIP excludes the large video, which
is distributed as a separate release asset.

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
