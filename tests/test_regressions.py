import copy
import json
import time
import httpx
import pytest
from groq import BadRequestError, RateLimitError
from types import SimpleNamespace
from vulnbrief.history import task_drafts
from vulnbrief.llm import GroqLLM,ProviderFailure
from vulnbrief.models import Context
from vulnbrief.trace import Trace
from test_history import sample


def test_same_asset_other_cve_does_not_suppress_draft():
    r=sample()
    r['asset_assessments'].append({'label':'edge','cve_id':'CVE-2021-44228','status':'not_affected_by_version'})
    assert len(task_drafts(r))==1


def test_duplicate_inventory_pairs_rejected():
    asset={'label':'edge','cve_id':'CVE-2024-3400','exposure':'Unknown','business_importance':'Unknown'}
    with pytest.raises(ValueError):
        Context.model_validate({'origin':'synthetic','notes':'test','assets':[asset,asset]})


def test_provider_schema_retry_is_bounded(tmp_path,monkeypatch):
    llm=GroqLLM('test-only','TEST',Trace(tmp_path/'trace',True),0)
    calls=[]
    def rejected(**kwargs):
        calls.append(kwargs)
        response=httpx.Response(400,json={'error':{'code':'json_validate_failed'}},request=httpx.Request('POST','https://api.groq.com/test'))
        raise BadRequestError('Failed generation not for logs',response=response,body={})
    monkeypatch.setattr(llm.client.chat.completions,'create',rejected)
    with pytest.raises(ProviderFailure):llm._request([],time.monotonic()+30)
    assert len(calls)==2
    assert 'Failed generation not for logs' not in (tmp_path/'trace/events.jsonl').read_text()
    llm.close()


def test_rate_and_protocol_errors_have_separate_bounded_retries(tmp_path,monkeypatch):
    llm=GroqLLM('test-only','TEST',Trace(tmp_path/'mixed',True),0)
    monkeypatch.setattr('vulnbrief.llm.time.sleep',lambda _:None)
    calls=[]
    def completion(**kwargs):
        calls.append(kwargs)
        request=httpx.Request('POST','https://api.groq.com/test')
        if len(calls)==1:
            raise RateLimitError('rate',response=httpx.Response(429,headers={'retry-after':'0'},request=request),body={})
        if len(calls)==2:
            raise BadRequestError('protocol',response=httpx.Response(400,json={'error':{'code':'json_validate_failed'}},request=request),body={})
        return SimpleNamespace(usage=None,choices=[SimpleNamespace(finish_reason='stop',message=SimpleNamespace(content='{}'))])
    monkeypatch.setattr(llm.client.chat.completions,'create',completion)
    assert llm._request([],time.monotonic()+60,response_format={'type':'json_object'}).content=='{}'
    assert len(calls)==3
    llm.close()
