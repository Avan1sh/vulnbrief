# VulnBrief v0.2 engineering evaluation

Selected runs use real LLM calls and public live sources. Inventory and unavailable-CVE inputs are fictional; the timeout is deliberately injected. No static response mode is used.

| Run | Status | Model | Tools / failures | LLM calls | Tokens | Seconds |
| --- | --- | --- | --- | --- | --- | --- |
| v02-reviewed | complete | openai/gpt-oss-20b | 6 / 0 | 11 | 41636 | 401.88 |
| v02-recovery-final | complete | openai/gpt-oss-20b | 5 / 1 | 9 | 27500 | 271.12 |
| v02-partial-final | partial | openai/gpt-oss-20b | 4 / 2 | 8 | 14304 | 182.22 |

## Scope of verification

- The normal run exercises six tools, asset version statuses and field-cited conditional actions.
- The recovery run exposes an ERR failure and subsequent model-selected recovery. Successful evidence retains separate E IDs.
- The partial run preserves absent record/score information as unknown.
- Unit/API tests cover evidence paths, concrete version citations, version boundaries, queueing, persistent review state and comparisons. See tests/test-results.txt.
- Local API review write/read/restore and snapshot comparison were checked against real generated task drafts. No external action was performed.
- Browser visual verification was blocked by Computer Use active-URL confidence enforcement. Frontend syntax and ID references were checked; no completed browser visual test is claimed.
- Structural checks and model review do not prove semantic accuracy, full asset applicability or production readiness. No classifier precision/recall is claimed.

## Retained attempts

Baselines and failed development attempts are retained with their actual outcomes. Failures include protocol/schema errors, minute/day quota limits and rejected reports. The selected small set is not an unbiased success-rate sample.

- final-normal: complete / schema 0.1
- final-partial: partial / schema 0.1
- final-recovery: partial / schema 0.1
- run-normal: failed / schema 0.1
- run-normal-final: complete / schema 0.1
- run-normal-v2: complete / schema 0.1
- run-recovery: complete / schema 0.1
- run-recovery-final: complete / schema 0.1
- v02-final: complete / schema 0.2
- v02-integrated: failed / schema 0.2
- v02-partial-final: partial / schema 0.2 / selected
- v02-pilot: failed / schema 0.2
- v02-recovery: failed / schema 0.2
- v02-recovery-final: complete / schema 0.2 / selected
- v02-reviewed: complete / schema 0.2 / selected
- v02-verified: failed / schema 0.2
- v02-workbench: failed / schema 0.2
- validated-normal: failed / schema 0.1