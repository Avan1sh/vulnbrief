# Upgrade record: v0.2

The six requested additions were implemented sequentially:

1. **Evidence handling:** separate ERR request failures from E observations; exact source-field references for actions and summaries; mandatory action prerequisites; source-assigned severity displayed separately from model priority. A concrete version named in an action must occur in its cited value, preventing a neighboring fixed-version entry from being used as support.
2. **Asset assessment:** JSON/CSV inventory with product, version, owner, exposure and importance; explicit affected/unaffected hotfix-boundary comparison for the supported PAN-OS vendor table; unknown and conflicting cases stay unverified.
3. **Current vendor guidance:** read the exact official Palo Alto advisory referenced in the retrieved CVE record; preserve its source date, current product-status table, fixed-version candidates and short solution excerpt. Other vendors are explicit gaps.
4. **Analyst interface:** local FastAPI job queue and HTML/CSS/JS workbench with input editing, live event timeline, findings, original evidence and downloads. Credentials remain server-side. Visual verification was blocked by Computer Use's active-URL policy check; this is not represented as a completed visual test.
5. **Task drafts:** field-cited conditional follow-ups, owner assignment, review status/note and CSV export. No external tickets or system changes are made. Version-unaffected assets are excluded from remediation drafts.
6. **History and differences:** local SQLite persistence, idempotent imports, retained review state, interrupted-run labeling, edit-and-rerun inputs, and comparison of source/asset observations. Missing observations are not interpreted as resolution. There is no scheduled watcher or checkpoint-based graph resume.

Verification: current pytest output is in tests/test-results.txt. API tests require loopback socket access on this Windows sandbox. The vendor/version live smoke check used the fictional inventory and returned potentially affected for `11.0.4`, version-unaffected for `11.0.4-h1`, and unverified for the missing version. This is a source-driven comparison, not a hard-coded CVE response.

The first upgraded LLM runs exposed rate limits, daily quota exhaustion and intermittent provider JSON-schema errors. Failed runs are retained. The adapter now identifies daily quota separately, paces token volume, bounds protocol corrections, and offers the smaller supported model with JSON mode plus the same local validation. Exact live outcomes are in the artifact inventory.

Private runtime state lives in `.vulnbrief/` and is excluded from packaging. Public example runs and fictional inventory are included. Source data is not replayed as a live agent response.
