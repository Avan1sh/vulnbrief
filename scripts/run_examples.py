"""Execute the labeled scenarios against real APIs. No simulated LLM mode."""
import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
scenarios = json.loads((BASE / "examples/scenarios.json").read_text(encoding="utf-8"))
for scenario in scenarios:
    command = [sys.executable, "-m", "vulnbrief", "run", scenario["goal"],
               "--output", "artifacts/final-" + scenario["id"], "--max-seconds", "600"]
    if scenario["context"]:
        command += ["--context", scenario["context"]]
    if scenario["fault"]:
        command += ["--inject-failure", scenario["fault"]]
    print("Starting real scenario:", scenario["id"], flush=True)
    outcome = subprocess.run(command, cwd=BASE)
    print("Scenario",scenario["id"],"exit code:",outcome.returncode,flush=True)
    if outcome.returncode not in (0, 2):
        raise SystemExit(outcome.returncode)
