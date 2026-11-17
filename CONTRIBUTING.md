# Contributing

VulnBrief is a local assessment prototype. Changes should keep investigative
choices with the LLM and make tool execution, evidence, errors, and uncertainty
inspectable.

## Local checks

Create a virtual environment and install `python -m pip install -e ".[dev]"`.
From that environment, run:

```text
python -m pip check
python -m pytest -q
python scripts/audit_repository.py
node --check src/vulnbrief/web/app.js
python -m build --wheel
```

The unit/API tests use explicit doubles and synthetic data. They do not require a
Groq key or make paid LLM calls. Node is used only for an optional JavaScript
syntax check; running the workbench requires no Node installation or build step.
The publication audit examines tracked files and common credential patterns; it
is not an exhaustive secret scanner.

CI runs the suite and builds a wheel on Ubuntu with Python 3.10/3.12 and Windows
with Python 3.10. Live demonstrations are reviewed separately from those checks.

The `ui-tests/` development package adds Playwright and axe checks. With Node 24+
and the Python virtual environment activated, run `npm ci`,
`npx playwright install chromium`, then `npm test` from that folder.
The config starts a local server when needed. `npm run test:logic` exercises the
pure presentation calculations. `npm run capture` records real screenshots and a
silent tour; its large video is a release asset excluded from the source ZIP.

The live evaluation harness is opt-in: `python scripts/evaluate_agent.py --help`.
It uses your configured free API quota, preserves actual failures, and does not
run during CI. Define expectations before observing results and report only the
cases/trials actually executed.

## Evidence changes

Add meaningful regression coverage when changing evidence scope, version
comparison, provider retry bounds, or task review persistence. Unknown source or
asset information must stay unknown. Never turn an existing example report into
a live response or silently rewrite a retained model result.

For a live experiment, use fictional inventory, a new output directory, and a
bounded goal. Record the actual model, sources, result, limits, and injected faults.
Do not add private inputs or credentials. API quotas are account dependent.

## Commits and review

Use focused commits with a concrete description of the behavior changed. A pull
request should explain the problem, resulting behavior, tests actually run, and
material limitations. Public sample traces contain model output and external
source observations; review both before redistribution.
