# Changelog

All notable changes to `mulesoft-raml-validator` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] — 2026-05-04

### Added

- **§3bis: Output Language deliverable rule.** Audit reports (Markdown, HTML, JSON
  findings) are now **English-only by default**, regardless of the user's
  conversation language. Ensures consistency across audits, traceability in
  CI/CD pipelines, and shareability with international stakeholders.
- Explicit clarification that **conversational acknowledgment** to the user
  may follow the user's input language while the deliverable artifact stays
  in English.
- Per-call override mechanism: if the user explicitly requests another
  language, the skill confirms before deviating from the English default.

### Changed

- Updated `README.md` to align version, rule count, and roadmap entries with
  the SKILL.md authoritative source.
- Refined anti-pattern catalog (§6) to reject reports not written in English.

### Documentation

- Added an Apache 2.0 license header to `SKILL.md`.
- New `NOTICE` file capturing attribution requirements per Apache 2.0 §4(d).

---

## [1.1.0] — 2026-04-15

### Added

- Hybrid execution model: deterministic Python pre-analysis (`scripts/audit_raml.py`)
  + Claude semantic enrichment (layer-intent inference, business-impact severity).
- HTML report rendering via `scripts/render_report.py --format html` with a
  neutral, accessible default template.
- JSON intermediate format (`findings.json`) consumable by downstream tooling.
- Quick-review mode (executive summary + top 5 findings only) for informal
  pre-deployment checks.

### Changed

- Scoring rule made explicit and reproducible: start at 100, subtract 15
  per BLOCKER, 5 per MAJOR, 2 per MINOR, 0 per INFO. Floor at 0.
- BLOCKER findings now automatically force a NO-GO verdict regardless of
  numeric score.

---

## [1.0.0] — 2026-03-10

### Added

- Initial release of the **Community Edition**.
- 23 audit rules across 7 categories:
  - **Naming** (`NAMING-*`): 4 rules — kebab-case resources, plural nouns,
    camelCase query params, layer-prefixed titles.
  - **API-Led Connectivity** (`APIC-*`): 3 rules — Experience-layer purity,
    System-layer separation from orchestration, layer-prefixed identification.
  - **Reuse** (`REUSE-*`): 3 rules — pagination traits, shared error schemas,
    root-level `securedBy:`.
  - **Spec quality** (`SPEC-*`): 4 rules — request/response examples,
    mandatory error responses (400/401/404/500), schema externalization.
  - **Security** (`SEC-*`): 3 rules — declared schemes, sensitive endpoints
    secured, OAuth 2.0 preference.
  - **Versioning** (`VER-*`): 3 rules — root `version:`, version in `baseUri`,
    semantic version style.
  - **Documentation** (`DOC-*`): 3 rules — root description ≥ 50 chars,
    resource descriptions, `documentation:` section.
- Markdown report generation following `templates/audit-report-template.md`.
- Markdown report sections: Executive Summary, Findings Table, Detailed
  Findings, Strengths, Next Steps, Score Calculation appendix.
- Reference cheat sheet `references/raml-best-practices.md` indexing all
  rule IDs.

---

## [Roadmap — tentative]

### [1.3.0] — planned

- **Multi-language conversational layer**: chat reply in French/English/Spanish
  while keeping the report English-only (per §3bis).
- **`SPEC-005`**: JSON Schema validity check for inline RAML types.
- **Pre-production gate**: `--strict` CLI flag that exits with non-zero code
  on any BLOCKER, suitable for CI/CD pipelines.
- **Score evolution projection**: per-remediation-phase score trajectory
  (e.g., "after fixing BLOCKERs: 49/100 → after MAJORs: 89/100").

### [1.4.0] — planned

- **OAS 3.0 ingestion**: audit a converted RAML or a native OpenAPI 3.0 spec.
- **Diff mode**: audit only the delta between two RAML versions, useful for
  PR reviews.
- **Anypoint Exchange API Governance ruleset export**: emit a compatible
  ruleset for native enforcement at the Exchange level.

### Under consideration

- VS Code extension wrapping the audit script.
- GitLab CI / GitHub Actions templates.
- Sector-specific rule packs for Community (currently Enterprise-only).

---

## Versioning policy

- **MAJOR** (`X.0.0`): breaking change to the rule catalog (rule renamed,
  removed, or severity changed in a way that would alter existing audit
  scores), or breaking change to the report format consumed by downstream
  tooling.
- **MINOR** (`x.Y.0`): new rule added, new output format, new CLI flag,
  new template, or any backward-compatible feature.
- **PATCH** (`x.y.Z`): bug fix, false-positive correction, doc-only change,
  template wording fix.

Rule IDs are stable across MAJOR versions when possible. If a rule ID is
deprecated, it is announced one MINOR version ahead and removed only at
the next MAJOR boundary.

---

[1.2.0]: https://github.com/karim-djaafar/mulesoft-raml-validator/releases/tag/v1.2.0
[1.1.0]: https://github.com/karim-djaafar/mulesoft-raml-validator/releases/tag/v1.1.0
[1.0.0]: https://github.com/karim-djaafar/mulesoft-raml-validator/releases/tag/v1.0.0
