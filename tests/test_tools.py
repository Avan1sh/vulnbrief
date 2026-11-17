import json
import time

import httpx
import pytest

from vulnbrief.tools import ToolKit

CVE = "CVE-2024-3400"


def kit_for(handler, **kwargs):
    kit = ToolKit(client=httpx.Client(transport=httpx.MockTransport(handler)), **kwargs)
    kit.allowed_cves = {CVE}
    return kit


def invoke(kit, tool, args):
    return kit.invoke(tool, args, time.monotonic() + 30)


def test_missing_epss_is_not_zero():
    kit = kit_for(lambda r: httpx.Response(200, json={"status": "OK", "data": []}))
    observation = invoke(kit, "get_epss", {"cve_ids": [CVE]})
    assert observation["ok"]
    assert observation["evidence"]["data"]["results"][0]["score"] is None


@pytest.mark.parametrize("score", ["nan", "1.5", "-0.1"])
def test_invalid_epss_not_accepted(score):
    kit = kit_for(lambda r: httpx.Response(200, json={"status": "OK", "data": [
        {"cve": CVE, "epss": score, "percentile": "0.5", "date": "2026-11-17"}]}))
    assert not invoke(kit, "get_epss", {"cve_ids": [CVE]})["ok"]
    assert not kit.evidence


def test_unreachable_catalog_is_unknown_observation():
    kit = kit_for(lambda r: httpx.Response(503))
    for source in ("primary", "official_mirror"):
        observation = invoke(kit, "lookup_kev", {"cve_ids": [CVE], "source": source})
        assert observation["error"]["code"] == "http_503"
    assert not kit.evidence


def test_corrupt_catalog_cannot_establish_absence():
    kit = kit_for(lambda r: httpx.Response(200, json={"count": 1, "vulnerabilities": []}))
    assert not invoke(kit, "lookup_kev", {"cve_ids": [CVE], "source": "primary"})["ok"]


def test_catalog_fetched_once_per_source_per_run():
    calls = []
    def handler(request):
        calls.append(request.url)
        return httpx.Response(200, json={"count": 1, "catalogVersion": "fixture", "dateReleased": "2026-11-17", "vulnerabilities": [{"cveID": CVE}]})
    kit = kit_for(handler)
    for _ in range(2):
        assert invoke(kit, "lookup_kev", {"cve_ids": [CVE], "source": "primary"})["ok"]
    assert len(calls) == 1


def test_fault_reaches_model_then_next_request_is_real_transport():
    requests = []
    def handler(request):
        requests.append(str(request.url))
        return httpx.Response(200, json={"cveMetadata": {"cveId": CVE, "state": "PUBLISHED"}})
    kit = kit_for(handler, inject_failure=True)
    failed = invoke(kit, "get_cve_record", {"cve_id": CVE, "source": "primary"})
    assert failed["error"]["injected"] and not requests
    recovered = invoke(kit, "get_cve_record", {"cve_id": CVE, "source": "official_mirror"})
    assert recovered["ok"] and len(requests) == 1
    assert "/cves/2024/3xxx/" in requests[0]


def test_wrong_cve_record_rejected():
    kit = kit_for(lambda r: httpx.Response(200, json={"cveMetadata": {"cveId": "CVE-2021-44228", "state": "PUBLISHED"}}))
    assert not invoke(kit, "get_cve_record", {"cve_id": CVE, "source": "primary"})["ok"]


@pytest.mark.parametrize("payload", ["<html>outage</html>", "[]"])
def test_malformed_response_is_typed_error(payload):
    kit = kit_for(lambda r: httpx.Response(200, text=payload))
    assert not invoke(kit, "get_cve_record", {"cve_id": CVE, "source": "primary"})["ok"]


def test_context_scope_and_path_cannot_be_chosen_by_model(tmp_path):
    context = tmp_path / "input.json"
    context.write_text(json.dumps({"origin": "synthetic", "notes": "fixture", "assets": [{"label": "edge", "cve_id": CVE, "exposure": "unknown", "business_importance": "unknown"}]}))
    kit = kit_for(lambda r: httpx.Response(500), context_path=context)
    assert invoke(kit, "read_context_file", {})["ok"]
    assert not invoke(kit, "read_context_file", {"path": "other-file"})["ok"]
    assert not invoke(kit, "get_cve_record", {"cve_id": "CVE-2021-44228", "source": "primary"})["ok"]


def test_rejected_record_preserves_status():
    kit = kit_for(lambda r: httpx.Response(200, json={"cveMetadata": {"cveId": CVE, "state": "REJECTED"}}))
    result = invoke(kit, "get_cve_record", {"cve_id": CVE, "source": "primary"})
    assert result["evidence"]["data"]["record_state"] == "REJECTED"
