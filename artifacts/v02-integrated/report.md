# VulnBrief investigation

Status: **failed**

Goal: Investigate CVE-2024-3400 for the selected inventory. Retrieve the CVE record first, then current vendor advisory, KEV and EPSS. Assess the inventory versions. Produce actions with valid field paths directly inside evidence.data (no /data prefix), explicit applicability prerequisites, and distinguish ERR failures from E evidence.

Run: `v02-integrated` | Model: `openai/gpt-oss-20b`

## Plan


## Execution limit or failure

LLM provider returned HTTP 400; check account, model and quota

## Source observations

These facts are attached by the runtime from tool results, not rewritten by the LLM.

## Execution summary

```json
{
  "llm_calls": 1,
  "total_tokens": 0,
  "tool_calls": 0,
  "tool_failures": 0,
  "elapsed_seconds": 2.02,
  "fault_injected": false
}
```

A watchlist association does not prove asset applicability. Missing evidence is unknown, not safe.
