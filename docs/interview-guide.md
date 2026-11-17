# Explaining VulnBrief

## v0.2 additions to demonstrate

Open the local workbench with `python -m vulnbrief serve`. Load the fictional CSV and show its three version outcomes. Open a recommendation's exact source field and distinguish source-assigned CVSS from the model's priority. Explain why version arithmetic is an execution tool, while investigation order and advice come from the LLM. Show local task review/export, then compare saved observations. Clarify that draft acceptance executes no system change, and edit-and-rerun starts a fresh investigation rather than resuming an LLM checkpoint.

The new ERR identifiers prevent request failures from being confused with successful E evidence. Source-field existence and concrete version matching are deterministic checks, while model review remains fallible. The vendor pilot supports PAN-OS only. Browser visual verification was blocked by Computer Use's active-URL check; do not claim that visual test was completed.

## 60-second introduction

I built a bounded vulnerability investigation agent. It receives a natural-language goal and optionally a small watchlist with operational context. An LLM creates a plan, selects live tools, reads their results, and decides what to do next. The tools retrieve CVE records, CISA's known-exploited catalog, and FIRST EPSS scores. The model recommends an investigation order with evidence references and explicit uncertainty. The runtime validates inputs and references, limits execution, and saves a readable trace. In the recovery demonstration, a deliberately injected timeout is returned to the model, which selects another action rather than receiving an automatic replacement answer.

Use this explanation only after personally reading the implementation and running the examples.

## What makes this an agent?

The model selects the next function and its parameters from the available tool registry after seeing observations. Source order and recovery choices are not encoded as a fixed domain workflow. LangGraph supplies the control structure: plan, decide, execute, observe, and report. Input schemas, scope checks and resource limits are deterministic engineering controls. The model still controls investigative decisions and priorities.

## A few distinctions to know

- **CVE:** an identifier and published record for a vulnerability; presence in a watchlist does not prove an asset is affected.
- **CVSS:** a severity metric, with a version and assigning source. This project preserves CNA-supplied metrics rather than generating a number.
- **KEV:** evidence that CISA has included a vulnerability in its known exploited catalog. Absence does not establish safety.
- **EPSS:** a general estimate of exploitation in the next 30 days, not a particular organization's probability of compromise.
- **Retrieval time:** when our tool fetched data. This differs from the source's publication/update/score date.
- **Mirror:** an alternative copy of an underlying dataset; it is not another independent confirmation.

## Trace walkthrough

1. Open a sample run's transcript and locate `plan` before the first `tool_start`.
2. Locate `decision` events: these preserve the native function names and arguments selected by the model.
3. Match a `tool_result` to its `call_id`, evidence ID, URL and timestamps.
4. In the recovery run, identify the injected timeout and the subsequent LLM decision. Explain which observed action constitutes recovery.
5. Open the final report and match finding evidence IDs to original normalized observations.
6. Explain why the model's citations establish inspectability but not automatic proof that every natural-language conclusion is true.

## Tradeoffs you should be able to defend

- One agent reduces orchestration/debugging work for a small investigation; additional personas would not guarantee better evidence.
- Live structured public data is easier to validate than broad web scraping and needs no paid search service.
- JSON schemas make contracts explicit; they do not eliminate hallucination.
- Tool errors return to the model so it can adapt. Provider outages and invalid final reports can still terminate a run.
- Compact source data controls quota usage but omits some version trees and additional-data-provider content.
- A CLI is reproducible and leaves inspectable artifacts. It fits the assessment better than spending the initial budget on a large frontend.
- Mocked tests verify runtime behavior, while live demonstrations verify actual model/source integration. Neither a small suite nor three demos proves production reliability.

## Honest next steps

Extend asset/version support beyond the PAN-OS pilot, strengthen semantic claim verification, add explicit freshness/conflict policies, run broader independent evaluations, and explore resumable checkpoints. The current workbench already supports local analyst review; enterprise identity, privacy and shared deployment need separate work. Explain the use of AI assistance honestly; be prepared to change a tool/schema or add a test during an interview.
