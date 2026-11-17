# v0.3 verification record

The v0.2 browser check was blocked by its Computer Use active-URL confidence
check. v0.3 uses an isolated, development-only Playwright Chromium instance with
a fresh profile against the localhost QA server. It does not operate the user's
personal browser session. No screenshot or demo output was generated with AI.

## Completed checks

- Python/API regressions: see `tests/test-results.txt`.
- Eight Node presentation tests cover missing/partial/conflicting KEV observations,
  successful evidence after a failure, and runtime phase labels.
- Nine browser tests cover actual retained-run navigation, no new LLM calls during
  the tour, exact citation inspection, Escape/focus return, keyboard tabs, retained
  failures, mobile dialog size, and the unknown-KEV regression.
- The same nine checks also passed against a separately installed 0.3.0 wheel on
  the normal localhost dashboard port; package dependencies passed `pip check`.
- Automated axe WCAG A/AA-tagged checks passed on the loaded findings page at
  1440, 768 and 390 CSS pixels, and inside the mobile citation dialog.
- Real screenshots of the workbench, investigation, inspector and phone page were
  captured and visually inspected. Screenshot files are in `docs/screenshots/`.
- A genuine silent 90-second browser walkthrough opens the same retained runs.
  `artifacts/demo-recording.json` records its provenance and scene times. It starts
  zero new LLM investigations. The large video is a separate release asset.
- The refreshed design PDF remains one A4 page and was rendered and inspected.

The checks exposed Windows serving `.mjs` as text/plain and insufficient contrast
in table headings. Both were fixed before the passing run. Earlier failed test
artifacts remain in the ignored local browser-test output; the public report
records the final run.

## Reproduce

Install the Python package and Node 24+, activate that Python virtual environment,
then run from `ui-tests/`:

```text
npm ci
npx playwright install chromium
npm run test:logic
npm test
```

Playwright starts a localhost server automatically unless an existing QA server
is available. On Linux CI, use `npx playwright install --with-deps chromium`.
`npm run capture` records genuine UI screenshots and the video. The tools are
development dependencies; the application itself needs no Node runtime.

## Boundaries

Automated scans do not prove complete accessibility. Browser tests use Chromium,
not every engine or assistive technology. The loaded page contains public CVE
observations and fictional assets. UI/API checks exercise navigation and contracts;
they do not prove semantic claim accuracy or real device applicability. Repeated
live evaluations have a separate quota-bounded report and are not triggered by CI.
