"""Validate evidence scope and render a report from the accepted model decisions."""
import json
import re


def version_tokens(text):
    normalized=str(text).translate(str.maketrans({c:'-' for c in '\u2010\u2011\u2012\u2013\u2014\u2212'}))
    return set(re.findall(r'\b\d+\.\d+\.\d+(?:-h\d+)?\b',normalized))


def upgrade_targets(text):
    """Additional lexical guard for common named upgrade/install recommendations.

    This deliberately does not claim complete semantic verification of prose.
    """
    normalized=str(text).translate(str.maketrans({c:'-' for c in '\u2010\u2011\u2012\u2013\u2014\u2212'}))
    return set(re.findall(r'\b(?:upgrade|update|patch|install|deploy)\b[^;!?\n]{0,100}?\b(?:to\s+(?:version\s+)?|version\s+)(\d+\.\d+\.\d+(?:-h\d+)?)\b',normalized,re.I))

from .models import ReportDraft


def resolve_pointer(data, pointer):
    value = data
    for token in pointer.removeprefix("/").split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            if not key.isdigit():
                raise KeyError(key)
            value = value[int(key)]
        elif isinstance(value, dict):
            value = value[key]
        else:
            raise KeyError(key)
    return value


def source_facts(evidence):
    """Factual source fields are copied by the runtime, never invented by a model."""
    facts = {}
    for e in evidence:
        for cve in e.cve_ids:
            entry = facts.setdefault(cve, {"source_severity": [], "kev": [], "epss": [], "version_citations": []})
            if e.tool=='get_vendor_advisory':
                entry['version_citations'].extend({'version':v,'evidence_id':e.evidence_id,'field_path':f'/fixed_version_candidates/{i}'} for i,v in enumerate(e.data.get('fixed_version_candidates',[])))
            if e.tool in {"get_cve_record", "get_vendor_advisory"}:
                for i, metric in enumerate(e.data.get("metrics", [])):
                    for name, value in metric.items():
                        if name.startswith("cvss") and isinstance(value, dict):
                            entry["source_severity"].append({"evidence_id":e.evidence_id,
                                "field_path":f"/metrics/{i}/{name}", "version":value.get("version"),
                                "score":value.get("baseScore"), "severity":value.get("baseSeverity"),
                                "source_url":e.source_url})
            for category, tool in (("kev","lookup_kev"),("epss","get_epss")):
                if e.tool == tool:
                    entry[category].extend({"evidence_id":e.evidence_id, **row} for row in e.data["results"] if row["cve_id"]==cve)
    return facts


def validate_evidence(draft: ReportDraft, evidence: list, scope: set[str]) -> list[str]:
    errors = []
    by_id = {e.evidence_id: e for e in evidence}
    def check_ref(ref, cve=None):
        e = by_id.get(ref.evidence_id)
        if not e or (cve and cve not in e.cve_ids):
            return False
        try:
            value = resolve_pointer(e.data, ref.field_path)
            # Root-level metadata for multi-CVE observations is insufficient.
            if cve and ref.field_path.startswith("/results/"):
                row = resolve_pointer(e.data, "/" + "/".join(ref.field_path.strip("/").split("/")[:2]))
                if row.get("cve_id") != cve:
                    return False
            if cve and ref.field_path.startswith(("/assets/", "/assessments/")):
                row = resolve_pointer(e.data, "/" + "/".join(ref.field_path.strip("/").split("/")[:2]))
                if row.get("cve_id") != cve:
                    return False
            return True  # An explicit null is valid evidence of a missing score/value.
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            return False
    for claim in draft.summary:
        if any(eid not in by_id for eid in claim.evidence_ids):
            errors.append("Summary contains unknown evidence references")
        if any(not check_ref(ref) or ref.evidence_id not in claim.evidence_ids for ref in claim.field_refs):
            errors.append("Summary contains missing or inconsistent source field references")
    found = [finding.cve_id for finding in draft.findings]
    if len(set(found)) != len(found) or set(found) != scope:
        errors.append("Findings must cover each scoped CVE exactly once")
    ranks = [finding.rank for finding in draft.findings]
    if sorted(ranks) != list(range(1, len(found) + 1)):
        errors.append("Ranks must be unique and contiguous starting at 1")
    for finding in draft.findings:
        refs = [by_id.get(eid) for eid in finding.evidence_ids]
        if any(e is None or finding.cve_id not in e.cve_ids for e in refs):
            errors.append(f"{finding.cve_id}: missing or unrelated evidence reference")
        for action in finding.recommended_actions:
            invalid=[f"{ref.evidence_id}:{ref.field_path}" for ref in action.support if not check_ref(ref,finding.cve_id)]
            if not action.applies_when.strip() or invalid:
                errors.append(f"{finding.cve_id}: action source fields not found or unrelated: {invalid}; cite fields directly inside evidence.data, without a /data prefix, and state prerequisites")
            if not invalid:
                cited_versions=set()
                for ref in action.support:
                    cited_versions |= version_tokens(json.dumps(resolve_pointer(by_id[ref.evidence_id].data,ref.field_path)))
                missing=version_tokens(action.text)-cited_versions
                if missing:
                    errors.append(f"{finding.cve_id}: action versions {sorted(missing)} are not present in its cited source values. Use the exact version_citations supplied in source_facts or cite the matching vendor table row.")
                fixed_targets=set()
                for ref in action.support:
                    e=by_id[ref.evidence_id]
                    if e.tool=='get_vendor_advisory' and re.fullmatch(r'/fixed_version_candidates/\d+',ref.field_path):
                        fixed_targets |= version_tokens(str(resolve_pointer(e.data,ref.field_path)))
                unsupported_targets=upgrade_targets(action.text)-fixed_targets
                if unsupported_targets:
                    errors.append(f"{finding.cve_id}: named upgrade targets {sorted(unsupported_targets)} lack an exact current vendor fixed_version_candidates citation. An affected-version description is not proof of a fixed target. Omit the target and recommend checking current vendor guidance if no supported advisory exists.")
    if draft.status == "complete":
        tools = {e.tool for e in evidence}
        if len(tools) < 2:
            errors.append("A complete investigation requires at least two distinct data tools")
        for cve in scope:
            if not any(e.tool == "get_cve_record" and cve in e.cve_ids for e in evidence):
                errors.append(f"{cve}: complete result lacks a CVE record")
            if any(e.tool == "get_cve_record" and cve in e.cve_ids and e.data.get("record_state") != "PUBLISHED" for e in evidence):
                errors.append(f"{cve}: non-published records require partial status")
            kev = [row for e in evidence if e.tool == "lookup_kev" for row in e.data["results"] if row["cve_id"] == cve]
            epss = [row for e in evidence if e.tool == "get_epss" for row in e.data["results"] if row["cve_id"] == cve]
            if not kev or not epss or any(row.get("score") is None for row in epss):
                errors.append(f"{cve}: incomplete enrichment must use partial status")
    # Multiple retrieval locations are not independent votes; prevent silent conflicts.
    for cve in scope:
        records = [e for e in evidence if e.tool == "get_cve_record" and cve in e.cve_ids]
        if len({(e.source_date, json.dumps(e.data, sort_keys=True)) for e in records}) > 1 and draft.status == "complete":
            errors.append(f"{cve}: conflicting record versions require partial status and disclosure")
    return list(dict.fromkeys(errors))


def render_markdown(report: dict) -> str:
    lines = ["# VulnBrief investigation", "", f"Status: **{report['status']}**", "",
             f"Goal: {report['goal']}", "", f"Run: `{report['run_id']}` | Model: `{report['model']}`",
             "", "## Plan", ""]
    for step in (report.get("plan") or {}).get("steps", []):
        lines.append(f"- {step}")
    draft = report.get("analysis")
    if report.get("source_facts"):
        lines += ["", "## Source-assigned severity (separate from agent priority)", ""]
        for cve, facts in report["source_facts"].items():
            metrics = facts["source_severity"]
            lines.append(f"- {cve}: " + ("; ".join(f"CVSS {m['version']} / {m['score']} / {m['severity']} [{m['evidence_id']}]" for m in metrics) if metrics else "No source-assigned CVSS metric retrieved"))
    if draft:
        lines += ["", "## Summary", ""]
        for claim in draft["summary"]:
            lines.append(f"- {claim['text']} [{', '.join(claim['evidence_ids'])}]")
        lines += ["", "## Recommended investigation order", ""]
        for finding in sorted(draft["findings"], key=lambda f: f["rank"]):
            lines += [f"### {finding['rank']}. {finding['cve_id']} - {finding['priority']}", "",
                      finding["rationale"] + f" [{', '.join(finding['evidence_ids'])}]", "", "Recommended actions:", ""]
            for action in finding["recommended_actions"]:
                if isinstance(action, str):  # Read-only rendering of archived v0.1 artifacts.
                    lines.append(f"- {action}")
                else:
                    refs = ", ".join(f"{r['evidence_id']}:{r['field_path']}" for r in action["support"])
                    lines.append(f"- {action['text']}\n  - Prerequisites: {action['applies_when']}\n  - Source fields: {refs}")
            lines += ["", "Uncertainties:", ""] + [f"- {u}" for u in finding["uncertainties"]]
        lines += ["", "## Limitations", ""] + [f"- {v}" for v in draft["limitations"]]
    if report.get("stop_reason"):
        lines += ["", "## Execution limit or failure", "", report["stop_reason"]]
    if report.get("tool_errors"):
        lines += ["", "## Failed requests (distinct from evidence)", ""]
        lines += [f"- {e['error_id']}: {e['tool']} / {e['code']} / {e['message']}" for e in report["tool_errors"]]
    if report.get("asset_assessments"):
        lines += ["", "## Version-based asset assessments", ""]
        for a in report['asset_assessments']:
            lines += [f"- {a['label']}: {a['status']} ({a['product_version'] or 'version missing'}) - {a['reason']}"]
    lines += ["", "## Source observations", "", "These facts are attached by the runtime from tool results, not rewritten by the LLM.", ""]
    for e in report["evidence"]:
        lines += [f"### {e['evidence_id']} - {e['tool']}", "",
                  f"Source: {e['source_url']}", "", f"Retrieved: {e['retrieved_at']} | Source date: {e['source_date']} | Location: {e['location']}", "",
                  "```json", json.dumps(e["data"], ensure_ascii=False, indent=2), "```", ""]
    lines += ["## Execution summary", "", "```json", json.dumps(report["metrics"], indent=2), "```", "",
              "A watchlist association does not prove asset applicability. Missing evidence is unknown, not safe.", ""]
    return "\n".join(lines)
