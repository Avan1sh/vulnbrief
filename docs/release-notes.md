# VulnBrief 0.3.0

VulnBrief is a bounded LLM agent for vulnerability investigation and asset-aware
triage. It plans from a natural-language goal, chooses live tools, observes their
results, and produces an evidence-linked report with explicit uncertainty.

## Included

- A reviewer landing page and six-step tour of explicitly dated recorded real
  investigations, with no new LLM requests during playback.
- An accessible exact-field evidence inspector, unknown-aware KEV summaries,
  filtered history and responsive desktop/tablet/phone layouts.
- Genuine screenshots and a silent 90-second WebM walkthrough. The large video
  is a separate release asset to keep the source ZIP below 10 MB.
- Live CVE, CISA KEV, FIRST EPSS and supported vendor advisory tools.
- A narrow PAN-OS version pilot with affected, version-unaffected and unverified
  outcomes based on retrieved vendor tables.
- Exact source-field citations, conditional action prerequisites, separate error
  observations, and bounded report repair.
- A localhost analyst dashboard with task review/export, saved investigations,
  and source/asset comparisons.
- Source code, setup instructions, architecture image, a one-page design write-up,
  tests, and genuine demonstration traces, including retained failed attempts.
- A repeatable live evaluation harness with eight defined cases, two-trial
  batches, runtime fingerprints and explicit behavioral checks.

## Run locally

Use Python 3.10+ and follow the
[README](https://github.com/Avan1sh/vulnbrief#quick-start). A Groq API key is needed
for live investigations. Quotas and free access are provider/account dependent;
GPT-OSS 20B is available as a smaller alternative to the default 120B model.

After installing and configuring `.env`, run `python -m vulnbrief serve --port
8787` and open `http://127.0.0.1:8787`. Unit/API tests do not require a key.

## Validation

- **57 Python/API tests, eight presentation tests and nine browser tests passed**
  locally. The browser suite also passed against the separately installed wheel.
- Separate wheel installation and dependency checks passed.
- Three selected real upgraded runs: complete asset investigation, complete
  injected-timeout recovery, and partial missing-data investigation.
- Isolated Chromium checks passed at desktop, tablet and phone widths, including
  automated accessibility scans and keyboard/modal behavior. Real screenshots,
  video frames and the one-page PDF were visually inspected. This is not full
  accessibility certification or coverage of every browser engine.
- GitHub CI results are reported by the repository workflow, separately from
  recorded local checks.

See [sample evidence](https://github.com/Avan1sh/vulnbrief/blob/main/artifacts/sample-runs.md),
[engineering evaluation](https://github.com/Avan1sh/vulnbrief/blob/main/artifacts/evaluation-summary.md),
and [source-support limits](https://github.com/Avan1sh/vulnbrief/blob/main/docs/source-review.md).

## What the broader evaluation found

The original six-trial batch includes four real LLM/live-source investigations
and two scope guards with zero LLM calls. Missing-data handling and scope guards
passed their applicable checks. Unsupported-vendor trials exposed skipped
inventory, a schema failure and an unsupported upgrade inference.

Those findings prompted a bounded plan correction, stricter inventory completeness
and named upgrade-target validation. Both follow-up trials read and assessed the
inventory; one then failed citation validation and the other exhausted the free
provider's daily quota. Neither is presented as a completed successful report.
The two runtimes and budgets are recorded separately. Read
[the full findings](https://github.com/Avan1sh/vulnbrief/blob/main/docs/evaluation-findings-v03.md).

Free API quota may be unavailable after repeated evaluations. Recorded examples
remain usable without a key or new LLM calls. No aggregate production reliability
or classifier precision/recall claim is made.

## Boundaries

This is an assessment prototype for a small CVE watchlist. It does not scan or
patch systems, establish complete applicability, create external tickets, or
provide enterprise access controls. Recommendations require analyst review.
Version support is limited to explicitly parsed PAN-OS table branches. Source
coverage, LLM judgments and public API availability can be incomplete. Three
selected runs do not establish production reliability or classifier precision/recall.

Implementation was developed with AI coding assistance. No public agent repository
implementation was copied.
