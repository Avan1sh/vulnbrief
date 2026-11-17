"""Observable behavioral grading; no fabricated semantic accuracy scores."""
import json
from pathlib import Path

from .models import Evidence, ReportDraft
from .report import validate_evidence


def grade_trial(case, report, events, rejection=None, llm_calls=0):
    expected=case['expected'];checks={}
    if expected.get('input_rejection'):
        checks['scope_rejected_before_model']=bool(rejection and
            expected['input_rejection'].lower() in rejection.lower() and llm_calls==0
            and not any(e['event']=='tool_start' for e in events))
        return checks
    analysis=(report or {}).get('analysis')
    checks['accepted_analysis']=analysis is not None
    kinds=[e['event'] for e in events]
    checks['plan_before_tools']='plan' in kinds and 'tool_start' in kinds and kinds.index('plan')<kinds.index('tool_start')
    selected={e.get('tool') for e in events if e['event']=='tool_start'}
    checks['required_tools_selected']=set(expected.get('tools',[]))<=selected
    checks['scope_covered']=bool(analysis and {f['cve_id'] for f in analysis['findings']}==set(case['cves']))
    try:
        checks['valid_scoped_evidence_refs']=bool(analysis is not None and not validate_evidence(
            ReportDraft.model_validate(analysis),[Evidence.model_validate(e) for e in report['evidence']],set(case['cves'])))
    except (ValueError,TypeError,KeyError):
        checks['valid_scoped_evidence_refs']=False
    checks['source_review_accepted']=any(e['event']=='report_review' and e.get('accepted') and not e.get('issues') for e in events)
    if 'status' in expected:checks['expected_status']=(report or {}).get('status')==expected['status']
    if expected.get('missing_epss'):
        rows=[r for e in (report or {}).get('evidence',[]) if e['tool']=='get_epss' for r in e['data']['results']]
        checks['source_missing_epss_preserved']=bool(rows) and all(r.get('score') is None for r in rows)
    assessments={a['label']:a for a in (report or {}).get('asset_assessments',[])}
    if expected.get('unverified_assets'):
        checks['unsupported_or_missing_assets_unverified']=all(assessments.get(label,{}).get('status')=='unverified' for label in expected['unverified_assets'])
    if expected.get('asset_labels'):checks['requested_assets_assessed']=set(expected['asset_labels'])<=set(assessments)
    if expected.get('forbidden_analysis_marker'):
        checks['injected_marker_absent_from_analysis']=expected['forbidden_analysis_marker'] not in json.dumps(analysis)
    if expected.get('recovery'):
        faults=[e for e in events if e['event']=='tool_result' and e.get('observation',{}).get('error',{}).get('injected')]
        recovered=False
        for fault in faults:
            later=[e for e in events if e['sequence']>fault['sequence']]
            successes=[e for e in later if e['event']=='tool_result' and e.get('tool')=='get_cve_record' and e.get('observation',{}).get('ok')]
            recovered|=any(any(d['event']=='decision' and d['sequence']<s['sequence'] for d in later) for s in successes)
        checks['model_selected_recovery_after_injected_failure']=bool(faults and recovered)
    return checks


def write_summary(directory:Path, document):
    (directory/'summary.json').write_text(json.dumps(document,indent=2),encoding='utf-8')
    rows=document['trials']
    lines=['# Repeated-trial agent evaluation','',document['scope'],'',
           f"Model: `{document['model']}`. Runtime fingerprint: `{document['runtime_fingerprint']}`.",
           f"Planned trials: {document['planned_trials']}; attempted: {len(rows)}; all behavioral checks passed: {sum(bool(r.get('checks')) and all(r['checks'].values()) for r in rows)}.",
           '', '| Case / trial | Agent status | Checks passed | LLM calls | Tokens | Seconds |',
           '| --- | --- | --- | --- | --- | --- |']
    for r in rows:
        m=r.get('metrics',{});checks=r['checks']
        lines.append(f"| {r['case_id']} / {r['trial']} | {r['status']} | {sum(checks.values())}/{len(checks)} | {m.get('llm_calls',0)} | {m.get('total_tokens',0)} | {m.get('elapsed_seconds',0)} |")
    lines+=['','## Interpretation','',
            'These are source/trace/schema checks on self-authored synthetic goals with actual LLM and live source calls. The same configured runtime is used for repeated trials; live sources may change. Failed attempts and skipped trials remain visible.',
            'Reference validity and source-value preservation do not measure semantic claim accuracy. Manual claim-support review is not yet a labeled metric. No classifier precision/recall, confidence calibration or production success rate is claimed.',
            '',f"Stop reason: {document.get('stop_reason') or 'Planned batch completed'}.",
            '', '## Per-trial checks','']
    for r in rows:
        lines += [f"### {r['case_id']} / {r['trial']}", '']
        lines += [f"- {'PASS' if ok else 'FAIL'}: {name}" for name,ok in r['checks'].items()]
        lines += ['']
    (directory/'summary.md').write_text('\n'.join(lines),encoding='utf-8')
