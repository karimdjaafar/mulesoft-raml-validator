![RAML Validator logo](assets/logo.png)

# mulesoft-raml-validator

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.4.2-E97132.svg)](CHANGELOG.md)
[![Skill](https://img.shields.io/badge/Claude-Skill-0E2841.svg)](https://docs.claude.com/en/agents-and-tools/agent-skills/overview)

| Document | Version | Date | Author | Status |
|---|---|---|---|---|
| README — mulesoft-raml-validator | 1.4.2 | 2026-10-25 | Karim DJAAFAR — Jasmine Conseil | Released |

> A Claude skill that audits MuleSoft RAML 1.0 API specifications for production
> readiness — naming, API-Led Connectivity layering, reuse, examples, security,
> versioning and documentation — and can generate a corrected "best-practices"
> version of the spec with a remediation guide.

**Maintained by [Jasmine Conseil](https://www.jasmineconseil.com)** — MuleSoft
MCPA-certified integration consulting firm, founded in 2006, working across
Europe, North America and Africa.

---

## What this skill does

1. **Audits** a RAML 1.0 spec against **23 rules in 7 categories** (Naming,
   API-Led, Reuse, Spec, Security, Versioning, Documentation) — 21 checked by
   the analyzer, `REUSE-002` (duplicated error schemas) and `SPEC-004` (long
   inline schemas) by Claude's review.
2. **Scores** it from 0 to 100 (`100 − 15·BLOCKER − 5·MAJOR − 2·MINOR`) and gives
   a verdict: **GO** only with a score ≥ 80 and no BLOCKER.
3. **Reports** the API under audit (description, base URI, layer, operations,
   security) and each finding with its severity, location, impact and a
   remediation snippet, as an HTML report and a Markdown report.
4. **Refactors** the spec on request: a corrected RAML that re-audits at
   100/100, plus a remediation guide that traces every change and flags the
   ones that need a human decision.

Deterministic Python scripts do the checks; Claude adds the semantic review and
writes the reports.

**Two languages.** Reports are in **English by default** and in **French on
request** ("rapport en français"): both the audit report and the remediation
guide of a run are produced in the chosen language (`--lang fr` on the two
renderers). Rule IDs, RAML and JSON stay as they are.

## Quick start

### Use it in Claude

1. Install the skill (see [INSTALL.md](INSTALL.md)).
2. In a new conversation, ask for example:

```
Audit this RAML for production readiness: [paste or attach your RAML]
Generate a best-practices version of this RAML and the remediation guide.
```

### Use the scripts on their own

Python 3.9+ with `PyYAML` and `Jinja2`. From the skill folder:

```bash
python scripts/audit_raml.py --raml path/to/spec.raml --out findings.json
python scripts/render_report.py --findings findings.json --out report.html
python scripts/generate_best_practices.py --raml path/to/spec.raml --findings findings.json \
  --out-raml spec-best-practices.raml --out-transformations transformations.json
python scripts/render_remediation_guide.py --transformations transformations.json \
  --findings findings.json --out-md guide.md --out-html guide.html
```

Check an installation in one command: `python scripts/verify_install.py`.

To change the skill (add a rule, extend the generator, change a report, cut a
release), read the **[Developer guide](docs/DEVELOPER-GUIDE.md)**.

## Reference demo

[`examples/demo/`](examples/demo/) runs the whole chain on a realistic
**Leave Management API** and keeps every deliverable, so you can see the
output before running anything:

| Step | File | Result |
|---|---|---|
| Input spec | `leave-management-api.raml` | — |
| Audit | `leave-management-api-findings.json`, `leave-management-api-report.html` (FR: `.fr.html`) | 16 findings (2 BLOCKER, 8 MAJOR, 2 MINOR, 4 INFO) — **26/100, NO-GO** |
| Refactor | `leave-management-api-best-practices.raml`, `leave-management-api-transformations.json` | 15 transformations (9 mechanical, 6 heuristic) |
| Re-audit | `leave-management-api-best-practices-findings.json` | 0 findings — **100/100, GO** |
| Remediation guide | `leave-management-api-remediation-guide.md` / `.html` (FR: `.fr.md` / `.fr.html`) | 6 points flagged for human review |

## Rule catalog

Full catalog in [`references/raml-best-practices.md`](references/raml-best-practices.md)
and §2 of [`SKILL.md`](SKILL.md).

| Category | Rules | Examples |
|---|:---:|---|
| Naming (`NAMING-*`) | 4 | kebab-case resources, plural collections, camelCase query parameters, `s-/p-/x-` titles |
| API-Led (`APIC-*`) | 3 | no database resources in Experience APIs, no orchestration verbs in System APIs |
| Reuse (`REUSE-*`) | 3 | pagination and errors as traits, root `securedBy` |
| Spec quality (`SPEC-*`) | 4 | examples on bodies, 400/401/404/500 documented |
| Security (`SEC-*`) | 3 | security scheme declared, sensitive endpoints secured, OAuth 2.0 preferred |
| Versioning (`VER-*`) | 3 | `version` at root and in `baseUri`, `v1` rather than `v1.0.3` |
| Documentation (`DOC-*`) | 3 | root description, resource descriptions, `documentation` section |
| **Total** | **23** | |

## Project structure

```
mulesoft-raml-validator/
├── SKILL.md                     # Skill instructions (rules, workflow, output contract)
├── README.md · CHANGELOG.md · INSTALL.md · UPGRADE.md · RELEASE-NOTES-1.4.2.md
├── docs/DEVELOPER-GUIDE.md      # architecture, data contracts, adding a rule, release
├── assets/logo.png
├── LICENSE · NOTICE · SECURITY.md · CONTRIBUTING.md
├── scripts/
│   ├── version.py               # single source of the version
│   ├── audit_raml.py            # analyzer → findings.json
│   ├── render_report.py         # findings.json → HTML report
│   ├── generate_best_practices.py   # refactored RAML + transformations.json
│   ├── render_remediation_guide.py  # remediation guide (Markdown + HTML)
│   └── verify_install.py        # install check + regression tests
├── templates/                   # Jinja2 / Markdown report templates
├── references/raml-best-practices.md
└── examples/
    ├── README.md                # fixtures and how to regenerate them
    ├── customerOrderAPI.raml (+ findings)        # broken fixture: 21/100 NO-GO
    ├── s-customer-orders-api.raml (+ findings)   # clean fixture: 100/100 GO
    └── demo/                    # reference demo, every deliverable
```

## Open core

This is the **Community Edition**, under Apache 2.0. Jasmine Conseil clients can
get an **Enterprise Edition** with sector rule packs (banking, telecom,
healthcare), reports in the client's own branding (HTML/PDF), Anypoint Exchange and
CI/CD integration, custom rules and priority support. Contact
[kdjaafar@jasmineconseil.com](mailto:kdjaafar@jasmineconseil.com).

## Compatibility

- RAML 1.0 (RAML 0.8 is not supported)
- Python 3.9+, `PyYAML`, `Jinja2`
- Claude with code execution enabled (claude.ai, Claude Code, Cowork)

## Data handling

The scripts read the RAML file you give them and write their outputs next to
the paths you choose. They make no network call and send no data anywhere.

## Release notes

Latest: [RELEASE-NOTES-1.4.2.md](RELEASE-NOTES-1.4.2.md) — full history in
[CHANGELOG.md](CHANGELOG.md).

## Roadmap

See [CHANGELOG.md](CHANGELOG.md#roadmap--tentative). Next: `SPEC-005` JSON
Schema check, `--strict` CI gate, layer inference on nested resources.

## Contact & feedback

**Follow the project**: select **Watch → Custom → Releases** on GitHub to be
notified of each new version, and ⭐ **Star** it if it helps you. Release notes
for every version are in `RELEASE-NOTES-x.y.z.md` and [CHANGELOG.md](CHANGELOG.md).

**Give feedback**: [open an issue](https://github.com/karimdjaafar/mulesoft-raml-validator/issues/new/choose)
— templates are ready for a bug, a false positive and a rule proposal. You can
follow each one and its fix from the issue page.

- **Maintainer**: Karim DJAAFAR — [kdjaafar@jasmineconseil.com](mailto:kdjaafar@jasmineconseil.com)
- **Bugs, false positives, rule ideas**: [GitHub Issues](https://github.com/karimdjaafar/mulesoft-raml-validator/issues)
- **Enterprise Edition**: [kdjaafar@jasmineconseil.com](mailto:kdjaafar@jasmineconseil.com)
- **Security issues**: see [SECURITY.md](SECURITY.md) — do not open a public issue

## Contributing · License

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and
[SECURITY.md](SECURITY.md). Licensed under the Apache License 2.0: see
[LICENSE](LICENSE) and [NOTICE](NOTICE).

```
Copyright (c) 2026 Karim DJAAFAR — Jasmine Conseil
```

---

## Historique du document

| Version | Date | Commentaire |
|---|---|---|
| 1.4.2 | 2026-10-25 | Rewritten for v1.4.2: real script usage, reference demo, structure, data handling, release notes link, contact & feedback, roadmap; Jasmine Conseil cartouches. |
| 1.2.0 | 2026-05-04 | Previous README (v1.2.0). |

<p align="right"><span style="color:#E97132">© 2026 Jasmine Conseil</span></p>
