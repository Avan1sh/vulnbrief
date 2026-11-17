"""Read-only live tools. Failed retrieval is an observation, never a negative fact."""
import hashlib
import json
import re
import time
from pathlib import Path

import httpx
from pydantic import ValidationError

from .models import Context, CveArgs, CvesArgs, Evidence, KevArgs, NoArgs, utc_now
from .inventory import load_context, assess_inventory

KEV_URLS = {
    "primary": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    "official_mirror": "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json",
}
SPECS = {
    "read_context_file": (NoArgs, "Read the explicitly selected context file. No arbitrary paths accepted."),
    "get_cve_record": (CveArgs, "Retrieve a live CVE Program/CNA record, NOT NVD. An official_mirror is available if primary fails."),
    "lookup_kev": (KevArgs, "Look up CVEs in a live CISA KEV catalog. Absence is not proof of safety."),
    "get_epss": (CvesArgs, "Retrieve live FIRST EPSS scores. Missing scores remain unknown, not zero."),
    "get_vendor_advisory": (CvesArgs, "Fetch current PAN-OS vendor advisories referenced by retrieved CVE records. Includes version table, fixed-version candidates, dates and a short solution excerpt. Unsupported vendors return a typed gap."),
    "assess_assets": (NoArgs, "Compare the selected inventory to retrieved vendor version tables. Read context and fetch vendor advisory first. Supports PAN-OS numeric/hotfix versions; uncertain applicability stays unverified."),
    "finish_investigation": (NoArgs, "Finish gathering evidence and generate the report, including any unresolved gaps."),
}


def tool_definitions() -> list[dict]:
    return [{"type": "function", "function": {"name": name, "description": desc,
             "parameters": model.model_json_schema()}} for name, (model, desc) in SPECS.items()]


class ToolFault(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False, injected: bool = False):
        super().__init__(message)
        self.code, self.retryable, self.injected = code, retryable, injected


class ToolKit:
    def __init__(self, context_path: Path | None = None, inject_failure: bool = False,
                 client: httpx.Client | None = None):
        self.context_path = context_path.resolve() if context_path else None
        self.inject_failure = inject_failure
        self.fault_used = False
        self.client = client or httpx.Client(timeout=12, follow_redirects=False,
                                            headers={"User-Agent": "VulnBrief/0.1 (public-data-research)"})
        self.evidence: list[Evidence] = []
        self.errors: list[dict] = []
        self.catalogs: dict = {}  # Within-run cache, never bundled/static lookup answers.
        self.allowed_cves: set[str] = set()
        self.context: Context | None = None

    def close(self):
        self.client.close()

    def failure(self, tool, arguments, code, message, retryable=False, injected=False):
        error = {"error_id": f"ERR{len(self.errors)+1:03d}", "tool": tool,
                 "arguments": arguments, "code": code, "message": message,
                 "retryable": retryable, "injected": injected, "occurred_at": utc_now()}
        self.errors.append(error)
        return {"ok": False, "error": error}

    def _json(self, url: str, deadline: float):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ToolFault("budget_exhausted", "Run deadline reached")
        try:
            with self.client.stream("GET", url, timeout=min(12, remaining)) as response:
                response.raise_for_status()
                body = bytearray()
                for chunk in response.iter_bytes():
                    if time.monotonic() >= deadline:
                        raise ToolFault("budget_exhausted", "Run deadline reached during download")
                    body.extend(chunk)
                    if len(body) > 5_000_000:
                        raise ToolFault("response_too_large", "Response exceeded 5 MB")
                value = json.loads(body)
                if not isinstance(value, dict):
                    raise ToolFault("invalid_response", "Expected a JSON object")
                return value, utc_now()
        except httpx.TimeoutException as exc:
            raise ToolFault("timeout", "Public source timed out; retry or select an official mirror", True) from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            raise ToolFault(f"http_{status}", f"Public source returned HTTP {status}", status == 429 or status >= 500) from exc
        except httpx.RequestError as exc:
            raise ToolFault("network_error", "Public source could not be reached", True) from exc
        except (ValueError, UnicodeError) as exc:
            raise ToolFault("invalid_json", "Public source returned invalid JSON") from exc

    def _record(self, tool, cves, url, retrieved_at, source_date, location, data):
        evidence = Evidence(evidence_id=f"E{len(self.evidence) + 1:03d}", tool=tool,
                            cve_ids=cves, source_url=url, retrieved_at=retrieved_at,
                            source_date=source_date, location=location, data=data)
        self.evidence.append(evidence)
        return {"ok": True, "evidence": evidence.model_dump()}

    def invoke(self, name: str, arguments: dict, deadline: float) -> dict:
        try:
            if name not in SPECS or name == "finish_investigation":
                raise ToolFault("invalid_tool", "Unknown data tool")
            args = SPECS[name][0].model_validate(arguments)
            cves = ([args.cve_id] if isinstance(args, CveArgs) else
                    args.cve_ids if isinstance(args, CvesArgs) else [])
            if any(cve not in self.allowed_cves for cve in cves):
                raise ToolFault("out_of_scope", "Use only CVEs from the user goal or selected context file")
            if name == "read_context_file":
                return self._context()
            if name == "get_cve_record":
                return self._cve(args, deadline)
            if name == "lookup_kev":
                return self._kev(args, deadline)
            if name == "get_vendor_advisory":
                return self._vendor(args, deadline)
            if name == "assess_assets":
                return self._assets()
            return self._epss(args, deadline)
        except ValidationError:
            return self.failure(name, arguments, "invalid_arguments", "Arguments do not match the published tool schema")
        except ToolFault as exc:
            return self.failure(name, arguments, exc.code, str(exc), exc.retryable, exc.injected)
        except (KeyError, TypeError, IndexError, AttributeError, ValueError):
            return self.failure(name, arguments, "invalid_response", "Source JSON failed structural validation")

    def _context(self):
        if not self.context_path:
            raise ToolFault("no_context", "No context file selected; use the goal and disclose missing asset context")
        try:
            context, raw = load_context(self.context_path)
        except (OSError, ValueError, ValidationError) as exc:
            raise ToolFault("invalid_context", "Cannot read context file or it does not match the documented schema") from exc
        cves = list(dict.fromkeys(a.cve_id for a in context.assets))
        if len(self.allowed_cves | set(cves)) > 3:
            raise ToolFault("scope_limit", "Goal plus context exceed three CVEs")
        self.allowed_cves.update(cves)
        self.context = context
        data = context.model_dump()
        data["sha256"] = hashlib.sha256(raw).hexdigest()
        return self._record("read_context_file", cves, "input://selected-context", utc_now(), None, "user_input", data)

    def _assets(self):
        if not self.context:
            raise ToolFault("context_required", "Call read_context_file first; no inventory has been loaded")
        assessments = assess_inventory(self.context, self.evidence)
        return self._record("assess_assets", sorted({a.cve_id for a in self.context.assets}),
                            "derived://selected-inventory-and-vendor-tables", utc_now(), None, "derived",
                            {"assessments":assessments,"note":"Version match is not an asset scan; potentially affected requires configuration verification"})

    def _vendor(self, args, deadline):
        # The adapter deliberately supports one source family. No model-provided
        # URL or arbitrary redirects, preventing source-text URL injection.
        if len(args.cve_ids)!=1:
            raise ToolFault("single_cve_required", "Fetch one vendor advisory per call")
        cve=args.cve_ids[0]
        url=f"https://security.paloaltonetworks.com/{cve}"
        records=[e for e in self.evidence if e.tool=='get_cve_record' and cve in e.cve_ids]
        if not any(url in e.data.get('references',[]) for e in records):
            raise ToolFault("unsupported_vendor", "Retrieve a CVE record with an exact supported Palo Alto advisory reference first")
        from .vendor import parse_palo_advisory
        remaining=deadline-time.monotonic()
        if remaining<=0:
            raise ToolFault("budget_exhausted","Run deadline reached")
        try:
            with self.client.stream('GET',url,timeout=min(12,remaining)) as response:
                response.raise_for_status()
                body=bytearray()
                for chunk in response.iter_bytes():
                    if time.monotonic()>=deadline or len(body)+len(chunk)>2_000_000:
                        raise ToolFault("response_limit","Vendor response exceeded time or size budget")
                    body.extend(chunk)
            data=parse_palo_advisory(body.decode('utf-8'),cve)
        except httpx.HTTPStatusError as exc:
            raise ToolFault(f'http_{exc.response.status_code}','Vendor advisory request failed') from exc
        except httpx.RequestError as exc:
            raise ToolFault('network_error','Vendor advisory unavailable',True) from exc
        except ValueError as exc:
            raise ToolFault('invalid_advisory',str(exc)) from exc
        return self._record('get_vendor_advisory',[cve],url,utc_now(),data['updated_at'],'vendor',data)

    def _cve(self, args: CveArgs, deadline):
        if self.inject_failure and not self.fault_used and args.source == "primary":
            self.fault_used = True
            raise ToolFault("timeout", "Deliberately injected one-shot primary CVE timeout; retry or choose official_mirror", True, True)
        _, year, number = args.cve_id.split("-")
        bucket = f"{int(number) // 1000}xxx"
        url = (f"https://cveawg.mitre.org/api/cve/{args.cve_id}" if args.source == "primary" else
               f"https://raw.githubusercontent.com/CVEProject/cvelistV5/main/cves/{year}/{bucket}/{args.cve_id}.json")
        raw, retrieved = self._json(url, deadline)
        metadata = raw["cveMetadata"]
        if metadata["cveId"] != args.cve_id or metadata["state"] not in {"PUBLISHED", "REJECTED", "RESERVED"}:
            raise ToolFault("invalid_record", "Record identifier or status did not match request")
        cna = raw.get("containers", {}).get("cna", {})
        data = {"cve_id": args.cve_id, "record_state": metadata["state"],
                "descriptions": [d["value"][:1600] for d in cna.get("descriptions", []) if d.get("lang", "").startswith("en")][:1],
                "affected": cna.get("affected", [])[:3], "metrics": cna.get("metrics", [])[:2],
                "references": [r["url"] for r in cna.get("references", [])][:8]}
        data["affected_entries_omitted"] = max(0, len(cna.get("affected", [])) - 3)
        # Bound complex version trees without treating truncated content as complete.
        encoded = json.dumps(data["affected"])
        if len(encoded) > 3500:
            data["affected"] = []
            data["affected_detail_omitted"] = "Version tree too large; consult the cited source before deciding applicability"
        return self._record("get_cve_record", [args.cve_id], url, retrieved,
                            metadata.get("dateUpdated"), args.source, data)

    def _kev(self, args: KevArgs, deadline):
        if args.source not in self.catalogs:
            raw, retrieved = self._json(KEV_URLS[args.source], deadline)
            entries = raw["vulnerabilities"]
            if not isinstance(entries, list) or raw["count"] != len(entries) or not entries:
                raise ToolFault("invalid_catalog", "KEV catalog is incomplete or structurally invalid")
            index = {entry["cveID"]: entry for entry in entries}
            if len(index) != len(entries):
                raise ToolFault("invalid_catalog", "Duplicate KEV identifiers")
            self.catalogs[args.source] = (raw, index, retrieved)
        raw, index, retrieved = self.catalogs[args.source]
        results = []
        for cve in args.cve_ids:
            entry = index.get(cve)
            results.append({"cve_id": cve, "status": "present" if entry else "not_present",
                            "entry": entry})
        return self._record("lookup_kev", args.cve_ids, KEV_URLS[args.source], retrieved,
                            raw["dateReleased"], args.source,
                            {"catalog_version": raw["catalogVersion"], "results": results})

    def _epss(self, args: CvesArgs, deadline):
        url = "https://api.first.org/data/v1/epss?cve=" + ",".join(args.cve_ids)
        raw, retrieved = self._json(url, deadline)
        if raw.get("status") != "OK" or not isinstance(raw.get("data"), list):
            raise ToolFault("invalid_epss", "EPSS API did not return a successful data list")
        index = {}
        for row in raw["data"]:
            if row["cve"] not in args.cve_ids or row["cve"] in index:
                raise ToolFault("invalid_epss", "Unexpected or duplicate CVE in EPSS response")
            score, percentile = float(row["epss"]), float(row["percentile"])
            if not (0 <= score <= 1 and 0 <= percentile <= 1) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date"]):
                raise ToolFault("invalid_epss", "Invalid EPSS value or date")
            index[row["cve"]] = {"cve_id": row["cve"], "score": score, "percentile": percentile, "date": row["date"]}
        results = [index.get(cve, {"cve_id": cve, "score": None, "percentile": None,
                                 "date": None, "status": "no_score_returned"}) for cve in args.cve_ids]
        dates = sorted({r["date"] for r in results if r["date"]})
        return self._record("get_epss", args.cve_ids, url, retrieved, ",".join(dates) or None,
                            "primary", {"results": results})
