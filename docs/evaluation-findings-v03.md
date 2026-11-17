# What the repeated evaluation found

The suite defines eight self-authored scenarios. The first executed batch selected
three scenarios and two trials each: four real LLM/live-source investigations and
two input-scope checks that correctly made zero LLM calls. This is a small,
selected engineering experiment, not an unbiased reliability estimate.

## Original batch

See [the complete six-trial report](../artifacts/evaluation-v03/summary.md).

- Both missing-record trials returned partial reports and passed all eight
  applicable structural/behavioral checks.
- Both scope-limit trials rejected four CVEs before a model request.
- Unsupported-vendor trial 1 returned a structurally accepted report, but skipped
  the supplied inventory and did not generate an asset assessment. It passed five
  of seven predefined checks. A manual spot check also found that it inferred an
  upgrade target from affected-version prose and described catalog guidance as a
  mandate. Reference existence and an accepted model review did not catch these
  semantic problems.
- Unsupported-vendor trial 2 failed at plan-schema validation. No tools executed.

Original model outputs, rejected drafts and raw events remain unchanged. There is
no fabricated semantic accuracy percentage or classifier precision/recall score.

## Changes prompted by the findings

The runtime now allows one bounded initial-plan schema correction. Instructions
clarify that selected inventory contents require a real file-tool call and that
unsupported vendor guidance can still yield an explicit unverified assessment.
A selected but unread/unassessed inventory prevents complete status.

An additional lexical check requires common named upgrade/install targets to cite
the exact vendor fixed-version candidate. An affected-version description cannot
supply that proof. It does not establish every natural-language interpretation,
all future version ranges, or complete real-device applicability.

## Follow-up

[Two follow-up trials](../artifacts/evaluation-v03-followup/summary.md) record the
changed runtime separately. They use a 600-second per-trial budget; the original
batch used 480 seconds. Runtime fingerprints and both budgets are disclosed, so
the two batches should not be treated as a controlled causal estimate.

Both follow-ups selected all six requested tools and produced unverified asset
assessments. The first report was rejected after one repair because an installed
version named in the action lacked its matching source-field citation. The second
reached the model's daily free-provider quota before report generation. Neither is
a successful completed investigation. The quota outcome is an operational failure,
not evidence that the model would pass or fail the report checks with more quota.
Consult the full follow-up report for every outcome; do not hide results or combine
guard checks with live model trials into a headline model success rate.

The next evaluation work should use more independent goals, manually labeled
claim support, additional source/product families, and repeated trials with a
fixed runtime and budget. The current findings already show why passing unit
tests, reference checks and a separate LLM review are insufficient evidence of
semantic reliability.
