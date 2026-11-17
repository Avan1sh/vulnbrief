"""CLI entry point. Exit codes: complete=0, partial=2, failed=1."""
import argparse
import json
import os
import time
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from pydantic import ValidationError

from .agent import Investigator
from .llm import GroqLLM, ProviderFailure
from .models import Plan
from .tools import ToolKit, tool_definitions
from .trace import Trace


def main(argv=None):
    parser = argparse.ArgumentParser(description="VulnBrief: investigate up to three CVEs using live public evidence.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Investigate a natural-language goal")
    run.add_argument("goal")
    run.add_argument("--context", type=Path)
    run.add_argument("--output", type=Path, help="New directory; existing directories are never overwritten")
    run.add_argument("--inject-failure", choices=["cve-primary-timeout-once"])
    run.add_argument("--max-seconds", type=int, default=600)
    run.add_argument("--max-rounds", type=int, default=10)
    run.add_argument("--max-tool-calls", type=int, default=20)
    run.add_argument("--quiet", action="store_true")
    run.add_argument("--model",choices=['openai/gpt-oss-120b','openai/gpt-oss-20b'])
    serve=sub.add_parser('serve',help='Open the local analyst workbench')
    serve.add_argument('--port',type=int,default=8787)
    serve.add_argument('--data',type=Path)
    sub.add_parser('history',help='List saved investigations')
    smoke = sub.add_parser("doctor", help="Verify credentials, structured output, and genuine tool calling")
    smoke.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    # Only .env in the invocation directory; do not traverse unrelated parent folders.
    load_dotenv(Path.cwd() / ".env", override=False)
    if args.command=='serve':
        import uvicorn
        from .server import create_app
        if not 1024<=args.port<=65535:
            parser.error('Port must be between 1024 and 65535')
        uvicorn.run(create_app(Path.cwd(),args.data),host='127.0.0.1',port=args.port,log_level='warning')
        return 0
    if args.command=='history':
        from .history import History
        print(json.dumps(History(Path.cwd()/'.vulnbrief/history.sqlite3').list(),indent=2))
        return 0
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        print("GROQ_API_KEY is not configured. Copy .env.example to .env and set a free Groq key.")
        return 1
    output = args.output or Path("runs") / (args.command + "-" + uuid4().hex[:10])
    try:
        trace = Trace(output, quiet=getattr(args, "quiet", False))
        interval = float(os.getenv("VULNBRIEF_MIN_REQUEST_INTERVAL", "25"))
        if not 0 <= interval <= 60:
            raise ValueError("Request interval must be between 0 and 60 seconds")
        llm = GroqLLM(key, getattr(args,'model',None) or os.getenv("VULNBRIEF_MODEL", "openai/gpt-oss-120b"), trace, interval)
        try:
            if args.command == "doctor":
                deadline = time.monotonic() + 150
                plan = llm.structured([{"role": "user", "content": "Give a concise plan to investigate one public CVE using tools. Return objective, steps and assumptions."}], Plan, deadline)
                trace.emit("smoke_structured", plan=plan.model_dump())
                decision = llm.decide([{"role": "user", "content": "Call get_cve_record for CVE-2024-3400 using primary source."}], tool_definitions(), deadline)
                if not decision["tool_calls"]:
                    raise ProviderFailure("Smoke test returned no genuine tool call")
                trace.emit("smoke_tools", tool_calls=decision["tool_calls"])
                print("Provider smoke test passed. No public data tools were executed by doctor.")
                return 0
            if not 1 <= args.max_rounds <= 12 or not 1 <= args.max_tool_calls <= 30 or not 10 <= args.max_seconds <= 600:
                raise ValueError("Bounds: rounds 1-12, tool calls 1-30, seconds 10-600")
            if len(args.goal) > 8000:
                raise ValueError("Goal exceeds 8,000 characters")
            tools = ToolKit(args.context, bool(args.inject_failure))
            try:
                result = Investigator(llm, tools, trace, args.max_rounds, args.max_tool_calls, args.max_seconds).run(args.goal)
            finally:
                tools.close()
            from .history import History
            History(Path.cwd()/'.vulnbrief/history.sqlite3').save(result,output.resolve(),tools.context.model_dump() if tools.context else None)
            print(f"{result['status']}: {output.resolve() / 'report.md'}")
            return {"complete": 0, "partial": 2, "failed": 1}[result["status"]]
        finally:
            llm.close()
    except (ValueError, OSError, ProviderFailure, ValidationError) as exc:
        message = str(exc) if not isinstance(exc, ValidationError) else "Model response failed schema validation"
        print("Error: " + message)
        return 1
