from types import SimpleNamespace

import httpx
import pytest
from groq import RateLimitError

from vulnbrief.llm import GroqLLM, ProviderFailure
from vulnbrief.trace import Trace


def test_rate_limit_retry_is_bounded_and_does_not_log_provider_body(tmp_path, monkeypatch):
    monkeypatch.setattr('vulnbrief.llm.time.sleep', lambda _: None)
    llm = GroqLLM('test-only-not-a-real-key', 'TEST', Trace(tmp_path / 'retry', True), min_interval=0)
    attempts = []
    def limited(**kwargs):
        attempts.append(kwargs)
        response = httpx.Response(429, headers={'retry-after':'0'}, request=httpx.Request('POST','https://api.groq.com/test'))
        raise RateLimitError('PROVIDER_BODY_NOT_FOR_TRACE', response=response, body={})
    monkeypatch.setattr(llm.client.chat.completions,'create',limited)
    with pytest.raises(ProviderFailure, match='rate limit'):
        llm._request([], __import__('time').monotonic()+100)
    assert len(attempts) == 2
    assert 'PROVIDER_BODY_NOT_FOR_TRACE' not in (tmp_path/'retry'/'events.jsonl').read_text()
    llm.close()


def test_text_finish_discards_unvalidated_draft(tmp_path, monkeypatch):
    llm = GroqLLM('test-only', 'TEST', Trace(tmp_path / 'finish', True), min_interval=0)
    monkeypatch.setattr(llm, '_request', lambda *a, **kw: SimpleNamespace(content='UNVALIDATED_FACTS', tool_calls=[]))
    result = llm.decide([], [], 100)
    assert result['tool_calls'] == []
    assert 'UNVALIDATED_FACTS' not in result['content']
    llm.close()
