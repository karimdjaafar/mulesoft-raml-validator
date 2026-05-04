# mulesoft-raml-validator

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Version](https://img.shields.io/badge/version-1.2.0-orange.svg)](CHANGELOG.md)
[![Skill](https://img.shields.io/badge/Claude-Skill-FF7A45.svg)](https://docs.claude.com/en/agents-and-tools/agent-skills/overview)

> A Claude skill that audits MuleSoft RAML 1.0 API specifications against production-grade best practices, including naming conventions, API-Led Connectivity layer alignment, security, versioning, and documentation quality.

**Maintained by [Jasmine Conseil](https://www.jasmineconseil.com)** — MuleSoft MCPA-certified consulting firm with 20 years of integration expertise across Europe, North America, and Africa.

---

## What this skill does

When invoked, it produces a structured audit report on any RAML 1.0 specification:

- ✅ **23 audit rules** across 7 categories (Naming, API-Led, Reuse, Spec, Security, Versioning, Documentation)
- ✅ **Severity-ranked findings** (BLOCKER / MAJOR / MINOR / INFO) with remediation snippets
- ✅ **Production-readiness score** from 0 to 100 with automatic NO-GO on any BLOCKER
- ✅ **English-only deliverable** — reports stay in English regardless of conversation language, for CI/CD traceability
- ✅ **Hybrid execution model** — deterministic Python checks + Claude semantic analysis

## Quick start

### Installation in Claude.ai

1. Download the latest release: [`mulesoft-raml-validator-v1.2.0.zip`](releases/)
2. In Claude.ai: **Settings → Customize → Skills → "+" → "+ Create skill"**
3. Upload the ZIP file
4. Toggle the skill on

### Usage

Open a new conversation in Claude and try one of these prompts:

```
Audit this RAML for production readiness: [paste or upload your RAML]
Validate my API spec against MuleSoft best practices
Check if this RAML follows API-Led Connectivity principles
```

Claude will load the skill, run the audit, and produce a Markdown report with findings and remediation.

### Standalone CLI usage

You can also use the audit scripts directly without Claude:

```bash
# Run the audit
python scripts/audit_raml.py --raml path/to/spec.raml --out findings.json

# Render an HTML report
python scripts/render_report.py --findings findings.json --out report.html --format html

# Or render Markdown
python scripts/render_report.py --findings findings.json --out report.md --format markdown
```

## Example output

A real audit on the included sample RAML (`examples/bad-customer-orders.raml`) produces:

```
✓ Audit complete: 18 findings, score 19/100

Findings breakdown:
  BLOCKER: 2   (no security declared, no error responses)
  MAJOR:   9   (naming, layering, examples, versioning)
  MINOR:   3   (snake_case query param, no resource descriptions)
  INFO:    4   (layer prefix hint, OAuth preference, etc.)

Verdict: 🛑 NO-GO — significant rework required before deployment
```

The full sample report is in [`examples/sample-report.md`](examples/sample-report.md).

## Audit rule catalog

See [`references/raml-best-practices.md`](references/raml-best-practices.md) for the complete rule catalog.

| Category | Rule count | Examples |
|----------|:---------:|----------|
| Naming | 4 | kebab-case resources, plural nouns, layer prefixes |
| API-Led Connectivity | 3 | Layer alignment, no DB calls in Experience APIs |
| Reuse | 3 | Traits for pagination, shared error schemas |
| Spec quality | 4 | Examples on bodies, 4xx/5xx defined |
| Security | 3 | securitySchemes declared, sensitive endpoints secured |
| Versioning | 3 | version in baseUri, semantic versioning |
| Documentation | 3 | Root description, resource descriptions |
| **Total** | **23** | |

## Project structure

```
mulesoft-raml-validator/
├── SKILL.md                              # Skill manifest (YAML frontmatter + instructions)
├── LICENSE                                # Apache 2.0
├── NOTICE                                 # Attribution
├── CHANGELOG.md                           # Version history (Keep a Changelog format)
├── README.md                              # This file
├── CONTRIBUTING.md                        # Contribution guidelines
├── .gitignore                             # Python / IDE / secrets
├── scripts/
│   ├── audit_raml.py                      # Deterministic structural audit (Python + PyYAML)
│   └── render_report.py                   # Markdown / HTML renderer
├── templates/
│   └── audit-report-template.md           # Report skeleton with placeholders
├── references/
│   └── raml-best-practices.md             # Quick reference for all rule IDs
└── examples/
    ├── bad-customer-orders.raml           # Deliberately broken sample RAML
    └── sample-report.md                   # The audit report this RAML produces
```

## Open core model

This is the **Community Edition** under Apache 2.0. An **Enterprise Edition** is available
for clients of Jasmine Conseil with the following additional features:

| Feature | Community | Enterprise |
|---------|:---------:|:----------:|
| 23 baseline audit rules | ✅ | ✅ |
| Markdown report output | ✅ | ✅ |
| Basic HTML report | ✅ | ✅ |
| Sector-specific rules (banking, telecom, healthcare) | — | ✅ |
| Branded HTML/PDF reports (Jasmine Conseil charter) | — | ✅ |
| Anypoint Exchange integration | — | ✅ |
| CI/CD integration (Maven plugin, GitHub Actions) | — | ✅ |
| Priority support and updates | — | ✅ |
| Custom rules on demand | — | ✅ |

For Enterprise inquiries, contact [contact@jasmineconseil.com](mailto:contact@jasmineconseil.com).

## Compatibility

- **RAML version**: 1.0 only (RAML 0.8 not supported)
- **Python**: 3.9+
- **Dependencies**: PyYAML (auto-installed by Claude when running the skill)
- **Claude**: tested with Claude 4.7 family, requires Code Execution capability enabled

## Roadmap

See [CHANGELOG.md](CHANGELOG.md#roadmap--tentative) for the full version history.

**v1.2.0 (current):**
- English-only deliverable enforcement (§3bis) — reports stay in English regardless of conversation language

**v1.3.0 (planned):**
- Multi-language conversational layer (French + English chat replies, English report)
- JSON Schema validity check (`SPEC-005`)
- Pre-production gate via `--strict` flag (non-zero exit on any BLOCKER)
- Score evolution projection (per-remediation-phase trajectory)

**v1.4.0 (planned):**
- OAS 3.0 ingestion (audit a converted RAML or native OpenAPI 3.0 spec)
- Diff mode (audit only the delta between two RAML versions)
- Anypoint Exchange API Governance ruleset export

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs or false positives
- Proposing new audit rules
- Submitting pull requests

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full text and [NOTICE](NOTICE) for attribution requirements.

```
Copyright (c) 2026 Karim DJAAFAR — Jasmine Conseil
```

## About Jasmine Conseil

Jasmine Conseil is an international consulting firm specialized in digital transformation,
systems integration, and software craftsmanship. Founded in 2006, present across Europe,
North Africa, West Africa, and North America. Strategic partner of MuleSoft (MCPA), Salesforce,
Red Hat, Sonarqube, and Eclipse Foundation.

🌐 [www.jasmineconseil.com](https://www.jasmineconseil.com) ·
🐦 [@JasmineConseil](https://twitter.com/JasmineConseil) ·
💼 [LinkedIn](https://www.linkedin.com/company/jasmineconseil/)
