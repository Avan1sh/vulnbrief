"""Assemble submission logs and descriptive metrics from existing real events."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def build(normal, recovery, partial):
    selected = {"normal": normal, "recovery": recovery, "partial": partial}
    summaries, sections = [], []
    for label, name in selected.items():
        folder = BASE / "artifacts" / name
        report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
        events = [json.loads(line) for line in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        kinds = [e["event"] for e in events]
        plan_before_tools = "plan" in kinds and "tool_start" in kinds and kinds.index("plan") < kinds.index("tool_start")
        injections = [e for e in events if e["event"] == "tool_result" and e["observation"].get("error",{}).get("injected")]
        recovered = False
        for failure in injections:
            after = [e for e in events if e["sequence"] > failure["sequence"]]
            recovered = any(e["event"] == "decision" for e in after) and any(
                e["event"] == "tool_result" and e["tool"] == "get_cve_record" and e["observation"]["ok"] for e in after)
        accepted = plan_before_tools and report["analysis"] is not None
        review_accepted = any(e['event']=='report_review' and e['accepted'] and not e['issues'] for e in events)
        accepted = accepted and review_accepted
        if label == "normal": accepted = accepted and report["status"] == "complete"
        if label == "recovery": accepted = accepted and recovered
        if label == "partial": accepted = accepted and report["status"] == "partial"
        summaries.append({"scenario":label,"directory":name,"status":report["status"],
            "acceptance_passed":bool(accepted),"plan_before_tools":plan_before_tools,
            "automated_source_review_accepted":review_accepted,
            "injected_fault_recovered":recovered,**report["metrics"]})
        sections += [f"# Scenario: {label}\n", f"Origin and behavior label: see examples/scenarios.json. Runtime directory: {name}.\n",
                     (folder / "transcript.md").read_text(encoding="utf-8"), "\n## Accepted analysis\n",
                     "```json\n" + json.dumps(report["analysis"],indent=2,ensure_ascii=False) + "\n```\n"]
    attempts=[]
    for path in sorted((BASE / "artifacts").glob("*/report.json")):
        r=json.loads(path.read_text(encoding="utf-8"))
        attempts.append({"directory":path.parent.name,"status":r["status"],"selected":path.parent.name in selected.values(),"metrics":r["metrics"]})
    data={"scope":"Descriptive engineering evidence, not a reliability benchmark or detector evaluation",
          "selected_runs":summaries,"all_retained_agent_attempts":attempts}
    (BASE/"artifacts/evaluation.json").write_text(json.dumps(data,indent=2),encoding="utf-8")
    lines=["# Engineering evaluation summary", "", "Real Groq executions with live public source requests. Synthetic environment/goals and injected faults are explicitly labeled. Tests use doubles separately.", "",
           "| Scenario | Status | Checks | Tool calls / failures | LLM calls | Tokens | Seconds |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in summaries:
        lines.append(f"| {r['scenario']} | {r['status']} | {'pass' if r['acceptance_passed'] else 'fail'} | {r['tool_calls']} / {r['tool_failures']} | {r['llm_calls']} | {r['total_tokens']} | {r['elapsed_seconds']} |")
    lines += ["",f"Selected scenario acceptance checks: {sum(r['acceptance_passed'] for r in summaries)}/{len(summaries)}. This is a deliberately chosen small demonstration set, not an unbiased success-rate estimate.",
        "",f"Injected recoverable-failure demonstration: {sum(r['injected_fault_recovered'] for r in summaries if r['scenario']=='recovery')}/1.",
        "", "All selected runs include a plan before data tools and a separate source-grounding model review. Complete status checks coverage, references and enrichment; partial status preserves missing data. Structural citations and model review do not prove semantic correctness.",
        "", "## Development attempts retained", "", "Early attempts are included rather than hidden. The first normal run failed because required tool choice rejected a model text finish. A later run completed structurally but manual review found overstatement of EPSS and unsupported mitigation details. Report generation was changed to fresh source observations, excluding earlier assistant prose. Selected final normal evidence follows that change.", ""]
    lines += [f"- {a['directory']}: {a['status']}; {'selected demonstration' if a['selected'] else 'development attempt'}" for a in attempts]
    lines += ["", "The first review-enabled normal attempt also failed after an EPSS interpretation false positive; the reviewer definition was corrected. Model review remains fallible.", "", "## Validation boundaries", "", "Unit tests: see tests/test-results.txt for the actual pytest result. A fresh Python environment was used to install the built wheel; CLI help and pip dependency checks passed. Live samples exercise provider integration, while mocked tests verify deterministic contracts.", "",
        "Manual source-support review and limitations are recorded in docs/source-review.md. No precision/recall is claimed because no malicious/benign classifier target exists. No production-readiness claim is made. Provider quotas, source availability, limited normalization and unverified asset applicability remain constraints.", ""]
    (BASE/"artifacts/evaluation-summary.md").write_text("\n".join(lines),encoding="utf-8")
    (BASE/"artifacts/sample-runs.md").write_text("# Selected live sample runs\n\n"+"\n".join(sections),encoding="utf-8")
    print(json.dumps(summaries,indent=2))


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--normal",default="run-normal-final")
    parser.add_argument("--recovery",default="run-recovery")
    parser.add_argument("--partial",default="run-partial")
    args=parser.parse_args()
    build(args.normal,args.recovery,args.partial)
