import json
import pytest

from vulnbrief.inventory import load_context, row_version_status, assess_inventory
from vulnbrief.models import Context, Evidence
from vulnbrief.vendor import parse_palo_advisory

ROW={'product':'PAN-OS 11.0','affected':'< 11.0.3-h10, < 11.0.4-h1','unaffected':'>= 11.0.3-h10, >= 11.0.4-h1'}


@pytest.mark.parametrize('version,expected',[('11.0.3-h9','potentially_affected'),('11.0.3-h10','not_affected_by_version'),('11.0.4','potentially_affected'),('11.0.4-h1','not_affected_by_version'),('11.0.99','unverified')])
def test_hotfix_boundary_and_unknown_branch(version,expected):
    assert row_version_status(ROW,version)==expected


def test_unsupported_version_not_guessed():
    with pytest.raises(ValueError):
        row_version_status(ROW,'11.0.4-ubuntu-backport')


def test_inventory_loads_csv_with_missing_version(tmp_path):
    p=tmp_path/'input.csv'
    p.write_text('label,cve_id,product,product_version,exposure,business_importance\na,CVE-2024-3400,PAN-OS,,Internet,High\n')
    context,_=load_context(p)
    assert context.origin=='user_supplied'
    assert context.assets[0].product_version is None
    result=assess_inventory(context,[])[0]
    assert result['status']=='unverified' and 'product_version' in result['required_information']


def test_vendor_parser_uses_page_table_and_patch_values():
    html='<h2>CVE-2024-3400 example</h2><p>Updated 2026-11-17</p><h3>Product Status</h3><table><tr><td>PAN-OS 11.0</td><td>&lt; 11.0.4-h1</td><td>&gt;= 11.0.4-h1</td></tr></table><h3>Solution</h3><p>Fixed in 11.0.4-h1.</p><h3>Other</h3>'
    d=parse_palo_advisory(html,'CVE-2024-3400')
    assert d['fixed_version_candidates']==['11.0.4-h1']
    assert d['updated_at']=='2026-11-17'
    assert d['product_status'][0]['affected']=='< 11.0.4-h1'


def test_conflicting_vendor_tables_produce_unverified():
    context=Context.model_validate({'origin':'synthetic','notes':'test','assets':[{'label':'a','cve_id':'CVE-2024-3400','exposure':'Internet','business_importance':'High','product':'PAN-OS','product_version':'11.0.4'}]})
    def evidence(i,row):
        return Evidence(evidence_id=i,tool='get_vendor_advisory',cve_ids=['CVE-2024-3400'],source_url='https://vendor.invalid',retrieved_at='2026-11-17',source_date=None,location='vendor',data={'product_status':[row]})
    a=evidence('E001',ROW)
    b=evidence('E002',{'product':'PAN-OS 11.0','affected':'None','unaffected':'All'})
    assert assess_inventory(context,[a,b])[0]['status']=='unverified'
