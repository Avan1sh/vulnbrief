"""Capture updated recovery and missing-data demonstrations using real APIs."""
import subprocess
import sys
from pathlib import Path

base=Path(__file__).resolve().parents[1]
scenarios=[
    ('v02-recovery-final','Investigate CVE-2024-3400 using live CVE, KEV, EPSS and supported vendor guidance. Recover from failed requests, distinguish ERR errors from successful E evidence, and produce two conditional actions with exact supporting source fields. Use the exact version_citations for any named version. No asset inventory was supplied.',True),
    ('v02-partial-final','Investigate CVE-2099-9999999, an intentionally unavailable test identifier. Check live CVE, KEV and EPSS tools. Produce an honest partial report with exact source-field references. Missing scores stay unknown, not zero. Do not invent vulnerability details or fixed versions.',False)]
for name,goal,fault in scenarios:
    command=[sys.executable,'-m','vulnbrief','run',goal,'--model','openai/gpt-oss-20b','--output','artifacts/'+name]
    if fault:command+=['--inject-failure','cve-primary-timeout-once']
    print('Starting',name,flush=True)
    result=subprocess.run(command,cwd=base)
    print(name,'exit code',result.returncode,flush=True)
    if result.returncode not in (0,2):raise SystemExit(result.returncode)
