# VulnBrief investigation

Status: **failed**

Goal: Investigate CVE-2024-3400 using live CVE, KEV, EPSS and supported vendor guidance. Recover from failed requests, distinguish ERR errors from successful E evidence, and produce two conditional actions with exact supporting source fields. Use the exact version_citations for any named version. No asset inventory was supplied.

Run: `v02-recovery` | Model: `openai/gpt-oss-20b`

## Plan


## Execution limit or failure

LLM provider returned HTTP 400 (tool_use_failed); check account, model and quota

## Source observations

These facts are attached by the runtime from tool results, not rewritten by the LLM.

## Execution summary

```json
{
  "llm_calls": 2,
  "total_tokens": 0,
  "tool_calls": 0,
  "tool_failures": 0,
  "elapsed_seconds": 25.72,
  "fault_injected": false
}
```

A watchlist association does not prove asset applicability. Missing evidence is unknown, not safe.
