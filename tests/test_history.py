import copy
import json
from vulnbrief.history import History, compare_reports, task_drafts


def sample():
    return {'run_id':'test-run','created_at':'2026-11-17T10:00:00+00:00','goal':'Synthetic history fixture','model':'TEST_DOUBLE','status':'partial',
            'analysis':{'findings':[{'cve_id':'CVE-2024-3400','priority':'high','recommended_actions':[{'text':'Verify version','applies_when':'Before changing the asset','support':[{'evidence_id':'E001','field_path':'/assets/0'}]}]}]},
            'evidence':[{'evidence_id':'E001','tool':'read_context_file','cve_ids':['CVE-2024-3400'],'data':{'assets':[{'label':'edge','cve_id':'CVE-2024-3400','owner':'Infrastructure'}]}},
                        {'tool':'get_epss','cve_ids':['CVE-2024-3400'],'data':{'results':[{'cve_id':'CVE-2024-3400','score':None,'percentile':None,'date':None}]}}],
            'asset_assessments':[{'label':'edge','cve_id':'CVE-2024-3400','status':'unverified','product_version':None}]}


def test_reviews_persist_and_import_is_idempotent(tmp_path):
    h=History(tmp_path/'history.db');r=sample();h.save(r,tmp_path/'run')
    t=h.tasks()[0];h.review_task(t['task_id'],'accepted','Checked applicability','Alice')
    h.save(r,tmp_path/'run')
    assert len(h.tasks())==1 and h.tasks()[0]['status']=='accepted'
    assert History(tmp_path/'history.db').tasks()[0]['owner']=='Alice'


def test_unaffected_versions_do_not_generate_change_drafts():
    r=sample();r['asset_assessments'][0]['status']='not_affected_by_version'
    assert task_drafts(r)==[]


def test_comparison_keeps_missing_data_distinct_from_zero():
    old=sample();new=copy.deepcopy(old);new['run_id']='new';new['evidence'][1]['data']['results'][0]['score']=0.0
    change=compare_reports(old,new)['changes'][0]
    assert change['before']['score'] is None and change['after']['score']==0


def test_restart_marks_in_progress_runs_interrupted(tmp_path):
    h=History(tmp_path/'history.db');h.create('x','Synthetic test',tmp_path/'x')
    h.recover_interrupted();assert h.get('x')['status']=='interrupted'


def test_new_asset_observation_is_a_gap_not_a_claim_of_new_exposure():
    before=sample();after=copy.deepcopy(before);before['asset_assessments']=[]
    changes=compare_reports(before,after)['changes']
    assert len(changes)==1 and changes[0]['kind']=='observation_gap'
