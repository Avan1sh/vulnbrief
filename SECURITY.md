# Security scope

VulnBrief 0.2 is a single-user localhost prototype. It has no enterprise identity,
tenant separation, or production hardening. Keep it bound to `127.0.0.1`; do not
publish the server through a tunnel or expose it as a shared service.

The application performs bounded read-only public-data requests. Task acceptance
records local analyst review and does not apply a patch or create an external
ticket. Model output and retrieved text remain untrusted; field validation and
LLM review do not prove every recommendation is correct or prevent every prompt
injection.

Inventory and goals are sent to the configured LLM provider. Use fictional or
non-sensitive data for demonstrations. `.env`, runtime SQLite databases, uploaded
inputs, and private runs are ignored by Git and excluded from the source package.
The public `artifacts/` directory contains reviewed demonstration evidence.

## Reporting a vulnerability

Do not disclose credentials, private inventories, or an unpatched security issue
in a public issue. Contact the maintainer through their
[GitHub profile](https://github.com/Avan1sh) to arrange a private report. Include a
minimal reproduction with synthetic data and the affected commit. There is no
formal response-time or supported-version commitment for this prototype.
