import copy
import pytest
from vulnbrief.reviewer import demonstrations, inspect_evidence
from test_history import sample


def observation(evidence_id='E001',data=None):
    return {'evidence_id':evidence_id,'tool':'get_epss','cve_ids':['CVE-2024-3400'],
            'source_url':'https://api.first.org/data/v1/epss','retrieved_at':'2026-11-17T00:00:00Z',
            'source_date':None,'location':'primary','data':data or {'results':[{'score':None}]}}


def test_inspector_resolves_original_value_and_preserves_null():
    report=sample()
    report['evidence']=[observation('E009')]
    result=inspect_evidence(report,'E009','/results/0/score')
    assert result['value'] is None
    assert result['source_date'] is None
    with pytest.raises(KeyError):inspect_evidence(report,'E009','/invented')
    with pytest.raises(KeyError):inspect_evidence(report,'ERR001')


def test_demonstrations_are_available_only_when_real_reports_exist():
    class Empty:
        def get(self,_):raise KeyError()
    assert demonstrations(Empty())==[]


def test_inspector_does_not_modify_report():
    report=sample();report['evidence']=[observation()];before=copy.deepcopy(report)
    evidence=report['evidence'][0]
    inspect_evidence(report,evidence['evidence_id'])
    assert report==before
