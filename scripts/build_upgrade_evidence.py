"""Build a version-labeled evidence bundle from actual retained executions."""
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
SELECTED=['v02-reviewed','v02-recovery-final','v02-partial-final']


def build():
    selected=[];sections=[]
    for name in SELECTED:
        folder=BASE/'artifacts'/name
        report=json.loads((folder/'report.json').read_text(encoding='utf-8'))
        events=[json.loads(l) for l in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
        kinds=[e['event'] for e in events]
        row={'run_id':name,'status':report['status'],'schema_version':report.get('schema_version'),
             'model':report['model'],'plan_before_tools':kinds.index('plan')<kinds.index('tool_start'),
             'source_review_accepted':any(e['event']=='report_review' and e['accepted'] and not e['issues'] for e in events),
             'tool_names':sorted({e['tool'] for e in report['evidence']}),**report['metrics']}
        if report.get('asset_assessments'):
            row['asset_statuses']={a['label']:a['status'] for a in report['asset_assessments']}
        selected.append(row)
        sections += [f'# {name}\n', 'Actual live execution. Fictional inventory/test goals are disclosed in examples and docs/upgrades.md.\n',
                     (folder/'transcript.md').read_text(encoding='utf-8'), '\n## Accepted analysis\n',
                     '```json\n'+json.dumps(report['analysis'],indent=2,ensure_ascii=False)+'\n```\n']
    retained=[]
    for path in sorted((BASE/'artifacts').glob('*/report.json')):
        r=json.loads(path.read_text(encoding='utf-8'))
        retained.append({'run_id':r['run_id'],'status':r['status'],'schema_version':r.get('schema_version','0.1'),
                         'model':r['model'],'selected':r['run_id'] in SELECTED})
    document={'scope':'Selected engineering demonstrations; not an unbiased reliability benchmark',
              'selected_runs':selected,'all_retained_agent_attempts':retained,
              'visual_verification':'Blocked: Computer Use could not establish the active Windows browser URL confidently',
              'local_api_tests':'See tests/test-results.txt; loopback-enabled test run',
              'source_limitations':'See docs/source-review.md and docs/upgrades.md'}
    (BASE/'artifacts/evaluation.json').write_text(json.dumps(document,indent=2),encoding='utf-8')
    lines=['# VulnBrief v0.2 engineering evaluation','',
           'Selected runs use real LLM calls and public live sources. Inventory and unavailable-CVE inputs are fictional; the timeout is deliberately injected. No static response mode is used.','',
           '| Run | Status | Model | Tools / failures | LLM calls | Tokens | Seconds |',
           '| --- | --- | --- | --- | --- | --- | --- |']
    for r in selected:
        lines.append(f"| {r['run_id']} | {r['status']} | {r['model']} | {r['tool_calls']} / {r['tool_failures']} | {r['llm_calls']} | {r['total_tokens']} | {r['elapsed_seconds']} |")
    lines += ['', '## Scope of verification','',
              '- The normal run exercises six tools, asset version statuses and field-cited conditional actions.',
              '- The recovery run exposes an ERR failure and subsequent model-selected recovery. Successful evidence retains separate E IDs.',
              '- The partial run preserves absent record/score information as unknown.',
              '- Unit/API tests cover evidence paths, concrete version citations, version boundaries, queueing, persistent review state and comparisons. See tests/test-results.txt.',
              '- Local API review write/read/restore and snapshot comparison were checked against real generated task drafts. No external action was performed.',
              '- Browser visual verification was blocked by Computer Use active-URL confidence enforcement. Frontend syntax and ID references were checked; no completed browser visual test is claimed.',
              '- Structural checks and model review do not prove semantic accuracy, full asset applicability or production readiness. No classifier precision/recall is claimed.',
              '', '## Retained attempts','',
              'Baselines and failed development attempts are retained with their actual outcomes. Failures include protocol/schema errors, minute/day quota limits and rejected reports. The selected small set is not an unbiased success-rate sample.','']
    lines += [f"- {r['run_id']}: {r['status']} / schema {r['schema_version']}"+(' / selected' if r['selected'] else '') for r in retained]
    (BASE/'artifacts/evaluation-summary.md').write_text('\n'.join(lines),encoding='utf-8')
    (BASE/'artifacts/sample-runs.md').write_text('# Selected v0.2 live sample runs\n\n'+'\n'.join(sections),encoding='utf-8')
    print(json.dumps(selected,indent=2))


if __name__=='__main__':build()
