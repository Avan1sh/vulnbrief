# VulnBrief 0.2.0

VulnBrief is a bounded LLM agent for vulnerability investigation and asset-aware
triage. It plans from a natural-language goal, chooses live tools, observes their
results, and produces an evidence-linked report with explicit uncertainty.

## Included

- Live CVE, CISA KEV, FIRST EPSS and supported vendor advisory tools.
- A narrow PAN-OS version pilot with affected, version-unaffected and unverified
  outcomes based on retrieved vendor tables.
- Exact source-field citations, conditional action prerequisites, separate error
  observations, and bounded report repair.
- A localhost analyst dashboard with task review/export, saved investigations,
  and source/asset comparisons.
- Source code, setup instructions, architecture image, a one-page design write-up,
  tests, and genuine demonstration traces, including retained failed attempts.

## Run locally

Use Python 3.10+ and follow the
[README](https://github.com/Avan1sh/vulnbrief#quick-start). A Groq API key is needed
for live investigations. Quotas and free access are provider/account dependent;
GPT-OSS 20B is available as a smaller alternative to the default 120B model.

After installing and configuring `.env`, run `python -m vulnbrief serve --port
8787` and open `http://127.0.0.1:8787`. Unit/API tests do not require a key.

## Validation

- Retained local result: **46 tests passed**.
- Separate wheel installation and dependency checks passed.
- Three selected real upgraded runs: complete asset investigation, complete
  injected-timeout recovery, and partial missing-data investigation.
- Public API/static frontend checks passed. Browser visual verification was not
  completed because the automation could not establish the active URL confidently.
- GitHub CI results are reported by the repository workflow, separately from
  recorded local checks.

See [sample evidence](https://github.com/Avan1sh/vulnbrief/blob/main/artifacts/sample-runs.md),
[engineering evaluation](https://github.com/Avan1sh/vulnbrief/blob/main/artifacts/evaluation-summary.md),
and [source-support limits](https://github.com/Avan1sh/vulnbrief/blob/main/docs/source-review.md).

## Boundaries

This is an assessment prototype for a small CVE watchlist. It does not scan or
patch systems, establish complete applicability, create external tickets, or
provide enterprise access controls. Recommendations require analyst review.
Version support is limited to explicitly parsed PAN-OS table branches. Source
coverage, LLM judgments and public API availability can be incomplete. Three
selected runs do not establish production reliability or classifier precision/recall.

Implementation was developed with AI coding assistance. No public agent repository
implementation was copied.
