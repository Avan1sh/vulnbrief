import time
import httpx

from vulnbrief.tools import ToolKit
from vulnbrief.report import validate_evidence, source_facts
from test_agent import draft, CVE
from vulnbrief.models import Evidence, SourceRef


def test_failure_ids_never_consume_evidence_ids():
    kit=ToolKit(inject_failure=True, client=httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={"cveMetadata":{"cveId":CVE,"state":"PUBLISHED"}}))))
    kit.allowed_cves={CVE}
    a=kit.invoke('get_cve_record',{'cve_id':CVE,'source':'primary'},time.monotonic()+5)
    b=kit.invoke('get_cve_record',{'cve_id':CVE,'source':'official_mirror'},time.monotonic()+5)
    assert a['error']['error_id']=='ERR001'
    assert a['error']['arguments']['source']=='primary'
    assert b['evidence']['evidence_id']=='E001'
    assert b['evidence']['location']=='official_mirror'


def test_action_field_path_must_exist_and_match_cve():
    kit=ToolKit(client=httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={"cveMetadata":{"cveId":CVE,"state":"PUBLISHED"}}))))
    kit.allowed_cves={CVE}
    kit.invoke('get_cve_record',{'cve_id':CVE,'source':'primary'},time.monotonic()+5)
    report=draft()
    assert not validate_evidence(report,kit.evidence,{CVE})
    report.findings[0].recommended_actions[0].support[0].field_path='/invented_patch'
    assert validate_evidence(report,kit.evidence,{CVE})
    assert source_facts(kit.evidence)[CVE]['source_severity']==[]


def test_action_named_version_must_match_cited_value():
    kit=ToolKit(client=httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'cveMetadata':{'cveId':CVE,'state':'PUBLISHED'}}))))
    kit.allowed_cves={CVE}
    kit.invoke('get_cve_record',{'cve_id':CVE,'source':'primary'},time.monotonic()+5)
    report=draft()
    report.findings[0].recommended_actions[0].text='Upgrade to 11.0.4\u2011h1'
    assert any('not present' in e for e in validate_evidence(report,kit.evidence,{CVE}))


def test_affected_version_text_cannot_support_a_named_upgrade_target():
    evidence=[Evidence(evidence_id='E001',tool='get_cve_record',cve_ids=[CVE],
        source_url='https://example.test/cve',retrieved_at='2026-11-17T00:00:00Z',source_date=None,
        location='primary',data={'record_state':'PUBLISHED','description':'Versions before 2.15.0 are affected'})]
    report=draft();action=report.findings[0].recommended_actions[0]
    action.text='Upgrade the component to version 2.15.0';action.support[0].field_path='/description'
    assert any('lack an exact current vendor' in e for e in validate_evidence(report,evidence,{CVE}))
    evidence.append(Evidence(evidence_id='E002',tool='get_vendor_advisory',cve_ids=[CVE],
        source_url='https://example.test/vendor',retrieved_at='2026-11-17T00:00:00Z',source_date=None,
        location='vendor',data={'fixed_version_candidates':['2.15.0']}))
    action.support=[SourceRef(evidence_id='E002',field_path='/fixed_version_candidates/0')]
    assert not validate_evidence(report,evidence,{CVE})
