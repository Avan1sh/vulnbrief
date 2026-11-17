import time
import json
from fastapi.testclient import TestClient
from vulnbrief.server import create_app
from test_history import sample


def test_api_runs_history_task_review_and_downloads(tmp_path):
    def runner(run_id,request,context,directory):
        directory.mkdir(parents=True)
        report=sample();report['run_id']=run_id
        (directory/'report.json').write_text(json.dumps(report))
        (directory/'report.md').write_text('Synthetic test-only report')
        return report
    app=create_app(tmp_path,tmp_path/'state',runner=runner)
    with TestClient(app) as client:
        assert client.get('/').status_code==200
        assert 'javascript' in client.get('/view-model.mjs').headers['content-type']
        response=client.post('/api/runs',json={'goal':'Synthetic test goal'})
        assert response.status_code==202
        run_id=response.json()['run_id']
        for _ in range(50):
            result=client.get(f'/api/runs/{run_id}').json()
            if result['report']:break
            time.sleep(.01)
        assert result['report'] is not None
        assert 'directory' not in result
        task=client.get('/api/tasks').json()[0]
        assert client.patch('/api/tasks/'+task['task_id'],json={'status':'accepted','owner':'Analyst','review_note':'Reviewed'}).status_code==200
        assert client.get('/api/tasks-export').status_code==200
        assert client.get(f'/api/runs/{run_id}/download/json').json()['run_id']==run_id
        assert client.get(f'/api/runs/{run_id}/download/secrets').status_code==404
        assert client.get('/api/runs/unknown').status_code==404


def test_rejects_cross_origin_and_invalid_inventory(tmp_path):
    app=create_app(tmp_path,tmp_path/'state',runner=lambda *a:None)
    with TestClient(app) as client:
        assert client.post('/api/runs',headers={'origin':'https://example.com'},json={'goal':'Synthetic goal'}).status_code==403
        assert client.post('/api/runs',json={'goal':'Synthetic goal','inventory_text':'{"GROQ_API_KEY":"not an inventory"}'}).status_code==422
        assert client.post('/api/runs',json={'goal':'Synthetic goal','model':'unknown-model'}).status_code==422


def test_inspector_api_preserves_null_and_rejects_missing_fields(tmp_path):
    app=create_app(tmp_path,tmp_path/'state',runner=lambda *a:None)
    report=sample()
    report['evidence']=[{'evidence_id':'E001','tool':'get_epss','cve_ids':['CVE-2024-3400'],
        'source_url':'https://api.first.org/data/v1/epss','retrieved_at':'2026-11-17T00:00:00Z',
        'source_date':None,'location':'primary','data':{'results':[{'score':None},{'score':0.0}]}}]
    app.state.history.save(report,tmp_path/'recorded')
    with TestClient(app) as client:
        path='/api/runs/test-run/evidence/E001'
        assert client.get(path,params={'field_path':'/results/0/score'}).json()['value'] is None
        assert client.get(path,params={'field_path':'/results/1/score'}).json()['value']==0.0
        assert client.get(path,params={'field_path':'/invented'}).status_code==404
        assert client.get(path,params={'field_path':'not/a/pointer'}).status_code==422
        assert client.get('/api/runs/unknown/evidence/E001').status_code==404
