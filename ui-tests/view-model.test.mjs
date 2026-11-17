import {test} from 'node:test';
import assert from 'node:assert/strict';
import {kevSummary, executionPhase} from '../src/vulnbrief/web/view-model.mjs';

const A='CVE-2024-3400', B='CVE-2021-44228';
const report=(rows, ids=[A])=>({analysis:{findings:ids.map(cve_id=>({cve_id}))}, evidence:rows===null?[]:[{tool:'lookup_kev',cve_ids:ids,data:{results:rows}}]});
test('an unavailable KEV lookup is unknown, never zero',()=>assert.equal(kevSummary(report(null)).value,'Unknown'));
test('a retrieved catalog absence can show zero with its limitation',()=>{
  const result=kevSummary(report([{cve_id:A,status:'not_present'}]));
  assert.equal(result.value,'0');assert.match(result.detail,/does not prove safety/);
});
test('partial KEV coverage does not hide an unchecked CVE',()=>assert.equal(kevSummary(report([{cve_id:A,status:'present'}],[A,B])).value,'1 + unknown'));
test('conflicting catalog observations stay unknown',()=>assert.equal(kevSummary(report([{cve_id:A,status:'present'},{cve_id:A,status:'not_present'}])).value,'Unknown'));
test('successful evidence remains valid after an earlier request failure',()=>{
  const value=report([{cve_id:A,status:'present'}]);value.tool_errors=[{tool:'lookup_kev'}];
  assert.equal(kevSummary(value).value,'1');
});
test('no selected report has no invented count',()=>assert.equal(kevSummary(null).value,'—'));
test('the observed execution phase distinguishes provider retries',()=>assert.equal(executionPhase('running',[{event:'provider_retry',code:'rate_limit'}]).name,'Provider retry'));
test('completed runs do not appear to be running',()=>assert.equal(executionPhase('partial',[{event:'tool_start'}]).name,'partial'));
