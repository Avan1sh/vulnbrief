"""Validated JSON/CSV inventory and narrowly supported version comparisons."""
import csv
import io
import json
import re
from pathlib import Path

from .models import Context


def load_context(path: Path) -> tuple[Context, bytes]:
    if path.stat().st_size > 50_000:
        raise ValueError("Context file exceeds 50 KB")
    raw = path.read_bytes()
    if path.suffix.lower() == ".csv":
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        rows = list(reader)
        allowed = {"label","cve_id","exposure","business_importance","product_version","product","owner","origin","notes"}
        if set(reader.fieldnames or []) - allowed:
            raise ValueError("CSV contains unsupported columns")
        origins = {r.get("origin") or "user_supplied" for r in rows}
        if len(origins) != 1:
            raise ValueError("CSV must have one consistent origin")
        assets = [{k:(v or None) if k in {"product_version","product","owner"} else v for k,v in r.items() if k not in {"origin","notes"}} for r in rows]
        context = Context.model_validate({"origin":next(iter(origins)),"notes":rows[0].get("notes", "CSV inventory; asset assertions are user supplied"),"assets":assets})
    else:
        context = Context.model_validate_json(raw)
    return context, raw


def numeric_version(text):
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:-h(\d+))?", text.strip())
    if not match:
        raise ValueError("Only numeric major.minor.patch and PAN-OS -hN hotfix versions are supported")
    return tuple(int(x or 0) for x in match.groups())


def row_version_status(row, version):
    """Compare explicit vendor table constraints within the same patch branch.

    This does not infer that a later unlisted branch is fixed, interpret SemVer
    prereleases, or compare distro/backport versions.
    """
    value = numeric_version(version)
    candidates = set()
    if row["affected"].strip().lower() == "none" and row["unaffected"].strip().lower() == "all":
        return "not_affected_by_version"
    for field, result in (("affected","potentially_affected"),("unaffected","not_affected_by_version")):
        for condition in row[field].split(","):
            match = re.fullmatch(r"\s*(>=|<=|>|<|=)?\s*(\d+\.\d+\.\d+(?:-h\d+)?)\s*", condition)
            if not match:
                continue
            boundary = numeric_version(match[2])
            if boundary[:3] != value[:3]:
                continue
            op = match[1] or "="
            matches = {"<":value<boundary, "<=":value<=boundary, ">":value>boundary, ">=":value>=boundary, "=":value==boundary}[op]
            if matches:
                candidates.add(result)
    return candidates.pop() if len(candidates)==1 else "unverified"


def assess_inventory(context, evidence):
    results = []
    for asset in context.assets:
        result = {**asset.model_dump(), "status":"unverified", "basis":[],
                  "reason":"Product, installed version and a supported vendor version table are required",
                  "required_information":[]}
        if not asset.product:
            result["required_information"].append("product")
        if not asset.product_version:
            result["required_information"].append("product_version")
        if (asset.product or "").casefold() == "pan-os" and asset.product_version:
            try:
                version=numeric_version(asset.product_version)
                matches=[]
                for e in evidence:
                    if e.tool!="get_vendor_advisory" or asset.cve_id not in e.cve_ids:
                        continue
                    for i,row in enumerate(e.data.get("product_status", [])):
                        if row["product"].casefold() != f"pan-os {version[0]}.{version[1]}":
                            continue
                        matches.append(row_version_status(row,asset.product_version))
                        result["basis"].append({"evidence_id":e.evidence_id,"field_path":f"/product_status/{i}"})
                if matches and len(set(matches))==1:
                    result["status"]=matches[0]
                    result["reason"]="Compared the supplied version with explicit vendor table constraints in the same patch branch"
                else:
                    result["reason"]="No matching vendor table, or source version assessments conflict"
                if result["status"]=="potentially_affected":
                    result["required_information"].append("Verify advisory configuration prerequisites on this asset")
            except ValueError as exc:
                result["reason"]=str(exc)
        elif asset.product and not asset.product_version:
            result['reason']='Installed version is missing; version applicability cannot be established'
        elif asset.product:
            result["reason"]="Version applicability support is currently limited to PAN-OS numeric/hotfix versions"
        if result["status"]=="unverified" and not result["required_information"]:
            result["required_information"].append("Check exact version/configuration against current vendor guidance")
        results.append(result)
    return results
