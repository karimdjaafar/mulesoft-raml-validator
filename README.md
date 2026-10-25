![RAML Validator logo](assets/logo.png)

# mulesoft-raml-validator

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.5.0-E97132.svg)](CHANGELOG.md)
[![Skill](https://img.shields.io/badge/Claude-Skill-0E2841.svg)](https://docs.claude.com/en/agents-and-tools/agent-skills/overview)

| Document | Version | Date | Author | Status |
|---|---|---|---|---|
| README — mulesoft-raml-validator | 1.5.0 | 2026-10-25 | Karim DJAAFAR — Jasmine Conseil | Released |

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

### Use the `raml-validator` command

One command, no script to chain by hand, on **macOS, Linux and Windows**
(setup in [INSTALL.md](INSTALL.md)):

```bash
raml-validator run   my-api.raml --out-dir reports/              # everything, in English
raml-validator run   my-api.raml --out-dir reports/ --lang fr    # everything, in French
raml-validator audit my-api.raml                                 # audit report only
raml-validator fix   my-api.raml                                 # corrected RAML + remediation guide
raml-validator verify                                            # install check
raml-validator --version
```

- **Coloured output** on a terminal (verdict in green or red, step titles,
  file list); plain when piped, with `--no-color` or when `NO_COLOR` is set.
- **Tab completion** for zsh, bash and PowerShell: commands, options,
  `en`/`fr`, and only `.raml` files for the spec —
  `eval "$(raml-validator completion zsh)"`.
- Files are named after the spec: `my-api-findings.json`, `my-api-report.html`,
  `my-api-best-practices.raml`, `my-api-transformations.json`,
  `my-api-remediation-guide.md` / `.html` (`.fr.html` / `.fr.md` in French).
- `--api-description "…"` shows another description of the API in the
  reports, e.g. its translation.
- Prerequisites: macOS, Linux or Windows and Python 3.9+. PyYAML and Jinja2 are
  installed automatically into a private `.venv` on first use
  (`raml-validator setup` to do it on demand) — see [INSTALL.md](INSTALL.md#0-prerequisites).

To change the skill (add a rule, extend the generator, change a report, cut a
release), read the **[Developer guide](docs/DEVELOPER-GUIDE.md)**.

## Reference demo

[`examples/demo/`](skills/mulesoft-raml-validator/examples/demo/) runs the whole chain on a realistic
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

Full catalog in [`references/raml-best-practices.md`](skills/mulesoft-raml-validator/references/raml-best-practices.md)
and §2 of [`SKILL.md`](skills/mulesoft-raml-validator/SKILL.md).

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

The repository is a **Claude plugin** (`jasmine-raml-validator`) holding one
skill, `mulesoft-raml-validator`:

```
mulesoft-raml-validator/                 # repository = plugin
├── .claude-plugin/plugin.json           # plugin manifest (name, version, author, licence)
├── bin/raml-validator(.cmd)             # the raml-validator command (put this folder on PATH)
├── skills/mulesoft-raml-validator/      # the skill
│   ├── SKILL.md                         # instructions for Claude (rules, workflow, output contract)
│   ├── bin/raml-validator(.cmd)         # launchers used by the skill (macOS, Linux / Windows)
│   ├── completions/                     # zsh, bash and PowerShell tab completion
│   ├── scripts/                         # raml_validator.py (the command), audit_raml.py, render_report.py,
│   │                                    # generate_best_practices.py, render_remediation_guide.py,
│   │                                    # verify_install.py, version.py, i18n_fr.py
│   ├── templates/                       # HTML / Markdown report templates (EN, FR)
│   ├── references/raml-best-practices.md
│   └── examples/                        # regression fixtures + reference demo (examples/demo/)
├── docs/DEVELOPER-GUIDE.md · docs/ACCEPTANCE-TESTS.md · docs/images/
├── README.md · INSTALL.md · UPGRADE.md · CHANGELOG.md · RELEASE-NOTES-1.5.0.md
├── LICENSE · NOTICE · SECURITY.md · CONTRIBUTING.md · assets/logo.png
└── .github/                             # issue templates, acceptance workflow (Ubuntu, macOS, Windows)
```

## Open core

This is the **Community Edition**, under Apache 2.0. Jasmine Conseil clients can
get an **Enterprise Edition** with sector rule packs (banking, telecom,
healthcare), reports in the client's own branding (HTML/PDF), Anypoint Exchange and
CI/CD integration, custom rules and priority support. Contact
[kdjaafar@jasmineconseil.com](mailto:kdjaafar@jasmineconseil.com).

## Compatibility

- RAML 1.0 (RAML 0.8 is not supported)
- macOS, Linux or Windows for the command; Python 3.9+; `PyYAML` and `Jinja2`
  (installed automatically on first use)
- Claude with code execution enabled (claude.ai, Claude Code, Cowork)

## Data handling

The scripts read the RAML file you give them and write their outputs next to
the paths you choose; they send no data anywhere. The only network access is the
**one-time setup**: on first use (or `raml-validator setup`) the command creates
a private Python environment (`.venv`) inside the skill folder and downloads
**PyYAML** and **Jinja2** from the Python Package Index (pypi.org). Nothing else
is downloaded, and nothing about your RAML is sent.

## Release notes

Latest: [RELEASE-NOTES-1.5.0.md](RELEASE-NOTES-1.5.0.md) — full history in
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
| 1.5.0 | 2026-10-25 | Rewritten for v1.5.0: real script usage, reference demo, structure, data handling, release notes link, contact & feedback, roadmap; Jasmine Conseil cartouches. |
| 1.2.0 | 2026-05-04 | Previous README (v1.2.0). |

<p align="right"><span style="color:#E97132">© 2026 Jasmine Conseil</span></p>
