/* Local workbench. All model/source text is rendered with textContent. */
import {kevSummary, executionPhase} from './view-model.mjs';
const $ = id => document.getElementById(id);
let selected = null, selectedData = null, currentRuns = [], events = [], lastTaskState = '';
let demos = [], polling = false, tourIndex = -1, inspectorRequest = 0;
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
  for(const b of document.querySelectorAll('[data-tab]')) {
    const chosen=b.dataset.tab===name;b.classList.toggle('selected',chosen);
    b.setAttribute('aria-selected',String(chosen));b.tabIndex=chosen?0:-1;
  }
  for(const id of ['findings','evidence','timeline'])$(id).classList.toggle('hidden',id!==name);
}
function refButtons(refs, claim=''){
  const root=node('div',undefined,'refs');
  for(const ref of refs){
    const id=typeof ref==='string'?ref:ref.evidence_id;
    const text=typeof ref==='string'?ref:`${id}:${ref.field_path}`;
    const b=node('button',text,'ref'); b.title='Inspect original source observation';
    b.onclick=()=>openInspector({evidence_id:id,field_path:typeof ref==='string'?'':ref.field_path},claim);
    root.append(b);
  }
  return root;
}
async function loadRuns(){
  currentRuns=await api('/api/runs');
  renderRuns();
  for(const id of ['before','after']){
    const previous=$(id).value;$(id).replaceChildren();
    for(const run of currentRuns.filter(r=>!active(r.status))){ const option=node('option',`${run.run_id} · ${label(run.status)}`);option.value=run.run_id;$(id).append(option); }
    if([...$(id).options].some(o=>o.value===previous))$(id).value=previous;
  }
  if(!$('before').dataset.initialized && $('before').options.length>1){$('before').selectedIndex=1;$('before').dataset.initialized='1';}
}
function renderRuns(){
  $('runList').replaceChildren();
  const filter=$('historyFilter').value;
  const runs=currentRuns.filter(r=>filter==='all'||(filter==='failed'?['failed','interrupted'].includes(r.status):r.status===filter));
  if(!runs.length)$('runList').append(node('div','No investigations match this view. Start with a goal or select another filter.','empty'));
  for(const run of runs){
    const b=node('button',undefined,`run-item${run.run_id===selected?' selected-run':''}`);
    b.setAttribute('aria-pressed',String(run.run_id===selected));
    const head=node('div');head.append(node('strong',run.run_id),badge(run.status));
    b.append(head,node('p',run.goal),node('time',when(run.created_at)));b.onclick=()=>selectRun(run.run_id);$('runList').append(b);
  }
}
async function selectRun(id){
  selected=id;events=[];lastTaskState='';
  await Promise.all([loadRuns(),loadDetail()]);
  const url=new URL(location.href);url.searchParams.set('run',id);window.history.replaceState({},'',url);
  renderDemoSelection();
}
async function loadDetail(){
  if(!selected)return;
  const id=selected,data=await api(`/api/runs/${encodeURIComponent(id)}`);
  if(id!==selected)return;
  selectedData=data;
  const report=data.report;
  const demo=demos.find(d=>d.run_id===id);
  $('runTitle').textContent=demo?.title||data.run_id;
  $('runOrigin').textContent=demo?'RECORDED REAL INVESTIGATION':'INVESTIGATION DETAIL';
  $('runMeta').textContent=`${data.run_id} · ${when(data.created_at)} · ${data.goal}`;
  $('statStatus').textContent=label(data.status);
  $('statModel').textContent=data.model||'Model assigned when run starts';
  $('rerun').disabled=active(data.status);
  $('download').classList.toggle('disabled',!report);
  $('download').setAttribute('aria-disabled',String(!report));
  $('download').href=`/api/runs/${encodeURIComponent(id)}/download/report`;
  const incremental=await api(`/api/runs/${encodeURIComponent(id)}/events?after=${events.at(-1)?.sequence||0}`);
  if(id!==selected)return;
  const seen=new Set(events.map(e=>e.sequence));events.push(...incremental.filter(e=>!seen.has(e.sequence)));renderEvents();
  const assets=report?.asset_assessments||[];
  $('statAssets').textContent=report?(assets.length?String(assets.length):'Not assessed'):'—';
  const kev=kevSummary(report);$('statKev').textContent=kev.value;$('statKevDetail').textContent=kev.detail;
  const phase=executionPhase(data.status,events);$('phaseName').textContent=label(phase.name);$('phaseDetail').textContent=phase.detail;
  $('execution').classList.toggle('is-running',active(data.status));
  const metrics=report?.metrics;
  $('runMetrics').textContent=metrics?`${metrics.tool_calls} tool attempts · ${metrics.total_tokens.toLocaleString()} tokens · ${Math.round(metrics.elapsed_seconds)}s`:`${events.filter(e=>e.event==='tool_start').length} tool attempts observed`;
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
  if(report.analysis?.summary?.length){
    const summary=node('div',undefined,'report-summary');summary.append(node('h3','Investigation brief'));
    for(const claim of report.analysis.summary){const p=node('div');p.append(node('p',claim.text),refButtons(claim.field_refs||claim.evidence_ids,claim.text));summary.append(p);}
    root.append(summary);
  }
  if(report.asset_assessments?.length){
    const wrap=node('div',undefined,'asset-table'),table=node('table');
    const header=node('tr');for(const h of ['ASSET / OWNER','PRODUCT VERSION','VERSION ASSESSMENT','INFORMATION NEEDED'])header.append(node('th',h));table.append(header);
    for(const a of report.asset_assessments){
      const row=node('tr'),name=node('td',a.label);name.append(node('small',a.owner||'Owner unassigned'));
      const version=node('td',`${a.product||'Product missing'} ${a.product_version||'—'}`);
      const status=node('td');status.append(badge(a.status),node('small',a.reason));
      const missing=node('td',(a.required_information||[]).join('; ')||'No version information gap');
      if(a.basis?.length)missing.append(refButtons(a.basis,`${a.label}: ${a.reason}`));
      row.append(name,version,status,missing);table.append(row);
    }
    wrap.append(table);root.append(wrap);
  }
  if(!report.analysis){root.append(node('div','This run did not produce an accepted analysis. Original observations and errors remain available.','empty'));return;}
  for(const f of [...report.analysis.findings].sort((a,b)=>a.rank-b.rank)){
    const card=node('article',undefined,'finding'),head=node('div',undefined,'finding-head');
    head.append(node('h3',`${f.rank.toString().padStart(2,'0')} / ${f.cve_id}`),node('span',`Agent priority: ${label(f.priority)}`,`badge ${f.priority}`));card.append(head);
    const metrics=report.source_facts?.[f.cve_id]?.source_severity||[];
    card.append(node('p',metrics.length?`Source severity: ${metrics.map(m=>`CVSS ${m.version} · ${m.score} · ${m.severity}`).join(' / ')}`:'No source-assigned severity metric recorded in this report.','muted'));
    card.append(node('p',f.rationale),refButtons(f.evidence_ids||[],f.rationale),node('h4','Recommended next actions'));
    for(const action of f.recommended_actions){
      const item=node('div',typeof action==='string'?action:action.text,'action');
      if(typeof action==='object'){item.append(node('small',`Applies when: ${action.applies_when}`),refButtons(action.support,action.text));}
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
    const inspect=node('button','Inspect this observation','secondary');inspect.onclick=()=>openInspector({evidence_id:e.evidence_id,field_path:''});box.append(inspect);
    const raw=node('details',undefined,'raw-observation');raw.append(node('summary','Original normalized JSON'),node('pre',JSON.stringify(e.data,null,2)));box.append(raw);root.append(box);
  }
  for(const e of report.tool_errors||[]){const box=node('details',undefined,'source');box.append(node('summary',`${e.error_id} / failed request · ${e.tool}`),node('pre',JSON.stringify(e,null,2)));root.append(box);}
}
function renderEvents(){
  const root=$('timeline');root.replaceChildren();
  if(!events.length){root.append(node('div','Waiting for the first execution event.','empty'));return;}
  for(const e of events){
    const item=node('div',undefined,'event'),head=node('h4',`${String(e.sequence).padStart(2,'0')} · ${label(e.event)}${e.tool?' / '+e.tool:''}`);
    item.dataset.event=e.event;
    head.append(node('time',when(e.time)));item.append(head);
    const details=node('details');if(e.event==='plan')details.open=true;
    details.append(node('summary',e.event==='plan'?'Plan and assumptions':'Inspect event details'),node('pre',JSON.stringify(e,null,2)));item.append(details);root.append(item);
    if(e.event==='tool_result'&&e.observation?.error){item.classList.add('error-event');item.prepend(node('span',`${e.observation.error.error_id||'Error'} · ${e.observation.error.injected?'deliberately injected':'source request failed'}`,'error-caption'));}
  }
}
async function loadTasks(){
  const tasks=await api('/api/tasks');$('railTasks').textContent=tasks.length;
  $('statTasks').textContent=tasks.filter(t=>t.run_id===selected).length;
  const visible=$('allTasks').checked?tasks:tasks.filter(t=>t.run_id===selected);
  $('taskExport').href='/api/tasks-export'+($('allTasks').checked||!selected?'':`?run_id=${encodeURIComponent(selected)}`);
  const root=$('taskList');root.replaceChildren();
  if(!visible.length){root.append(node('div','No action drafts in this view. Version-unaffected assets do not receive remediation drafts.','empty'));return;}
  for(const task of visible){
    const row=node('article',undefined,'task'),body=node('div');
    body.append(node('h3',`${task.asset} / ${task.cve_id}`),node('div',task.action),node('p',`Prerequisites: ${task.applies_when}`),node('p',`${label(task.applicability)} · Agent priority: ${task.priority} · ${task.run_id}`));
    const support=node('p',task.support.map(r=>`${r.evidence_id}:${r.field_path}`).join(', '));body.append(support);
    const inspect=node('button','Inspect linked investigation ↗','link-button');inspect.onclick=async()=>{await selectRun(task.run_id);showTab('evidence');$('workspace').scrollIntoView({behavior:'smooth'});};body.append(inspect);
    const assignment=node('div'),owner=node('input');owner.value=task.owner;owner.maxLength=120;owner.id=`owner-${task.task_id}`;
    const note=node('textarea');note.value=task.review_note;note.maxLength=1500;note.placeholder='Review note';note.setAttribute('aria-label',`Review note for ${task.asset}`);
    note.id=`note-${task.task_id}`;const ownerLabel=node('label','Owner');ownerLabel.htmlFor=owner.id;const noteLabel=node('label','Review note');noteLabel.htmlFor=note.id;assignment.append(ownerLabel,owner,noteLabel,note);
    const controls=node('div'),select=node('select');
    for(const status of ['draft','accepted','dismissed']){const option=node('option',label(status));option.value=status;select.append(option);}select.value=task.status;
    select.id=`review-${task.task_id}`;const statusLabel=node('label','Draft status');statusLabel.htmlFor=select.id;
    const save=node('button','Save review','secondary');save.onclick=async()=>{try{await api(`/api/tasks/${task.task_id}`,{method:'PATCH',body:JSON.stringify({status:select.value,owner:owner.value,review_note:note.value})});save.textContent='Saved ✓';setTimeout(()=>save.textContent='Save review',1800);}catch(e){notice(e.message,true);}};
    controls.append(statusLabel,select,save,node('p','Review only. No change is executed.'));
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
$('historyFilter').onchange=renderRuns;
$('allTasks').onchange=()=>loadTasks().catch(e=>notice(e.message,true));
for(const b of document.querySelectorAll('[data-tab]')){
  b.onclick=()=>showTab(b.dataset.tab);
  b.onkeydown=e=>{
    const tabs=[...document.querySelectorAll('[data-tab]')];let next=tabs.indexOf(b);
    if(e.key==='ArrowRight')next=(next+1)%tabs.length;
    else if(e.key==='ArrowLeft')next=(next+tabs.length-1)%tabs.length;
    else if(e.key==='Home')next=0;else if(e.key==='End')next=tabs.length-1;else return;
    e.preventDefault();showTab(tabs[next].dataset.tab);tabs[next].focus();
  };
}
for(const a of document.querySelectorAll('nav a'))a.onclick=()=>{for(const n of document.querySelectorAll('nav a'))n.classList.remove('active');a.classList.add('active');};

async function loadDemos(){
  demos=await api('/api/demonstrations');const root=$('demoCards');root.replaceChildren();
  if(!demos.length){root.append(node('div','No recorded examples are installed in this directory. Use the source repository to review the included demonstrations, or start a live run.','empty'));$('tour').disabled=true;return;}
  for(const demo of demos){
    const b=node('button',undefined,'demo-card');b.dataset.demo=demo.run_id;
    const top=node('div',undefined,'demo-top');top.append(node('span',demo.number,'demo-number'),node('span','RECORDED RUN','record-label'));
    const bottom=node('div',undefined,'demo-bottom');bottom.append(node('time',`Recorded ${when(demo.recorded_at)}`),node('span','Open investigation ↗'));
    b.append(top,node('h3',demo.title),node('p',demo.description),bottom);
    b.onclick=async()=>{try{await selectRun(demo.run_id);showTab(demo.focus);$('workspace').scrollIntoView({behavior:'smooth',block:'start'});}catch(e){notice(e.message,true);}};
    root.append(b);
  }
  $('tour').disabled=demos.length!==3;renderDemoSelection();
}
function renderDemoSelection(){
  for(const b of document.querySelectorAll('[data-demo]')){const chosen=b.dataset.demo===selected;b.classList.toggle('selected-demo',chosen);b.setAttribute('aria-pressed',String(chosen));}
}
function sourceLink(url,text){
  if(!url?.startsWith('https://'))return node('span',url||'Local or derived observation');
  const a=node('a',text||url);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;
}
async function openInspector(ref,claim=''){
  const request=++inspectorRequest,dialog=$('evidenceDialog'),body=$('inspectorBody');
  body.replaceChildren(node('p','Loading original source field…','muted'));
  if(!dialog.open)dialog.showModal();
  try{
    const e=await api(`/api/runs/${encodeURIComponent(selected)}/evidence/${encodeURIComponent(ref.evidence_id)}?field_path=${encodeURIComponent(ref.field_path||'')}`);
    if(request!==inspectorRequest||!dialog.open)return;
    body.replaceChildren();
    if(claim){const box=node('div',undefined,'claim-context');box.append(node('h3','Selected claim or assessment'),node('p',claim));body.append(box);}
    const meta=node('dl',undefined,'evidence-meta');
    for(const [title,value] of [['Evidence',`${e.evidence_id} · ${label(e.tool)}`],['Source location',label(e.location)],['Retrieved at',e.retrieved_at],['Source date',e.source_date||'Not supplied'],['CVE scope',e.cve_ids.join(', ')||'Selected inventory']]){
      const row=node('div');row.append(node('dt',title),node('dd',value));meta.append(row);
    }
    body.append(meta,sourceLink(e.source_url,'Open the original source ↗'));
    const field=node('div',undefined,'exact-field');field.append(node('h3','Exact cited field'),node('code',e.field_path||'(entire observation)'));
    const value=node('pre',JSON.stringify(e.value,null,2));value.id='inspectedValue';field.append(value);
    if(e.value===null)field.append(node('p','The source returned null. This is missing information, not a zero value.','null-note'));
    body.append(field);
    if(e.linked_claims.length){const linked=node('div',undefined,'linked-claims');linked.append(node('h3','Report text citing this field'));
      for(const c of e.linked_claims){linked.append(node('p',c.text));if(c.applies_when)linked.append(node('small',`Applies when: ${c.applies_when}`));}body.append(linked);}
  }catch(e){body.replaceChildren(node('p',e.message,'error-message'));}
}
$('closeInspector').onclick=()=>$('evidenceDialog').close();
$('evidenceDialog').addEventListener('click',e=>{if(e.target===$('evidenceDialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}});

const tourSteps=[
  {title:'Start with a real investigation',text:'This recorded run used live public sources and a fictional inventory. Three asset versions produce different, source-driven outcomes. No new LLM request is made during this tour.',run:'v02-reviewed',tab:'findings',target:'workspace'},
  {title:'Follow a recommendation to its source',text:'Open a citation to see the exact source value, retrieval time and linked action. Close the inspector to continue. A citation is inspectable support, not a guarantee of correctness.',run:'v02-reviewed',tab:'findings',target:'workspace',inspect:true},
  {title:'See recovery in the execution trace',text:'The primary CVE request deliberately timed out. The subsequent model decision selected an official mirror. ERR request failures and successful E observations remain separate.',run:'v02-recovery-final',tab:'timeline',target:'workspace',error:true},
  {title:'Keep missing information visible',text:'This test CVE was intentionally unavailable. The report stays partial, and the absent EPSS score remains unknown. Catalog absence does not prove safety.',run:'v02-partial-final',tab:'findings',target:'workspace'},
  {title:'Review the next step',text:'Conditional actions become local reviewable drafts with an owner and supporting evidence. Accepting a draft records review only; it does not change a device or create an external ticket.',run:'v02-reviewed',tab:'findings',target:'actions'},
  {title:'Run your own investigation',text:'Choose a goal, load a fictional CSV or JSON inventory and select a configured model. A new live investigation uses fresh sources and your API quota. Nothing starts automatically.',target:'compose'}
];
async function showTour(index){
  const step=tourSteps[index];if(!step)return;
  tourIndex=index;$('tourPanel').hidden=false;$('tourStep').textContent=`GUIDED REVIEW · ${index+1} / ${tourSteps.length}`;
  $('tourTitle').textContent=step.title;$('tourText').textContent=step.text;
  $('tourPrevious').disabled=index===0;$('tourNext').textContent=index===tourSteps.length-1?'Finish tour':'Next →';
  $('tourNext').disabled=true;
  try{
    if($('evidenceDialog').open)$('evidenceDialog').close();
    if(step.run&&selected!==step.run)await selectRun(step.run);
    if(step.tab)showTab(step.tab);
    $(step.target).scrollIntoView({behavior:'smooth',block:'start'});
    if(step.error){const error=document.querySelector('.error-event');if(error){error.querySelector('details').open=true;error.scrollIntoView({behavior:'smooth',block:'center'});}}
    if(step.inspect){const action=selectedData?.report?.analysis?.findings?.[0]?.recommended_actions?.find(a=>typeof a==='object'&&a.support?.length);if(action)await openInspector(action.support[0],action.text);}
  }catch(e){notice(e.message,true);}finally{$('tourNext').disabled=false;}
}
function closeTour(){tourIndex=-1;$('tourPanel').hidden=true;$('tour').focus();}
$('tour').onclick=()=>showTour(0);
$('closeTour').onclick=closeTour;
$('tourPrevious').onclick=()=>showTour(tourIndex-1);
$('tourNext').onclick=()=>tourIndex===tourSteps.length-1?closeTour():showTour(tourIndex+1);
async function init(){
  try{const config=await api('/api/config');$('connection').textContent=config.key_configured?'API configured · local':'Recorded runs available';$('model').value=config.model;
    await Promise.all([loadDemos(),loadRuns()]);
    const requested=new URL(location.href).searchParams.get('run');
    const initial=currentRuns.find(r=>r.run_id===requested)?.run_id||demos[0]?.run_id||currentRuns[0]?.run_id;
    if(initial)await selectRun(initial);else await loadTasks();
    if(!config.key_configured)notice('Recorded examples need no API key. Configure GROQ_API_KEY locally before starting a new live run.');
  }
  catch(e){notice(e.message,true);$('connection').textContent='Connection issue';}
}
setInterval(async()=>{if(polling)return;polling=true;try{if(selectedData&&active(selectedData.status)){await loadDetail();await loadRuns();}}catch(e){notice(e.message,true);}finally{polling=false;}},2000);
init();
