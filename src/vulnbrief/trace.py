"""Append-only execution events with a readable, non-private reasoning trace."""
import json
from pathlib import Path

from .models import utc_now


class Trace:
    def __init__(self, directory: Path, quiet: bool = False):
        directory.mkdir(parents=True, exist_ok=False)
        self.directory = directory
        self.events: list[dict] = []
        self.quiet = quiet

    def emit(self, kind: str, **payload):
        event = {"sequence": len(self.events) + 1, "time": utc_now(), "event": kind, **payload}
        self.events.append(event)
        with (self.directory / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        # Rewrite after each event so an interrupted process still leaves a transcript.
        sections = ["# VulnBrief execution transcript\n", "Generated from actual runtime events.\n"]
        for entry in self.events:
            sections.append(f"## {entry['sequence']}. {entry['event']} ({entry['time']})\n")
            sections.append("```json\n" + json.dumps(entry, indent=2, ensure_ascii=False) + "\n```\n")
        (self.directory / "transcript.md").write_text("\n".join(sections), encoding="utf-8")
        if not self.quiet:
            print(f"[{event['sequence']:02d}] {kind}", flush=True)
            if kind in {"plan", "decision", "stop", "error"}:
                print(json.dumps(payload, ensure_ascii=True, indent=2), flush=True)
