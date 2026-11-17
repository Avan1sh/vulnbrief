# Repeated-trial agent evaluation

Behavioral engineering evaluation with real LLM calls and live public sources. Inputs are synthetic; no fixed priority or model wording is prescribed.

Model: `openai/gpt-oss-20b`. Runtime fingerprint: `d9f329f874e8b39042d2ab979e0e5ed4dda07d94ccc20f0211be2bd70ece3e2f`.
Planned trials: 6; attempted: 6; all behavioral checks passed: 4.

| Case / trial | Agent status | Checks passed | LLM calls | Tokens | Seconds |
| --- | --- | --- | --- | --- | --- |
| missing_record / 1 | partial | 8/8 | 8 | 14172 | 182.08 |
| missing_record / 2 | partial | 8/8 | 8 | 14629 | 181.89 |
| unsupported_vendor / 1 | complete | 5/7 | 8 | 19974 | 207.98 |
| unsupported_vendor / 2 | failed | 0/7 | 1 | 690 | 1.92 |
| scope_guard / 1 | input_rejected | 1/1 | 0 | 0 | 0.0 |
| scope_guard / 2 | input_rejected | 1/1 | 0 | 0 | 0.0 |

## Interpretation

These are source/trace/schema checks on self-authored synthetic goals with actual LLM and live source calls. The same configured runtime is used for repeated trials; live sources may change. Failed attempts and skipped trials remain visible.
Reference validity and source-value preservation do not measure semantic claim accuracy. Manual claim-support review is not yet a labeled metric. No classifier precision/recall, confidence calibration or production success rate is claimed.

Stop reason: Planned batch completed.

## Per-trial checks

### missing_record / 1

- PASS: accepted_analysis
- PASS: plan_before_tools
- PASS: required_tools_selected
- PASS: scope_covered
- PASS: valid_scoped_evidence_refs
- PASS: source_review_accepted
- PASS: expected_status
- PASS: source_missing_epss_preserved

### missing_record / 2

- PASS: accepted_analysis
- PASS: plan_before_tools
- PASS: required_tools_selected
- PASS: scope_covered
- PASS: valid_scoped_evidence_refs
- PASS: source_review_accepted
- PASS: expected_status
- PASS: source_missing_epss_preserved

### unsupported_vendor / 1

- PASS: accepted_analysis
- PASS: plan_before_tools
- FAIL: required_tools_selected
- PASS: scope_covered
- PASS: valid_scoped_evidence_refs
- PASS: source_review_accepted
- FAIL: unsupported_or_missing_assets_unverified

### unsupported_vendor / 2

- FAIL: accepted_analysis
- FAIL: plan_before_tools
- FAIL: required_tools_selected
- FAIL: scope_covered
- FAIL: valid_scoped_evidence_refs
- FAIL: source_review_accepted
- FAIL: unsupported_or_missing_assets_unverified

### scope_guard / 1

- PASS: scope_rejected_before_model

### scope_guard / 2

- PASS: scope_rejected_before_model
