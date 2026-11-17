# Repeated-trial agent evaluation

Behavioral engineering evaluation with real LLM calls and live public sources. Inputs are synthetic; no fixed priority or model wording is prescribed.

Model: `openai/gpt-oss-20b`. Runtime fingerprint: `9ca08566edaf54da8b6187d83b4c0e7c5b6699ada4d652556e2612c0527caa8c`.
Planned trials: 2; attempted: 2; all behavioral checks passed: 0.

| Case / trial | Agent status | Checks passed | LLM calls | Tokens | Seconds |
| --- | --- | --- | --- | --- | --- |
| unsupported_vendor / 1 | failed | 3/7 | 10 | 30026 | 286.83 |
| unsupported_vendor / 2 | failed | 3/7 | 9 | 19669 | 232.03 |

## Interpretation

These are source/trace/schema checks on self-authored synthetic goals with actual LLM and live source calls. The same configured runtime is used for repeated trials; live sources may change. Failed attempts and skipped trials remain visible.
Reference validity and source-value preservation do not measure semantic claim accuracy. Manual claim-support review is not yet a labeled metric. No classifier precision/recall, confidence calibration or production success rate is claimed.

Stop reason: Daily provider quota exhausted; no remaining trials were represented as completed.

## Per-trial checks

### unsupported_vendor / 1

- FAIL: accepted_analysis
- PASS: plan_before_tools
- PASS: required_tools_selected
- FAIL: scope_covered
- FAIL: valid_scoped_evidence_refs
- FAIL: source_review_accepted
- PASS: unsupported_or_missing_assets_unverified

### unsupported_vendor / 2

- FAIL: accepted_analysis
- PASS: plan_before_tools
- PASS: required_tools_selected
- FAIL: scope_covered
- FAIL: valid_scoped_evidence_refs
- FAIL: source_review_accepted
- PASS: unsupported_or_missing_assets_unverified
