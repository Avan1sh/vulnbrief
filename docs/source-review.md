# Source-support review and limits

v0.3 presentation note: reports retain schema 0.2 and their original model text.
The new inspector exposes exact cited values without rewriting those claims.
Current browser checks and repeated trials are recorded in `verification-v03.md`
and `artifacts/evaluation-v03/summary.md`; historical findings below remain dated
development observations.

Version note: the baseline findings below refer to retained v0.1 attempts. v0.2 adds separate ERR IDs, exact source-field action references, version-claim value matching, current vendor guidance and an independent arithmetic asset comparison. The latest upgraded runs are labeled in the evaluation summary. These controls improve inspectability but do not prove every natural-language inference.

This records the review method and development findings, not a claim that every sentence has been proven correct.

## Method

Upgrade spot check: `v02-reviewed` records the three fictional assets as potentially affected, version-unaffected and unverified, based on the current vendor table. Its concrete `11.0.4-h1` recommendation cites the matching `/fixed_version_candidates/1` value. An earlier neighboring-index citation is retained in the predecessor run; the added value-matching check rejects that case. All free-form recommendations still need human review.

- Match finding/summary evidence IDs to original observations in the same run.
- Compare vulnerability descriptions to retrieved CNA text, not model memory.
- Compare known-exploitation and ransomware claims to the retrieved KEV entries.
- Compare scores and dates to FIRST data. EPSS estimates general in-the-wild exploitation over the next 30 days, not imminent exploitation or an organization's breach probability.
- Check that missing data remains unknown and that version/context gaps are disclosed.
- Check recovery against an error followed by an LLM decision and a successful real retrieval.

The runtime attaches original normalized observations and validates evidence references. A separate model review checks natural-language judgments; human review remains necessary.

## Development findings

An initial run fetched all sources but failed because required tool choice rejected a text finish. Tool selection now permits a natural finish followed by structured reporting. Unsolicited draft prose at that boundary is discarded.

Early structurally valid reports overstated EPSS as imminent exploitation and included unsupported mitigation details. Report generation now receives fresh source observations instead of earlier assistant prose. A separate source-grounding LLM review can request one repair for unsupported claims, historical patch assumptions or unconditional remediation. A second rejection fails explicitly.

The first review-enabled normal attempt exposed reviewer fallibility: it incorrectly objected to the general 30-day interpretation of EPSS. The reviewer prompt now states the correct definition and distinguishes high estimated likelihood from certainty. The failed attempt is retained. Model review is an additional check, not a semantic guarantee.

## Manual spot check: final normal run

The PAN-OS command-injection/root-impact description and CVSS 3.1 score of 10.0 match E002. MOVEit's SQL-injection and database-impact description matches E003. Both KEV memberships and known ransomware fields match E004. Both numeric EPSS scores match E005, dated 2026-11-16. The missing product-version disclosures match the synthetic context, E001.

Residual language issue: the summary calls MOVEit "critical" even though its normalized CVE record supplies no CVSS metric. Treat this as the model's qualitative severity assessment, not a verified source-assigned score. The report itself discloses the absent metric. Action language also needs human review and confirmation of applicability. These limits remain despite an accepted model review; no exhaustive factual accuracy rate is claimed.

## Manual spot check: final recovery run

The raw events show an injected primary timeout followed by a model-selected official mirror request and a successful CVE record. The accepted partial analysis nevertheless mislabels E001 as the timeout in one limitation: E001 actually identifies the successful mirror record, while the timeout is a separate error event. Its wording about a future patch also reflects historical catalog guidance and does not establish present patch availability. These are retained output limitations, not silently edited model results. Consult the original observations and current vendor guidance; the automated reviewer did not catch every issue.

## Manual spot check: final missing-data run

Both CVE retrieval locations returned HTTP 404. The retrieved KEV catalog contained no matching entry, and FIRST returned no score. The report preserves unknown severity/remediation and does not replace the missing score with zero. Absence from those sources is not proof of safety or proof that no reserved/unpublished record could exist.

## Boundaries

Historical catalog actions do not establish whether a patch remains unreleased. Recommendations should verify applicability and consult current vendor guidance. Distinguish source severity, known exploitation, predictive probability and asset applicability. Final selected demonstrations and review outcomes are identified in the evaluation summary, which also inventories development attempts. Selected-run counts are not an unbiased reliability estimate.
