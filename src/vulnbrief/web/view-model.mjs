/* Pure presentation calculations. No model priorities or canned findings. */
export function kevSummary(report) {
  if (!report) return {value: '—', detail: 'No report selected'};
  const scope = new Set([
    ...(report.analysis?.findings || []).map(f => f.cve_id),
    ...(report.evidence || []).flatMap(e => e.cve_ids || [])
  ]);
  const observed = new Map();
  for (const e of report.evidence || []) {
    if (e.tool !== 'lookup_kev') continue;
    for (const row of e.data.results || []) {
      if (!observed.has(row.cve_id)) observed.set(row.cve_id, new Set());
      observed.get(row.cve_id).add(row.status);
    }
  }
  const known = [...scope].filter(id => {
    const states = observed.get(id);
    return states?.size === 1 && ['present', 'not_present'].includes([...states][0]);
  });
  const present = known.filter(id => observed.get(id).has('present')).length;
  const unknown = scope.size - known.length;
  if (!known.length) return {value: 'Unknown', detail: 'No conclusive KEV observation retrieved'};
  return {
    value: unknown ? `${present} + unknown` : String(present),
    detail: unknown ? `${known.length}/${scope.size} CVEs checked; ${unknown} unknown` : `${known.length} checked · catalog absence does not prove safety`
  };
}

export function executionPhase(status, events) {
  if (!['queued', 'running'].includes(status)) return {name: status || 'Select a run', detail: 'Recorded observations and report'};
  if (status === 'queued') return {name: 'Queued', detail: 'Waiting for the local worker'};
  const last = events.at(-1);
  if (!last) return {name: 'Starting', detail: 'Waiting for the first runtime event'};
  if (['provider_retry','provider_schema_retry'].includes(last.event)) return {name: 'Provider retry', detail: last.code === 'daily_quota' ? 'Daily quota reported; run will stop' : 'A bounded retry is in progress'};
  if (['report_review','report_rejected'].includes(last.event)) return {name: 'Reviewing report', detail: 'Checking evidence support and report structure'};
  if (last.event === 'tool_start') return {name: 'Retrieving evidence', detail: last.tool};
  if (events.some(e => e.event === 'plan')) return {name: 'Investigating', detail: 'The model is selecting actions or preparing its report'};
  return {name: 'Planning', detail: 'Preparing a public action plan'};
}
