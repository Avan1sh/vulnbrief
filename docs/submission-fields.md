# Submission field guide

Review these against the actual form before submitting. This guide does not submit anything.

**Role:** Agentic AI Engineer Intern.

**Domain/goal:** Autonomous vulnerability investigation and asset-aware triage. The agent combines live CVE, CISA KEV, FIRST EPSS and supported vendor advisory data with optional JSON/CSV inventory. It produces version-based assessments, conditional field-cited actions and reviewable task drafts, with a local workbench and saved run comparisons. The supported version pilot is PAN-OS; uncertain cases remain unverified.

**Assumptions/mock data:** The included environment/watchlist is synthetic and is not a real scan finding. Public vulnerability data is retrieved live during each run. One recovery scenario deliberately injects a single primary-source timeout; subsequent retrievals are real. Unit tests use synthetic HTTP responses and a scripted model double; those tests are not represented as live model performance.

**Architecture upload:** `docs/architecture.png`.

**Sample transcripts/logs:** `artifacts/sample-runs.md` combines the selected actual runs. Individual raw events, transcripts and reports are retained in the corresponding artifact directories. v0.3 adds repeated trials in `artifacts/evaluation-v03/` and separately recorded post-fix trials in `artifacts/evaluation-v03-followup/`; failures are disclosed in `docs/evaluation-findings-v03.md`.

**Design write-up:** `docs/design-writeup.pdf` (one page), with matching text source.

**Source:** GitHub repository: https://github.com/Avan1sh/vulnbrief. Use the public repository link in the code-link field once publication is verified. The release source ZIP provides the same source, documentation, tests and demonstration evidence without credentials or local runtime state.

**Synthetic/test traces and labels:** `examples/scenarios.json` and `examples/evaluation-suite.json` describe self-authored goals, synthetic context, faults and expected observable behavior. Actual execution events are under `artifacts/`. Eight evaluation cases are defined; only executed trials count. Labels concern engineering behavior, not a trained detector's malicious/benign ground truth.

**Monitoring report:** If optional for this Engineer track, leave it empty. If a response is required, attach `artifacts/evaluation-summary.md` as engineering telemetry and explain that a separate monitoring/detection agent was not the assigned project.

**Approach/precision/recall/production-readiness:** This is an investigation/reporting agent, not a classifier with a labeled detection target. Precision/recall is not defined for this implementation. Report only the actual structural tests, live-run outcomes and limits in the evaluation summary. It is an assessment prototype, not production-certified.

**Total time spent:** Enter actual personal time. Do not use the planning estimate or automated process wall time as your hours.

**Personal details:** Enter and verify your own full name, email and phone number.

**Authorship:** The implementation was developed with AI coding assistance. Review and understand it, and follow the employer's disclosure requirements. No public agent repository implementation was copied.
