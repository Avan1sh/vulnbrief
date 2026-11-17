"""Local SQLite run history, action drafts and source-observation deltas."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .models import utc_now


def task_drafts(report):
    tasks=[]
    context=[a for e in report.get('evidence',[]) if e['tool']=='read_context_file' for a in e['data']['assets']]
    assessments={(a['label'],a['cve_id']):a for a in report.get('asset_assessments',[])}
    for f in (report.get('analysis') or {}).get('findings',[]):
        assets=[a for a in context if a['cve_id']==f['cve_id']] or [{'label':'Unspecified asset','owner':None}]
        for asset in assets:
            assessment=assessments.get((asset['label'],f['cve_id']),{})
            if assessment.get('status')=='not_affected_by_version':
                continue
            for index,action in enumerate(f['recommended_actions']):
                if not isinstance(action,dict):
                    continue  # Legacy reports have no field-level action evidence.
                identity=f"{report['run_id']}:{f['cve_id']}:{asset['label']}:{index}"
                tasks.append({'task_id':hashlib.sha256(identity.encode()).hexdigest()[:20],
                    'run_id':report['run_id'],'cve_id':f['cve_id'],'asset':asset['label'],
                    'owner':asset.get('owner') or 'Unassigned','priority':f['priority'],
                    'action':action['text'],'applies_when':action['applies_when'],'support':action['support'],
                    'source_links':list(dict.fromkeys(e['source_url'] for ref in action['support'] for e in report.get('evidence',[]) if e.get('evidence_id')==ref['evidence_id'] and e.get('source_url','').startswith('https://'))),
                    'applicability':assessment.get('status','unverified'),'status':'draft',
                    'review_note':'','updated_at':utc_now()})
    return tasks


def observed_state(report):
    state={}
    for e in report.get('evidence',[]):
        for cve in e['cve_ids']:
            item=state.setdefault(cve,{'kev':None,'epss':None,'vendor':None})
            if e['tool']=='lookup_kev':
                item['kev']=next((r['status'] for r in e['data']['results'] if r['cve_id']==cve),None)
            elif e['tool']=='get_epss':
                row=next((r for r in e['data']['results'] if r['cve_id']==cve),{})
                item['epss']={k:row.get(k) for k in ('score','percentile','date')}
            elif e['tool']=='get_vendor_advisory':
                item['vendor']={k:e['data'].get(k) for k in ('updated_at','fixed_version_candidates','product_status')}
    return state


def compare_reports(before,after):
    old,new=observed_state(before),observed_state(after)
    changes=[]
    for cve in sorted(old.keys()|new.keys()):
        for category in ('kev','epss','vendor'):
            left,right=old.get(cve,{}).get(category),new.get(cve,{}).get(category)
            if left!=right:
                changes.append({'cve_id':cve,'field':category,'before':left,'after':right,
                                'kind':'observation_gap' if left is None or right is None else 'value_changed'})
    old_assets={(a['label'],a['cve_id']):a for a in before.get('asset_assessments',[])}
    new_assets={(a['label'],a['cve_id']):a for a in after.get('asset_assessments',[])}
    for key in sorted(old_assets.keys()|new_assets.keys()):
        previous,asset=old_assets.get(key),new_assets.get(key)
        left={k:previous.get(k) for k in ('status','product_version')} if previous else None
        right={k:asset.get(k) for k in ('status','product_version')} if asset else None
        if left!=right:
            changes.append({'asset':key[0],'cve_id':key[1],'field':'asset_version_assessment',
                            'before':left,'after':right,'kind':'observation_gap' if left is None or right is None else 'value_changed'})
    return {'before_run':before['run_id'],'after_run':after['run_id'],'changes':changes,
            'note':'Observation differences only; a failed/missing lookup is not proof that a vulnerability disappeared.'}


class History:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, goal TEXT NOT NULL,
                    status TEXT NOT NULL, model TEXT NOT NULL, directory TEXT NOT NULL,
                    report TEXT, error TEXT, context TEXT);
                CREATE TABLE IF NOT EXISTS tasks (task_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, payload TEXT NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=20)
        db.row_factory=sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def create(self,run_id,goal,directory,context=None,model=''):
        with self.connect() as db:
            db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?)',
                       (run_id,utc_now(),goal,'queued',model,str(directory),None,None,json.dumps(context)))

    def set_status(self,run_id,status,error=None):
        with self.connect() as db:
            db.execute('UPDATE runs SET status=?,error=? WHERE run_id=?',(status,error,run_id))

    def save(self,report,directory,context=None):
        with self.connect() as db:
            db.execute('''INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET
                status=excluded.status,model=excluded.model,report=excluded.report,directory=excluded.directory,error=NULL''',
                (report['run_id'],report['created_at'],report['goal'],report['status'],report['model'],str(directory),json.dumps(report),None,json.dumps(context)))
            for task in task_drafts(report):
                db.execute('INSERT OR IGNORE INTO tasks VALUES (?,?,?)',(task['task_id'],report['run_id'],json.dumps(task)))

    def list(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT run_id,created_at,goal,status,model,error FROM runs ORDER BY created_at DESC LIMIT 200')]

    def get(self,run_id):
        with self.connect() as db:
            row=db.execute('SELECT * FROM runs WHERE run_id=?',(run_id,)).fetchone()
        if not row:
            raise KeyError(run_id)
        data=dict(row)
        data['report']=json.loads(data['report']) if data['report'] else None
        data['context']=json.loads(data['context']) if data['context'] else None
        return data

    def tasks(self,run_id=None):
        with self.connect() as db:
            rows=db.execute('SELECT payload FROM tasks'+(' WHERE run_id=?' if run_id else ''),(run_id,) if run_id else ()).fetchall()
        return [json.loads(r[0]) for r in rows]

    def review_task(self,task_id,status,note,owner):
        if status not in {'draft','accepted','dismissed'}:
            raise ValueError('Unsupported review status')
        with self.connect() as db:
            row=db.execute('SELECT payload FROM tasks WHERE task_id=?',(task_id,)).fetchone()
            if not row:
                raise KeyError(task_id)
            task=json.loads(row[0]);task.update(status=status,review_note=note,owner=owner,updated_at=utc_now())
            db.execute('UPDATE tasks SET payload=? WHERE task_id=?',(json.dumps(task),task_id))
        return task

    def recover_interrupted(self):
        with self.connect() as db:
            db.execute("UPDATE runs SET status='interrupted',error='Local server restarted; use Re-run to start a fresh investigation' WHERE status IN ('running','queued')")
