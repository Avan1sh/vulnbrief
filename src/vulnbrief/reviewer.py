"""Presentation metadata for genuine retained runs, never agent responses."""
from .report import resolve_pointer

DEMONSTRATIONS = (
    {'run_id': 'v02-reviewed', 'title': 'Asset investigation', 'number': '01',
     'description': 'Three fictional assets. Live sources. Three version outcomes.',
     'focus': 'findings'},
    {'run_id': 'v02-recovery-final', 'title': 'Failure recovery', 'number': '02',
     'description': 'An injected timeout, then a model-selected official mirror.',
     'focus': 'timeline'},
    {'run_id': 'v02-partial-final', 'title': 'Missing information', 'number': '03',
     'description': 'An unavailable CVE and missing score stay unknown.',
     'focus': 'findings'},
)


def demonstrations(history):
    result = []
    for item in DEMONSTRATIONS:
        try:
            record = history.get(item['run_id'])
        except KeyError:
            continue
        report = record.get('report')
        if not report:
            continue
        result.append({**item, 'recorded_at': report['created_at'],
                       'status': report['status'], 'model': report['model'],
                       'provenance': 'Recorded real LLM run with live public sources',
                       'metrics': report['metrics']})
    return result


def inspect_evidence(report, evidence_id, field_path=''):
    """Resolve an original observation; null is a value, not a missing field."""
    evidence = next((e for e in report.get('evidence', [])
                     if e['evidence_id'] == evidence_id), None)
    if evidence is None:
        raise KeyError(evidence_id)
    value = resolve_pointer(evidence['data'], field_path) if field_path else evidence['data']
    claims = []
    analysis = report.get('analysis') or {}
    for claim in analysis.get('summary', []):
        if any(r['evidence_id'] == evidence_id and
               (not field_path or r['field_path'] == field_path)
               for r in claim.get('field_refs', [])):
            claims.append({'kind': 'summary', 'text': claim['text']})
    for finding in analysis.get('findings', []):
        for action in finding.get('recommended_actions', []):
            if isinstance(action, dict) and any(r['evidence_id'] == evidence_id and
                    (not field_path or r['field_path'] == field_path)
                    for r in action.get('support', [])):
                claims.append({'kind': 'conditional action', 'text': action['text'],
                               'applies_when': action['applies_when']})
    return {key: evidence[key] for key in ('evidence_id', 'tool', 'source_url',
            'retrieved_at', 'source_date', 'location', 'cve_ids')} | {
            'field_path': field_path, 'value': value, 'linked_claims': claims,
            'note': 'Original source value. A valid citation does not prove the claim.'}
