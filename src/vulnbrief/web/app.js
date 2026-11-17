/* Local workbench. All model/source text is rendered with textContent. */
const $ = id => document.getElementById(id);
let selected = null, selectedData = null, currentRuns = [], events = [], lastTaskState = '';
const active = status => ['queued','running'].includes(status);
const label = value => String(value || '').replaceAll('_',' ');
const node = (tag, text, className) => { const e=document.createElement(tag); if(text!==undefined)e.textContent=text; if(className)e.className=className; return e; };
function notice(text,error=false){ $('notice').textContent=text; $('notice').className=error?'error':''; }
async function api(url,options={}){
  const r=await fetch(url,{...options,headers:{'Content-Type':'application/json',...options.headers}});
  const data=await r.json().catch(()=>({detail:`Request returned ${r.status}`}));
  if(!r.ok)throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail));
  return data;
}
function badge(status){ return node('span',label(status),`badge ${status}`); }
function when(value){ return value?new Date(value).toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):''; }
function showTab(name){
  for(const b of document.querySelectorAll('[data-tab]')) b.classList.toggle('selected',b.dataset.tab===name);
  for(const id of ['findings','evidence','timeline'])$(id).classList.toggle('hidden',id!==name);
}
function refButtons(refs){
  const root=node('div',undefined,'refs');
  for(const ref of refs){
    const id=typeof ref==='string'?ref:ref.evidence_id;
    const text=typeof ref==='string'?ref:`${id}:${ref.field_path}`;
    const b=node('button',text,'ref'); b.title='Inspect original source observation';
    b.onclick=()=>{showTab('evidence');const source=$(`src-${id}`);if(source){source.open=true;source.scrollIntoView({behavior:'smooth',block:'center'});source.classList.add('flash');setTimeout(()=>source.classList.remove('flash'),1800);}};
    root.append(b);
  }
  return root;
}
async function loadRuns(){
  currentRuns=await api('/api/runs');
  $('runList').replaceChildren();
  if(!currentRuns.length)$('runList').append(node('div','No investigations yet. Start with a goal or the fictional inventory.','empty'));
  for(const run of currentRuns){
    const b=node('button',undefined,`run-item${run.run_id===selected?' selected-run':''}`);
    const head=node('div');head.append(node('strong',run.run_id),badge(run.status));
    b.append(head,node('p',run.goal),node('time',when(run.created_at)));b.onclick=()=>selectRun(run.run_id);$('runList').append(b);
  }
  for(const id of ['before','after']){
    const previous=$(id).value;$(id).replaceChildren();
    for(const run of currentRuns.filter(r=>!active(r.status))){ const option=node('option',`${run.run_id} · ${label(run.status)}`);option.value=run.run_id;$(id).append(option); }
    if([...$(id).options].some(o=>o.value===previous))$(id).value=previous;
  }
  if(!$('before').dataset.initialized && $('before').options.length>1){$('before').selectedIndex=1;$('before').dataset.initialized='1';}
}
async function selectRun(id){ selected=id;events=[];lastTaskState='';await Promise.all([loadRuns(),loadDetail()]); }
async function loadDetail(){
  if(!selected)return;
  const id=selected,data=await api(`/api/runs/${encodeURIComponent(id)}`);
  if(id!==selected)return;
  selectedData=data;
  const report=data.report;
  $('runTitle').textContent=data.run_id;
  $('runMeta').textContent=`${label(data.status)} · ${when(data.created_at)} · ${data.goal}`;
  $('statStatus').textContent=label(data.status);
  $('statModel').textContent=data.model||'Model assigned when run starts';
  $('rerun').disabled=active(data.status);
  $('download').classList.toggle('disabled',!report);
  $('download').href=`/api/runs/${encodeURIComponent(id)}/download/report`;
  const incremental=await api(`/api/runs/${encodeURIComponent(id)}/events?after=${events.at(-1)?.sequence||0}`);
  if(id!==selected)return;
  events.push(...incremental);renderEvents();
  const assets=report?.asset_assessments||[];
  $('statAssets').textContent=report?String(assets.length):'—';
  const kev=new Set((report?.evidence||[]).filter(e=>e.tool==='lookup_kev').flatMap(e=>e.data.results.filter(r=>r.status==='present').map(r=>r.cve_id)));
  $('statKev').textContent=report?String(kev.size):'—';
  if(report){renderFindings(report);renderEvidence(report);}
  else{
    $('findings').replaceChildren(node('div',data.error||'The agent is collecting evidence. Follow its plan and tool observations in the execution timeline.','empty'));
    $('evidence').replaceChildren(node('div','Original observations appear when the report artifact is ready. Live tool results are visible in the timeline.','empty'));
    $('evidenceCount').textContent='0';
  }
  if(lastTaskState!==data.status){await loadTasks();lastTaskState=data.status;}
}
function renderFindings(report){
  const root=$('findings');root.replaceChildren();
  if(!report.schema_version)root.append(node('div','Archived v0.1 demonstration. Start an upgraded investigation for asset assessments and field-level action citations.','banner'));
  if(report.stop_reason)root.append(node('div',report.stop_reason,'banner'));
  if(report.asset_assessments?.length){
    const wrap=node('div',undefined,'asset-table'),table=node('table');
    const header=node('tr');for(const h of ['ASSET / OWNER','PRODUCT VERSION','VERSION ASSESSMENT','INFORMATION NEEDED'])header.append(node('th',h));table.append(header);
    for(const a of report.asset_assessments){
      const row=node('tr'),name=node('td',a.label);name.append(node('small',a.owner||'Owner unassigned'));
      const version=node('td',`${a.product||'Product missing'} ${a.product_version||'—'}`);
      const status=node('td');status.append(badge(a.status),node('small',a.reason));
      const missing=node('td',(a.required_information||[]).join('; ')||'No version information gap');
      if(a.basis?.length)missing.append(refButtons(a.basis));
      row.append(name,version,status,missing);table.append(row);
    }
    wrap.append(table);root.append(wrap);
  }
  if(!report.analysis){root.append(node('div','This run did not produce an accepted analysis. Original observations and errors remain available.','empty'));return;}
  for(const f of [...report.analysis.findings].sort((a,b)=>a.rank-b.rank)){
    const card=node('article',undefined,'finding'),head=node('div',undefined,'finding-head');
    head.append(node('h3',`${f.rank.toString().padStart(2,'0')} / ${f.cve_id}`),badge(`${f.priority}`));card.append(head);
    const metrics=report.source_facts?.[f.cve_id]?.source_severity||[];
    card.append(node('p',metrics.length?`Source severity: ${metrics.map(m=>`CVSS ${m.version} · ${m.score} · ${m.severity}`).join(' / ')}`:'No source-assigned severity metric recorded in this report.','muted'));
    card.append(node('p',f.rationale),refButtons(f.evidence_ids||[]),node('h4','Recommended next actions'));
    for(const action of f.recommended_actions){
      const item=node('div',typeof action==='string'?action:action.text,'action');
      if(typeof action==='object'){item.append(node('small',`Applies when: ${action.applies_when}`),refButtons(action.support));}
      card.append(item);
    }
    card.append(node('h4','Uncertainties'));const list=node('ul');for(const u of f.uncertainties)list.append(node('li',u));card.append(list);root.append(card);
  }
  if(report.analysis.limitations?.length){const box=node('div',undefined,'banner');box.append(node('strong','Review boundaries'),node('p',report.analysis.limitations.join(' ')));root.append(box);}
}
function renderEvidence(report){
  const root=$('evidence');root.replaceChildren();$('evidenceCount').textContent=report.evidence.length;
  for(const e of report.evidence){
    const box=node('details',undefined,'source');box.id=`src-${e.evidence_id}`;
    box.append(node('summary',`${e.evidence_id} / ${e.tool} · ${e.location}`));
    const meta=node('div',`Retrieved ${when(e.retrieved_at)} · source date ${e.source_date||'not supplied'}`,'meta');box.append(meta);
    if(e.source_url.startsWith('https://')){const a=node('a','Open original source ↗');a.href=e.source_url;a.target='_blank';a.rel='noopener noreferrer';box.append(a);}
    else box.append(node('small',e.source_url));
    box.append(node('pre',JSON.stringify(e.data,null,2)));root.append(box);
  }
  for(const e of report.tool_errors||[]){const box=node('details',undefined,'source');box.append(node('summary',`${e.error_id} / failed request · ${e.tool}`),node('pre',JSON.stringify(e,null,2)));root.append(box);}
}
function renderEvents(){
  const root=$('timeline');root.replaceChildren();
  if(!events.length){root.append(node('div','Waiting for the first execution event.','empty'));return;}
  for(const e of events){
    const item=node('div',undefined,'event'),head=node('h4',`${String(e.sequence).padStart(2,'0')} · ${label(e.event)}${e.tool?' / '+e.tool:''}`);
    head.append(node('time',when(e.time)));item.append(head);
    const details=node('details');if(e.event==='plan')details.open=true;
    details.append(node('summary',e.event==='plan'?'Plan and assumptions':'Inspect event details'),node('pre',JSON.stringify(e,null,2)));item.append(details);root.append(item);
  }
}
async function loadTasks(){
  const tasks=await api('/api/tasks');$('railTasks').textContent=tasks.length;
  $('statTasks').textContent=tasks.filter(t=>t.run_id===selected).length;
  const root=$('taskList');root.replaceChildren();
  if(!tasks.length){root.append(node('div','An upgraded report creates draft follow-ups for assets that need investigation. Version-unaffected assets do not get remediation drafts.','empty'));return;}
  for(const task of tasks){
    const row=node('article',undefined,'task'),body=node('div');
    body.append(node('h3',`${task.asset} / ${task.cve_id}`),node('div',task.action),node('p',`Prerequisites: ${task.applies_when}`),node('p',`${label(task.applicability)} · Agent priority: ${task.priority} · ${task.run_id}`));
    const support=node('p',task.support.map(r=>`${r.evidence_id}:${r.field_path}`).join(', '));body.append(support);
    const inspect=node('button','Inspect linked investigation ↗','link-button');inspect.onclick=async()=>{await selectRun(task.run_id);showTab('evidence');$('workspace').scrollIntoView({behavior:'smooth'});};body.append(inspect);
    const assignment=node('div'),owner=node('input');owner.value=task.owner;owner.maxLength=120;owner.setAttribute('aria-label',`Owner for ${task.asset}`);
    const note=node('textarea');note.value=task.review_note;note.maxLength=1500;note.placeholder='Review note';note.setAttribute('aria-label',`Review note for ${task.asset}`);
    assignment.append(node('label','Owner'),owner,node('label','Review note'),note);
    const controls=node('div'),select=node('select');
    for(const status of ['draft','accepted','dismissed']){const option=node('option',label(status));option.value=status;select.append(option);}select.value=task.status;
    select.setAttribute('aria-label',`Review status for ${task.asset}`);
    const save=node('button','Save review','secondary');save.onclick=async()=>{try{await api(`/api/tasks/${task.task_id}`,{method:'PATCH',body:JSON.stringify({status:select.value,owner:owner.value,review_note:note.value})});save.textContent='Saved ✓';setTimeout(()=>save.textContent='Save review',1800);}catch(e){notice(e.message,true);}};
    controls.append(node('label','Draft status'),select,save,node('p','Review only. No change is executed.'));
    row.append(body,assignment,controls);root.append(row);
  }
}
$('start').onclick=async()=>{
  const button=$('start');button.disabled=true;notice('Queueing investigation…');
  try{
    const result=await api('/api/runs',{method:'POST',body:JSON.stringify({goal:$('goal').value,inventory_text:$('inventory').value,inventory_format:$('format').value,inject_failure:$('fault').checked,model:$('model').value})});
    notice('Investigation queued. You can inspect saved runs while it works.');await selectRun(result.run_id);showTab('timeline');$('workspace').scrollIntoView({behavior:'smooth'});
  }catch(e){notice(e.message,true);}finally{button.disabled=false;}
};
$('example').onclick=async()=>{try{const data=await api('/api/example');$('inventory').value=data.text;$('format').value=data.format;$('fileLabel').firstChild.textContent='Fictional PAN-OS inventory loaded';$('inventoryDetails').open=true;notice('Synthetic example loaded: three assets, one CVE, three version outcomes.');}catch(e){notice(e.message,true);}};
$('file').onchange=async e=>{const file=e.target.files[0];if(!file)return;if(file.size>50000){notice('Inventory must be smaller than 50 KB.',true);return;}$('inventory').value=await file.text();$('format').value=file.name.toLowerCase().endsWith('.csv')?'csv':'json';$('fileLabel').firstChild.textContent=file.name;notice('Inventory loaded. Review the goal, then start the investigation.');};
$('rerun').onclick=()=>{
  if(!selectedData)return;$('goal').value=selectedData.goal;
  let context=selectedData.context;
  if(!context){const source=selectedData.report?.evidence.find(e=>e.tool==='read_context_file')?.data;if(source)context={origin:source.origin,notes:source.notes,assets:source.assets};}
  $('inventory').value=context?JSON.stringify(context,null,2):'';$('format').value='json';$('inventoryDetails').open=!!context;
  $('top').scrollIntoView({behavior:'smooth'});notice('Previous inputs loaded. Edit missing information, then click Investigate to create a fresh run.');
};
$('compare').onclick=async()=>{
  try{
    if(!$('before').value||$('before').value===$('after').value)throw new Error('Choose two different completed investigations.');
    const data=await api(`/api/compare?before=${encodeURIComponent($('before').value)}&after=${encodeURIComponent($('after').value)}`);
    const root=$('diff');root.className='';root.replaceChildren(node('p',data.note,'muted'));
    if(!data.changes.length)root.append(node('div','No differences in the compared source observations.','empty'));
    for(const change of data.changes){const box=node('div',undefined,'change');box.append(node('h4',`${change.cve_id}${change.asset?' / '+change.asset:''} · ${label(change.field)} · ${label(change.kind)}`));const grid=node('div',undefined,'change-grid');grid.append(node('pre',JSON.stringify(change.before,null,2)),node('pre',JSON.stringify(change.after,null,2)));box.append(grid);root.append(box);}
  }catch(e){$('diff').textContent=e.message;}
};
$('refresh').onclick=()=>loadRuns().catch(e=>notice(e.message,true));
for(const b of document.querySelectorAll('[data-tab]'))b.onclick=()=>showTab(b.dataset.tab);
for(const a of document.querySelectorAll('nav a'))a.onclick=()=>{for(const n of document.querySelectorAll('nav a'))n.classList.remove('active');a.classList.add('active');};
async function init(){
  try{const config=await api('/api/config');$('connection').textContent=config.key_configured?'API configured · local':'API key needed';$('model').value=config.model;await loadRuns();await loadTasks();if(currentRuns.length)await selectRun(currentRuns[0].run_id);}
  catch(e){notice(e.message,true);$('connection').textContent='Connection issue';}
}
setInterval(async()=>{try{if(selectedData&&active(selectedData.status)){await loadDetail();await loadRuns();}}catch(e){notice(e.message,true);}},2000);
init();
