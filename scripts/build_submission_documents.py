"""Package retained assessment evidence as three upload-ready PDFs.

Requires documentation-only reportlab, pypdf and Pillow plus the Windows Segoe UI
and Consolas fonts. Uses no LLM calls,
fabricated traces, private runtime state or provider credentials.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
from textwrap import wrap
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Image, KeepTogether, LongTable, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle, XPreformatted,
)

BASE = Path(__file__).resolve().parents[1]
DEST = BASE / "docs/submission"
OUTPUT = BASE.parent / "output/pdf/assessment-uploads"
DATE = "18 November 2026"
COMMIT = "e7fcfed647013c670279084089c6e77b8821b8bb"
REPO = "https://github.com/Avan1sh/vulnbrief"
FROZEN = REPO + "/blob/" + COMMIT + "/"
IST = timezone(timedelta(hours=5, minutes=30))
SELECTED = [
    ("D01", "v02-reviewed", "Asset investigation"),
    ("D02", "v02-recovery-final", "Injected timeout recovery"),
    ("D03", "v02-partial-final", "Unavailable record and score"),
]
INK = colors.HexColor("#1d3029")
GREEN = colors.HexColor("#17654f")
MUTED = colors.HexColor("#52655c")
PALE = colors.HexColor("#edf3ec")
RULE = colors.HexColor("#d5dfd5")
WIDTH = 595.276 - 88


def text(value):
    value = str(value).translate(str.maketrans({c: "-" for c in "\u2010\u2011\u2012\u2013\u2014\u2212"}))
    return escape(value)


def load(path):
    return json.loads((BASE / path).read_text(encoding="utf-8"))


def events(path):
    return [json.loads(line) for line in (BASE / path).read_text(encoding="utf-8").splitlines()]


def sha(path):
    return hashlib.sha256((BASE / path).read_bytes()).hexdigest()


def local_time(value, clock_only=False):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(IST)
    return dt.strftime("%H:%M:%S") if clock_only else dt.strftime("%d %b %Y %H:%M:%S IST")


for name, filename in [("Body", "segoeui.ttf"), ("BodyBold", "segoeuib.ttf"),
                        ("Mono", "consola.ttf"), ("MonoBold", "consolab.ttf")]:
    pdfmetrics.registerFont(TTFont(name, "C:/Windows/Fonts/" + filename))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold", italic="Body", boldItalic="BodyBold")
pdfmetrics.registerFontFamily("Mono", normal="Mono", bold="MonoBold", italic="Mono", boldItalic="MonoBold")
STYLES = {
    "title": ParagraphStyle("Title", fontName="BodyBold", fontSize=25, leading=30, textColor=INK, spaceAfter=14),
    "subtitle": ParagraphStyle("Subtitle", fontName="Body", fontSize=11, leading=16, textColor=MUTED, spaceAfter=14),
    "h1": ParagraphStyle("Section", fontName="BodyBold", fontSize=15, leading=20, textColor=GREEN, spaceBefore=12, spaceAfter=9, keepWithNext=True),
    "h2": ParagraphStyle("Subsection", fontName="BodyBold", fontSize=11, leading=15, textColor=INK, spaceBefore=9, spaceAfter=5, keepWithNext=True),
    "body": ParagraphStyle("BodyText", fontName="Body", fontSize=10, leading=14.5, textColor=INK, spaceAfter=8),
    "small": ParagraphStyle("Small", fontName="Body", fontSize=8.5, leading=12, textColor=MUTED, spaceAfter=6, wordWrap="CJK"),
    "cell": ParagraphStyle("Cell", fontName="Body", fontSize=8.2, leading=11, textColor=INK, wordWrap="CJK"),
    "head": ParagraphStyle("HeadCell", fontName="BodyBold", fontSize=8, leading=11, textColor=GREEN, wordWrap="CJK"),
    "mono": ParagraphStyle("Code", fontName="Mono", fontSize=8, leading=10.8, textColor=INK, backColor=colors.HexColor("#f4f6f1"), borderPadding=8, spaceAfter=9),
}


def p(value, style="body"):
    return Paragraph(text(value).replace("\n", "<br/>"), STYLES[style])


def link(label, target, style="small"):
    return Paragraph('<link href="' + escape(target, {'"': '&quot;'}) + '" color="#17654f">' + text(label) + "</link>", STYLES[style])


def h(value, level=1):
    return p(value, "h1" if level == 1 else "h2")


def bullets(items):
    return [Paragraph("&#8226; " + text(item), STYLES["body"]) for item in items]


def table(headers, rows, widths, small=False):
    data = [[p(c, "head") for c in headers]]
    data += [[c if isinstance(c, Paragraph) else p(c, "cell") for c in row] for row in rows]
    t = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("LINEBELOW", (0, 0), (-1, 0), .8, RULE),
        ("LINEBELOW", (0, 1), (-1, -1), .35, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6 if not small else 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6 if not small else 2),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafbf8")]),
    ]))
    return t


def cover(title, field):
    return [
        p("VULNBRIEF  |  ASSESSMENT EVIDENCE", "small"),
        p(title, "title"),
        p("Prepared by Avanish for the Agentic AI Engineer Intern assessment\nXiarch Bharat Pvt Limited | " + DATE, "subtitle"),
        p("Form field: " + field, "body"),
        p("Project release 0.3.0. Recorded evidence is from 17 November 2026. "
          "This document packages existing artifacts; it does not claim a new live run on the preparation date."),
        link("Source repository and release", REPO + "/releases/tag/v0.3.0"),
    ]


class Pages(canvas.Canvas):
    def __init__(self, *args, short_title="", **kwargs):
        super().__init__(*args, **kwargs)
        self.saved = []
        self.short_title = short_title

    def showPage(self):
        self.saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self.saved)
        for state in self.saved:
            self.__dict__.update(state)
            self.setStrokeColor(RULE)
            self.setLineWidth(.5)
            self.line(44, 43, 551, 43)
            self.setFont("Body", 8)
            self.setFillColor(MUTED)
            self.drawString(44, 29, "VulnBrief | " + self.short_title)
            self.drawRightString(551, 29, f"{self._pageNumber} / {total}")
            super().showPage()
        super().save()


def build(name, short_title, story, attachments):
    DEST.mkdir(parents=True, exist_ok=True)
    raw = io.BytesIO()
    doc = SimpleDocTemplate(raw, pagesize=(595.276, 841.89), leftMargin=44, rightMargin=44,
        topMargin=43, bottomMargin=58, title="VulnBrief " + short_title, author="Avanish")
    doc.build(story, canvasmaker=lambda *a, **kw: Pages(*a, short_title=short_title, **kw))
    writer = PdfWriter()
    writer.clone_document_from_reader(PdfReader(io.BytesIO(raw.getvalue())))
    for filename, data in attachments.items():
        writer.add_attachment(filename, data)
    writer.add_metadata({"/Author": "Avanish", "/Subject": "Assessment evidence compiled " + DATE,
                         "/Keywords": "VulnBrief, agentic AI, assessment, actual traces"})
    path = DEST / name
    with path.open("wb") as handle:
        writer.write(handle)
    reader = PdfReader(path)
    assert all(reader.attachments[k][0] == value for k, value in attachments.items())
    assert path.stat().st_size < 10_000_000
    assert all(page.extract_text().strip() for page in reader.pages)
    print(json.dumps({"file": name, "pages": len(reader.pages), "bytes": path.stat().st_size,
                      "embedded_evidence_files": len(attachments)}))
    return path


def attach_files(paths):
    return {str(path).replace("/", "__"): (BASE / path).read_bytes() for path in paths}


def evidence_index(story, paths):
    story += [h("Original evidence and integrity"),
        p("Readable tables in this PDF summarize the payloads. Full original files are embedded as PDF "
          "attachments and linked below at the frozen source commit. Some browser PDF viewers hide embedded files; "
          "open the original PDF in a reader that supports attachments or follow the repository links. "
          "Hashes identify the embedded files; Git can normalize text line endings in the linked web copies."),
        p("Source commit " + COMMIT, "small")]
    for path in paths:
        story += [KeepTogether([link(path, FROZEN + path), p("Embedded file SHA256 " + sha(path), "small")])]


def event_description(e):
    kind = e["event"]
    if kind == "run_started":
        result = f"Goal received. context_selected={e.get('context_selected')}; fault_mode={e.get('fault_mode')}"
    elif kind == "plan":
        result = f"Public plan: {len(e.get('steps', []))} steps, {len(e.get('assumptions', []))} assumptions. See preceding plan."
    elif kind == "decision":
        calls = [c["function"]["name"] + " " + c["function"]["arguments"] for c in e.get("tool_calls", [])]
        result = " | ".join(calls) or "Model finished tool selection; structured report stage follows."
    elif kind == "tool_start":
        result = e["tool"] + " " + json.dumps(e.get("arguments", {}), separators=(",", ":"))
    elif kind == "tool_result":
        obs = e["observation"]
        if not obs["ok"]:
            err = obs["error"]
            result = f"{e['tool']}: {err.get('error_id')} {err['code']}; injected={err.get('injected', False)}. {err['message']}"
        elif obs.get("evidence"):
            v = obs["evidence"]
            result = f"{e['tool']}: {v['evidence_id']}, {v['location']}; scope={','.join(v['cve_ids'])}; source date={v['source_date'] or 'not supplied'}"
        else:
            result = e["tool"] + ": " + obs.get("message", "completed")
    elif kind == "llm_usage":
        result = f"Provider call {e.get('call')}: {e.get('total_tokens')} total tokens."
    elif kind == "report_review":
        result = f"accepted={e.get('accepted')}; issues=" + json.dumps(e.get("issues", []))
    elif kind == "report_rejected":
        result = "Validation issues: " + " | ".join(e.get("errors", []))
    elif kind == "run_finished":
        result = "Final runtime status: " + e["status"]
    else:
        result = "; ".join(f"{k}={v}" for k, v in e.items() if k not in {"sequence", "time", "event"})
    return result[:330] + (" [payload continues in original log]" if len(result) > 330 else "")


def sample_runs():
    story = cover("Sample Run Transcripts and Logs", "Sample Run Transcripts/Logs")
    story += [h("What the three samples demonstrate"),
        p("The selected records use genuine Groq model calls and public source requests. Inventory and test goals "
          "are fictional. D02 deliberately injects one primary-source timeout. No private model reasoning is "
          "requested or stored; public plans, selected functions, observations and review events are preserved."),
        table(["ID and run", "Runtime status", "Tool attempts\nfailures", "LLM calls", "Tokens", "Seconds"],
              [[f"{sid}\n{name}", load(f"artifacts/{name}/report.json")["status"],
                f"{load(f'artifacts/{name}/report.json')['metrics']['tool_calls']} / {load(f'artifacts/{name}/report.json')['metrics']['tool_failures']}",
                load(f"artifacts/{name}/report.json")["metrics"]["llm_calls"],
                f"{load(f'artifacts/{name}/report.json')['metrics']['total_tokens']:,}",
                load(f"artifacts/{name}/report.json")["metrics"]["elapsed_seconds"]] for sid, name, _ in SELECTED],
              [151, 67, 74, 54, 74, 87]),
        Spacer(1, 12),
        p("These are retained v0.2 executions, distributed with release 0.3.0. They were not rerun after the later "
          "guard changes. Runtime complete means the original runtime accepted its report; it does not prove "
          "every natural-language claim or the safety of a particular upgrade."),
        p("The later v0.3 repeated trials, including unsuccessful outcomes, are covered in the separate labeled "
          "trace and monitoring documents. Samples are deliberately selected demonstrations, not an unbiased benchmark."),
        h("Reading the evidence", 2),
        p("Times below are IST (UTC+05:30), converted from each original UTC event. Every saved event is listed, "
          "with payload summaries for readability. Full unchanged events.jsonl, transcript.md and report.json "
          "files are embedded in this PDF and linked at the end. Source dates differ from retrieval times."),
    ]
    paths = []
    for sid, name, title in SELECTED:
        base = f"artifacts/{name}"
        r = load(base + "/report.json")
        ev = events(base + "/events.jsonl")
        paths += [base + "/" + f for f in ["events.jsonl", "transcript.md", "report.json"]]
        story += [PageBreak(), h(f"{sid}  {title}"),
            p(name + " | " + r["model"] + " | schema " + r.get("schema_version", "0.1"), "small"),
            p("Started " + local_time(ev[0]["time"]) + "\nFinished " + local_time(ev[-1]["time"]), "small"),
            h("Original user goal", 2), p(r["goal"]),
            h("Public model plan", 2), p(r["plan"]["objective"])]
        story += bullets(r["plan"]["steps"])
        story += [h("Model assumptions at planning time", 2),
                  p("These are assumptions generated before retrieval, not established source facts.", "small")]
        story += bullets(r["plan"]["assumptions"])
        story += [PageBreak(), h(sid + "  Complete event ledger"),
            p("Every saved event is present. Details are a readable summary; full payloads and call IDs remain in the embedded originals.", "small"),
            table(["Seq", "Time IST", "Event", "Observed action or result"],
                [[e["sequence"], local_time(e["time"], True), e["event"], event_description(e)] for e in ev],
                [29, 55, 85, 338], small=True),
            PageBreak(), h(sid + "  Accepted report and source observations"),
            table(["Evidence", "Tool", "Location", "Source date"],
                [[e["evidence_id"], e["tool"], e["location"], e["source_date"] or "Not supplied"] for e in r["evidence"]],
                [50, 160, 107, 190]),
            h("Original model output excerpts", 2),
            p("The text below is reproduced from the saved accepted analysis with typographic dash normalization. "
              "It is historical model output, not fresh operational advice or a guarantee of correctness.", "small")]
        for claim in r["analysis"]["summary"]:
            story += [p(claim["text"]), p("References: " + ", ".join(x["evidence_id"] + ":" + x["field_path"] for x in claim["field_refs"]), "small")]
        for finding in r["analysis"]["findings"]:
            story += [h(finding["cve_id"] + "  Agent priority " + finding["priority"], 2),
                      p("Model rationale: " + finding["rationale"])]
            for n, action in enumerate(finding["recommended_actions"], 1):
                story += [p(f"Action {n}: {action['text']}"), p("Applies when: " + action["applies_when"], "small"),
                    p("Support: " + ", ".join(x["evidence_id"] + ":" + x["field_path"] for x in action["support"]), "small")]
            story += bullets(["Uncertainty: " + value for value in finding["uncertainties"]])
        if r["asset_assessments"]:
            story += [h("Fictional inventory outcomes", 2), table(["Asset", "Supplied version", "Observed status"],
                [[a["label"], a["product_version"] or "Unknown", a["status"]] for a in r["asset_assessments"]], [147, 131, 229])]
        story += bullets(["Report limitation: " + value for value in r["analysis"]["limitations"]])
        if sid == "D02":
            story += [p("Review note: the injected ERR001 timeout precedes the next model decision and the successful E001 official-mirror retrieval. "
                "A mirror is an alternative location for the same dataset. The report's broad upgrade-range wording and mitigation recommendation still require source and applicability review.")]
        if sid == "D03":
            story += [p("Review note: the model's phrase 'No action is required' does not establish safety. "
                "The observed facts are two CVE HTTP 404 responses, no catalog match, and a null EPSS score. "
                "A missing public record or score is not evidence that an asset is unaffected.")]
    story += [PageBreak()]
    evidence_index(story, paths)
    return build("01-sample-run-transcripts-and-logs.pdf", "Sample run transcripts", story, attach_files(paths))


def trial_records():
    rows = []
    for batch, prefix in [("evaluation-v03", "E"), ("evaluation-v03-followup", "F")]:
        doc = load("artifacts/" + batch + "/summary.json")
        for i, row in enumerate(doc["trials"], 1):
            item = dict(row, trace_id=prefix + f"{i:02d}", batch=batch,
                        evidence_path="artifacts/" + batch + "/" + row["directory"],
                        runtime_fingerprint=doc["runtime_fingerprint"], bounds=doc["per_trial_bounds"])
            rows.append(item)
    return rows


def labels_doc():
    records = trial_records()
    suite = load("examples/evaluation-suite.json")
    selected_labels = [
        {"trace_id": "D01", "run_id": "v02-reviewed", "labels": ["fictional_inventory", "asset_version_assessment", "accepted_report"],
         "observed": "All six tools used; potentially affected, version-unaffected and unverified asset outcomes recorded."},
        {"trace_id": "D02", "run_id": "v02-recovery-final", "labels": ["injected_source_timeout", "model_selected_recovery", "accepted_report"],
         "observed": "ERR001 primary timeout; later model decision chooses official mirror and obtains E001."},
        {"trace_id": "D03", "run_id": "v02-partial-final", "labels": ["unavailable_test_identifier", "missing_epss", "partial_report", "residual_wording_risk"],
         "observed": "Two CVE 404s, catalog absence, null score; partial status. Some generated action wording still needs human review."},
    ]
    manifest = {"prepared_on": DATE, "source_commit": COMMIT,
        "label_authority": "Self-authored engineering expectations; no independent detector ground truth",
        "selected_demonstrations": selected_labels, "case_definitions": suite["cases"],
        "executed_trials": records, "not_run_as_named_suite_cases": [c["id"] for c in suite["cases"] if c["id"] not in {"missing_record", "unsupported_vendor", "scope_guard"}],
        "caution": "A separate demonstration can cover related behavior without constituting a run of the exact suite case. No malicious/benign classifier labels or precision/recall are asserted."}
    manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
    story = cover("Synthetic and Test Traces With Labels", "Synthetic/Test Traces Used (with labels)")
    story += [h("How the traces and labels were produced"),
        p("Synthetic goals and small fictional inventories were authored for the project. Expected behavior was "
          "specified in scenario metadata, while model responses and public source observations were obtained "
          "from actual executions. A single source-timeout fault was deliberately injected only in the recovery "
          "demonstration. No live response was replaced with a stored answer."),
        p("The v0.3 suite defines eight cases. Three cases were selected for two trials each in the first batch; "
          "the unsupported-vendor case was then attempted twice with changed guard code. That is six LLM trials "
          "and two scope checks with zero LLM calls, in addition to the three selected demonstration runs."),
        p("Unit tests separately use explicit HTTP/model doubles. They are not included in live model trial counts. "
          "Labels below describe engineering behavior, not malicious-versus-benign detector classes."),
        h("Label meanings", 2),
        table(["Label or state", "Meaning"], [
            ["PASS for a check", "The specified observable condition is satisfied in the saved trace."],
            ["FAIL for a check", "The condition is not established. A missing final report can make downstream report checks false."],
            ["Quota blocked outcome", "The provider stopped the run; this is not a semantic-quality judgment about an unproduced report."],
            ["Not run", "A case is defined but no trial of that exact case was executed in these batches."],
            ["Runtime complete", "The runtime accepted a report. This can coexist with failed evaluation criteria or a manual grounding concern."],
            ["Unverified asset", "Available inventory/vendor evidence is insufficient for the supported version comparison."],
        ], [143, 364]),
        p("Expected labels are self-authored and were not independently annotated by a SOC team. No statistical "
          "precision, recall, calibrated confidence or production reliability estimate is claimed."),
        PageBreak(), h("Labels for the selected demonstrations")]
    for item in selected_labels:
        story += [h(item["trace_id"] + "  " + item["run_id"], 2),
            p("Labels: " + ", ".join(item["labels"]), "small"), p(item["observed"]),
            link("Original events", FROZEN + "artifacts/" + item["run_id"] + "/events.jsonl")]
    story += [h("Data origin and fault disclosure", 2),
        p("Inventory asset names, owners, versions, exposure and business importance are fictional assertions. "
          "A watchlist association is not a scanner finding. CVE, KEV, EPSS and supported vendor observations were "
          "retrieved live during those runs. The unavailable CVE-2099-9999999 identifier is a deliberate test input."),
        p("D02 fault label: cve-primary-timeout-once. Only the first chosen primary CVE request is synthetically "
          "failed; subsequent source retrievals are real. The agent, rather than an automatic source substitution, "
          "selects its recovery action."),
        PageBreak(), h("Defined evaluation cases")]
    exercised = {"missing_record", "unsupported_vendor", "scope_guard"}
    story += [table(["Case", "Predefined observable expectation", "Exact suite execution"], [
        [c["id"], c["expected"].get("input_rejection") or
         "; ".join(([f"status {c['expected']['status']}"] if c["expected"].get("status") else []) +
                   (["model-selected recovery"] if c["expected"].get("recovery") else []) +
                   (["null EPSS preserved"] if c["expected"].get("missing_epss") else []) +
                   (["unverified named assets"] if c["expected"].get("unverified_assets") else []) +
                   (["requested assets assessed"] if c["expected"].get("asset_labels") else []) +
                   (["injection marker absent from analysis"] if c["expected"].get("forbidden_analysis_marker") else []) +
                   ["scoped references and requested tool coverage"]),
         "Executed; see trial table" if c["id"] in exercised else "Not run as an exact suite case"]
        for c in suite["cases"]], [119, 253, 135]),
        p("D01 and D02 demonstrate related version and recovery behavior, but they are not relabeled as executions "
          "of the later named suite cases. The full case goals, fictional input and expectations are in the embedded suite JSON."),
        PageBreak(), h("Executed trial labels and outcomes"),
        table(["Trace", "Case / trial", "Runtime status", "Checks\npassed", "Interpretation"], [
            [r["trace_id"], r["case_id"] + " / " + str(r["trial"]), r["status"],
             f"{sum(r['checks'].values())}/{len(r['checks'])}",
             "Zero LLM calls; input bound tested" if r["case_id"] == "scope_guard" else
             "Partial with absent source data preserved" if r["case_id"] == "missing_record" else
             "Quota stop before report" if r["trace_id"] == "F02" else
             "Citation validation failure after one repair" if r["trace_id"] == "F01" else
             "Skipped inventory; manual grounding concern" if r["trial"] == 1 else "Initial plan schema failure"]
            for r in records], [42, 126, 74, 67, 198]),
        h("How the checks are assigned", 2),
        p("The evaluator reads actual saved events and report fields. It checks plan-before-tools ordering, "
          "selected tool coverage, scoped output, reference validity and accepted source review. Applicable cases "
          "also check null EPSS preservation, unverified asset outcomes, or input rejection before model use. "
          "Recovery requires an injected failure, a later model decision, and a subsequent successful CVE retrieval."),
        p("It does not grade every natural-language inference. The original unsupported-vendor trial passed "
          "structural reference checks while a manual spot check found an unsupported fix inference. A quota "
          "failure leaves report-dependent checks false because the final report does not exist."),
        PageBreak(), h("Runtime separation and full trace index")]
    for batch in ["evaluation-v03", "evaluation-v03-followup"]:
        d = load("artifacts/" + batch + "/summary.json")
        story += [h(batch, 2), p("Fingerprint: " + d["runtime_fingerprint"], "small"),
            p("Bounds: " + json.dumps(d["per_trial_bounds"]) + ". Stop reason: " + (d.get("stop_reason") or "planned batch completed"), "small")]
    story += [p("The follow-up changed both runtime code and the per-trial time budget (600 seconds rather than "
                "480). Treat it as a disclosed follow-up, not a controlled causal estimate."),
              link("Manual findings and limitations", FROZEN + "docs/evaluation-findings-v03.md")]
    paths = ["examples/evaluation-suite.json", "examples/scenarios.json",
             "artifacts/evaluation-v03/summary.json", "artifacts/evaluation-v03-followup/summary.json",
             "artifacts/evaluation-runtime-provenance.json"]
    paths += [r["evidence_path"] + "/events.jsonl" for r in records]
    paths += [r["evidence_path"] + "/report.json" for r in records if (BASE / (r["evidence_path"] + "/report.json")).exists()]
    paths += ["artifacts/" + name + "/events.jsonl" for _, name, _ in SELECTED]
    evidence_index(story, paths)
    attachments = attach_files(paths)
    attachments["trace-label-manifest.json"] = manifest_bytes
    return build("02-synthetic-test-traces-with-labels.pdf", "Labeled test traces", story, attachments)


def picture(filename, max_height):
    path = BASE / "docs/screenshots" / filename
    with PILImage.open(path) as image:
        w, h0 = image.size
    scale = min(WIDTH / w, max_height / h0)
    return Image(str(path), width=w * scale, height=h0 * scale, hAlign="LEFT")


def monitoring_doc():
    story = cover("Monitoring Report and Dashboard Output", "Monitoring Report / Dashboard Output")
    story += [h("Engineering monitoring scope"),
        p("This report covers observability, test results and dashboard evidence for the Agentic AI Engineer "
          "submission. VulnBrief investigates supplied CVEs; it is not a separately trained malicious-trace "
          "detector. Precision and recall are therefore not defined for this implementation."),
        table(["Verification layer", "Recorded result", "Scope"], [
            ["Python and API", "57 passed", "Contracts, source faults, versions, citations, bounds, persistence and API behavior"],
            ["Presentation logic", "8 passed", "Unknown/conflicting KEV observations and execution-phase labels"],
            ["Browser", "9 passed", "Recorded-run tour, source inspector, keyboard/modal behavior and responsive layout"],
            ["Hosted CI", "4 jobs passed", "Ubuntu Python 3.10/3.12; Windows Python 3.10; separate browser/accessibility job"],
            ["Installed wheel", "20 files match source", "Runtime and web assets; dependency check passed; browser suite also passed against installed copy"],
        ], [115, 94, 298]),
        Spacer(1, 10),
        link("Frozen final CI result", REPO + "/actions/runs/44138588676"),
        p("Automated accessibility scans covered the findings page at 1440, 768 and 390 CSS pixels, plus the mobile "
          "citation dialog, in Chromium. This does not certify full accessibility or every browser engine."),
        h("Observations retained per investigation", 2),
        p("The runtime records public plan, selected native functions and arguments, successful E evidence, "
          "separate ERR failures, source URLs/dates, report review, elapsed time and token usage. It never "
          "requests or stores private model reasoning. Credentials, uploaded private inputs and local SQLite "
          "state are excluded from the public submission."),
        PageBreak(), h("Actual dashboard output"),
        p("Screenshot of the real local workbench, captured on 17 November 2026. The cards open dated recorded "
          "runs; opening a recorded run does not start an LLM request.", "small"),
        picture("workbench.png", 370),
        Spacer(1, 11),
        table(["Selected recorded run", "Visible output"], [
            ["v02-reviewed", "Runtime complete; 3 assets assessed; 1 CVE present in retrieved KEV data; 4 local action drafts"],
            ["Asset outcomes", "vpn-primary: potentially_affected; vpn-patched: not_affected_by_version; vpn-unknown: unverified"],
            ["Review state", "Draft acceptance records local analyst review only. No device patch, external ticket or message is executed."],
        ], [145, 362]),
        link("Full-resolution dashboard image", FROZEN + "docs/screenshots/workbench.png"),
        p("These are the captured selected-run values, not a current organization-wide inventory or a live SOC summary.", "small"),
        PageBreak(), h("Source inspection output"),
        p("The inspector shows a selected model claim next to the exact original source value. In the captured "
          "example, E005:/fixed_version_candidates/1 resolves to 11.0.4-h1. This illustrates citation inspection, "
          "not a fresh recommendation for any real device.", "small"),
        picture("evidence-inspector.png", 475),
        Spacer(1, 9),
        p("Retrieval time and source date are displayed separately. A field match makes support inspectable, "
          "but does not establish every inference, complete applicability or the safety of all future versions."),
        link("Full-resolution source inspector image", FROZEN + "docs/screenshots/evidence-inspector.png"),
        PageBreak(), h("Recorded agent telemetry"),
        table(["Selected demonstration", "Status", "Tool attempts / failures", "LLM calls", "Tokens", "Seconds"],
            [[name, load(f"artifacts/{name}/report.json")["status"],
              f"{load(f'artifacts/{name}/report.json')['metrics']['tool_calls']} / {load(f'artifacts/{name}/report.json')['metrics']['tool_failures']}",
              load(f"artifacts/{name}/report.json")["metrics"]["llm_calls"],
              f"{load(f'artifacts/{name}/report.json')['metrics']['total_tokens']:,}",
              load(f"artifacts/{name}/report.json")["metrics"]["elapsed_seconds"]] for _, name, _ in SELECTED],
            [139, 61, 92, 52, 76, 87]),
        p("Tool attempts can include failed requests and differ from distinct successful tools. Samples have different "
          "goals and coverage, so their latency/token counts are descriptive observations, not comparative performance scores."),
        h("Repeated evaluation outcomes", 2),
        table(["Batch and case", "Executed trials", "Observed outcome"], [
            ["Original missing_record", "2 LLM trials", "Both partial; all 8 applicable behavioral checks passed"],
            ["Original unsupported_vendor", "2 LLM trials", "One runtime-complete report failed 2 of 7 evaluation checks; the other failed plan schema validation"],
            ["Original scope_guard", "2 input checks", "Both rejected excessive scope before an LLM request"],
            ["Follow-up unsupported_vendor", "2 LLM trials", "Both selected six tools and assessed inventory as unverified. One report failed citation validation; one stopped on daily free-provider quota."],
        ], [157, 91, 259]),
        p("Eight scenarios are defined; only three named cases were executed in these batches. Original and "
          "follow-up runtime fingerprints and budgets are separated. No aggregate production success rate is inferred."),
        PageBreak(), h("Findings and production readiness"),
        table(["Observed issue", "Implemented response", "Remaining limitation"], [
            ["Missing KEV shown as zero", "Unknown and partial/conflicting coverage are represented explicitly", "Catalog absence itself does not prove safety"],
            ["Selected inventory skipped", "Clearer tool instructions; incomplete inventory work prevents complete status", "Model can still omit requested work and produce a partial/failed result"],
            ["Invalid initial plan", "At most one schema correction before tools execute", "Provider/protocol failures remain possible"],
            ["Affected range treated as a fix", "Common named upgrade targets require an exact current vendor candidate citation", "Lexical checks and LLM review do not prove all natural-language claims"],
            ["Unsupported-vendor follow-up", "Inventory was read and unverified assessments recorded; invalid report retained as failure", "One report still failed after citation repair; vendor/version support is narrow"],
            ["Daily quota exhausted", "Explicit quota failure with bounded provider handling", "Availability depends on account and time; recorded examples remain reviewable"],
        ], [113, 204, 190]),
        h("Operational boundaries", 2),
        p("This is a localhost, single-user prototype. It has no enterprise identity/tenant controls, complete "
          "configuration scans, checkpoint resume or autonomous patch execution. PAN-OS version comparison "
          "supports explicitly parsed table branches; other products remain unverified. Human review and current "
          "vendor guidance are required before operational decisions."),
        p("The quota stop is a recorded observation from 17 November, not a claim about current quota availability. "
          "No new provider availability check or live investigation was performed to prepare these documents."),
        link("Detailed evaluation findings", FROZEN + "docs/evaluation-findings-v03.md"),
        link("Actual 90-second silent walkthrough", REPO + "/releases/download/v0.3.0/vulnbrief-demo.webm"),
        PageBreak()]
    paths = ["artifacts/verification-v03.json", "artifacts/installation-check-v03.json", "tests/test-results.txt",
             "artifacts/browser-tests.json", "artifacts/evaluation-v03/summary.json",
             "artifacts/evaluation-v03-followup/summary.json", "artifacts/demo-recording.json"]
    evidence_index(story, paths)
    return build("03-monitoring-report-and-dashboard-output.pdf", "Monitoring and dashboard", story, attach_files(paths))


def main():
    paths = [sample_runs(), labels_doc(), monitoring_doc()]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    result = []
    for path in paths:
        target = OUTPUT / path.name
        shutil.copyfile(path, target)
        result.append({"file": path.name, "bytes": path.stat().st_size,
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                       "pages": len(PdfReader(path).pages)})
    manifest = {"prepared_on": DATE, "source_release": "0.3.0", "source_commit": COMMIT,
                "format": "PDF", "max_upload_bytes": 10_000_000, "files": result}
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
