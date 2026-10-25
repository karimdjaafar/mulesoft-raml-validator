# Changelog — mulesoft-raml-validator

| Document | Version | Date | Author | Status |
|---|---|---|---|---|
| CHANGELOG — mulesoft-raml-validator | 1.4.2 | 2026-10-25 | Karim DJAAFAR — Jasmine Conseil | Released |

All notable changes to this skill are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.2] — 2026-10-25

### Fixed
- **Repository re-synchronised with the released skill.** The GitHub
  repository had stayed at v1.2.0 while v1.3.0 → v1.4.1 shipped to Claude
  users. v1.4.2 brings the code, templates and examples of v1.4.1 back into
  the repository, and merges this changelog.
- **One finding per rule (`audit_raml.py`).** Findings sharing a rule ID are
  now merged into one entry listing every location, as §4 of `SKILL.md`
  always stated. Before, a snake_case query parameter on two resources
  raised two `NAMING-003` findings and was penalised twice.
- **`NAMING-004` checks the whole title.** A title must now be fully
  kebab-case after its layer prefix; `s-leave management-api` used to pass.
  The generator rebuilds such titles (`s-leave-management-api`).
- **Generator no longer pluralises singleton sub-resources** written as one
  multi-segment key (`/users/{userId}/password`, `/{employeeId}/balance`).
  It now judges the last segment only, like the analyzer.
- **`verify_install.py` is path-agnostic.** It checks the folder it ships in
  (or `--root PATH`) instead of a fixed `/mnt/skills/user/...` path that
  reported "NOT INSTALLED" on correct installs, writes its scratch files to a
  private temporary folder, and runs the scripts with the current Python.

### Added
- **Reports in two languages**: English by default, French with `--lang fr` on
  `render_report.py` and `render_remediation_guide.py` (French templates and
  `scripts/i18n_fr.py`). Both reports of a run use the same target language
  (§3bis of `SKILL.md`). English output is unchanged. `--api-description`
  shows a translated description of the API (marked "description traduite")
  without touching the RAML.
- Generator writes multi-line descriptions as a literal block (`|`) instead of
  a quoted string with doubled line breaks.
- **"API under audit" section in the HTML report and in the remediation guide**: title, version, layer,
  description, base URI, media type, resources, operations (with their
  descriptions), security schemes, types and traits, as declared in the spec.
  Carried by a new optional `api` block in `findings.json` (`api_profile`);
  older findings files still render.
- **Developer guide** (`docs/DEVELOPER-GUIDE.md`): architecture, data
  contracts, adding a rule, reports and charter, tests, release.
- Report footer links: project, developer guide, feedback, contact.
- **Reference demo API** in `examples/demo/`: a Leave Management API with
  every deliverable (findings, HTML report, best-practices RAML, re-audit,
  transformations, remediation guide). `verify_install.py` replays it
  (step 7: 16 findings, 26/100 NO-GO → refactor 100/100 GO).
- **`scripts/version.py`** — single source of the version, read by every
  script and by `verify_install.py`.
- **Jasmine Conseil charter on the HTML report and the remediation guide**:
  header band with the project name and a bug-and-shield logo, "by Jasmine
  CONSEIL" wordmark, orange `#E97132` and dark blue `#0E2841`
  palette, Calibri, © 2026 Jasmine Conseil footer. The Enterprise Edition
  now offers the client's own branding instead.

### Changed
- Rule count corrected to **23** (21 automated; `REUSE-002` and `SPEC-004` by
  Claude's review) in
  `SKILL.md`, the README and the rule reference; earlier texts said 22 or 23.
- Contact and feedback: maintainer address (kdjaafar@jasmineconseil.com) in
  every document, GitHub issue templates (bug, false positive, rule proposal),
  "Follow the project" section in the README.
- `README.md`, `INSTALL.md`, `UPGRADE.md` and `examples/README.md` rewritten
  for v1.4.2.

### Removed
- `examples/bad-customer-orders.raml` and `examples/sample-report.md`
  (v1.2.0 samples, superseded by `customerOrderAPI.raml` and `examples/demo/`).

### Known limitations
- Layer inference only looks at top-level resources: the demo's nested
  `/approve` action does not make the generator pick the Process layer. The
  remediation guide flags the title choice for human review.

---

## [1.4.1] — 2026-05-06

### Changed
- **Skill front-matter `description` widened** to cover both audit and
  remediation intents. The v1.4.0 description only listed audit verbs
  (*audit, review, validate, check*) so the skill router did not reliably
  activate on remediation requests like *"generate a best-practices
  RAML"*, *"refactor this RAML"*, or *"fix the issues in this spec"*.
  v1.4.1 adds *fix, refactor, remediate, regenerate, generate a
  best-practices version* to the trigger list and explicitly mentions
  the "best-practices" deliverable in the first sentence.

### Notes
- This is a **trigger-fix patch** with no functional changes. The 22
  rules, the score formula, the round-trip contract, and all scripts/
  templates are byte-identical to v1.4.0 except for the version banner
  bump and the description string.
- If you have v1.4.0 installed and the skill activates correctly on your
  typical phrasing, you can safely stay on v1.4.0. v1.4.1 only matters
  if you noticed the skill not activating on remediation phrasings.

---

## [1.4.0] — 2026-05-06

### Added
- **`scripts/generate_best_practices.py` — best-practices generator.**
  New script that refactors a RAML to resolve every finding produced by
  `audit_raml.py`. Applies one transformation per rule, idempotently
  (no-op if the finding is absent). Writes both the refactored RAML
  (mono-file) and a structured `transformations.json` that traces every
  change with a kind classification (mechanical / heuristic /
  architectural) and a confidence level (high / medium / low). The
  round-trip contract is: refactoring a NO-GO RAML must produce a RAML
  that the analyzer scores 100/100, GO. Verified on the broken fixture
  (21/100 → 100/100).
- **`scripts/render_remediation_guide.py` — guide renderer.** Renders
  the personalized remediation guide (Markdown + HTML) from the
  transformations.json. The HTML guide uses the same v1.3 branded
  design language as the audit report (cyan header band, navy strip,
  pills) adapted for the remediation context: kind badges (green
  mechanical / orange heuristic / blue architectural) instead of
  severity pills, before/after diff cards in two columns, and explicit
  review-flag callouts for transformations that need human attention.
- **`templates/remediation-guide.md.j2` and
  `templates/remediation-guide.html.j2` — guide templates.**
  Single-file Jinja2 templates that consume the transformations.json
  payload. The HTML template extends the v1.3 CSS custom property
  palette with 3 new variables (`--mechanical`, `--heuristic`,
  `--architectural`) for the kind palette.
- **§3ter in `SKILL.md`** documenting the best-practices generator as a
  distinct deliverable from the audit. Clarifies that audit and
  remediation are separate user intents — the generator is invoked when
  the user explicitly asks for a remediation, refactor, or "fixed
  version", not silently after every audit.
- **Step 6 in `verify_install.py` — round-trip test.** The verifier now
  exercises the full audit → generate → re-audit pipeline on the broken
  fixture, validating that the refactor scores 100/100. This is the
  strongest possible smoke test because it exercises every script in
  the bundle.

### Changed
- **§4 Active Components** in `SKILL.md` updated with the four new
  resources from v1.4.0.
- **`verify_install.py` expected file count** raised from 15 to 19
  (added: `generate_best_practices.py`, `render_remediation_guide.py`,
  `remediation-guide.md.j2`, `remediation-guide.html.j2`).
- **`verify_install.py` final verdict** now reads "v1.4.0 FULLY
  DEPLOYED" with the round-trip line included in the success summary.

### Notes
- No rule changes. The 22 audit rules and the score formula are unchanged
  from v1.3.0. v1.4.0 is purely additive — it builds a new layer on top
  of the existing audit pipeline rather than modifying it.
- The mono-file output mode of the generator was chosen for portability.
  A `--output-mode multi` flag for fragment-based output (libraries/,
  dataTypes/, traits/) is a candidate for v1.5.0 if the demand emerges.
- Pluralization (`NAMING-002` fix) uses a simple heuristic suffix rule
  that handles the common cases (-y → -ies, default → +s). Domain-specific
  irregular plurals (e.g. "person" → "people") are not handled and would
  need to be added to a custom dictionary if they appear in audited
  RAMLs.

---

## [1.3.0] — 2026-05

### Added
- **`scripts/audit_raml.py` — first real implementation.** Versions 1.1.0
  through 1.2.0 referenced this analyzer in §4 but never shipped it. v1.3.0
  ships a working PyYAML-based analyzer that applies all 22 rules from §2
  and emits the `findings.json` schema consumed by `render_report.py`.
  Self-tested on both an intentionally-broken RAML (17 findings, score
  21/100, NO-GO) and a clean best-practices RAML (0 findings, score
  100/100, GO).
- **`templates/audit-report-template.md` — first real implementation.**
  Same backstory as the analyzer: referenced in §3 and §5.5 since v1.1.0,
  never materialised until now. v1.3.0 ships a Jinja2 template that
  reproduces the canonical Markdown audit structure (verdict, summary
  table, findings table, detailed cards, strengths, score arithmetic,
  next steps) and handles both NO-GO and GO branches with appropriate
  empty-state messaging.
- **`references/raml-best-practices.md` — first real implementation.**
  Same backstory. v1.3.0 ships a 7-section cheat sheet: 22-row rules
  table, layer decision tree, verb→layer mapping, remediation snippet
  palette, severity calibration guidance, score interpretation bands,
  and a final "when this disagrees with §2, §2 wins" clause.
- **`examples/` — new directory with two test fixtures.** Ships
  `customerOrderAPI.raml` (deliberately broken — 17 findings, score
  21/100, NO-GO) and `s-customer-orders-api.raml` (single-file clean
  spec — 0 findings, score 100/100, GO), each with an analyzer-generated
  `findings.json` snapshot. The snapshots are committed alongside the
  fixtures so they double as a regression baseline: any code change
  that produces a different findings.json is flagged by `diff` against
  the committed snapshot. The smoke test in `UPGRADE.md` now uses these
  fixtures (the previous v1.3.0 release referenced a non-existent
  `examples/customerOrderAPI-findings.json` — fixed in this update).
- **Trait-aware SPEC-003 evaluation.** When a method declares
  `is: [ standardErrors ]`, the analyzer follows the trait reference and
  unions the trait-contributed response codes with the method's inline
  responses before checking for the required error set. External
  `!include` traits are conservatively trusted (assumed to cover the
  required codes) to avoid false positives.
- **Branded HTML report design.** New `templates/report.html.j2` Jinja2
  template carrying the v1.3 visual identity: cyan header band on the
  category × severity matrix, severity pills (red / orange / gold / blue) for
  per-cell counts, navy totals strip with solid pills, score-formula caption,
  and per-finding cards with severity-coloured left borders + monospaced rule
  IDs + remediation code blocks.
- **6-variable themability.** The template exposes `--header-blue`,
  `--footer-navy`, `--sev-blocker`, `--sev-major`, `--sev-minor`,
  `--sev-info` as CSS custom properties so the Jasmine palette (or any other
  brand palette) drops in without forking the template.
- **Both formats delivered by default** (§5.7). The skill now produces both
  the Markdown report and the HTML report on every run, unless the user
  explicitly asks for one format only.

### Changed
- **`scripts/render_report.py` rewritten** to consume the v1.3 template.
  Severity counts in the category matrix are now computed strictly from
  rule-ID prefixes (`SEC-*` → Security, `NAMING-*` → Naming, etc.) so the
  matrix can never disagree with the detailed-findings list. Score and
  verdict are computed in-script applying the exact §5.6 + §6 formula
  (`100 − 15·B − 5·M − 2·m`, floor 0; GO requires score ≥ 80 AND zero
  blockers).
- **§3 Outputs & Deliverables** rewritten to promote HTML from "basic" to a
  first-class deliverable, with a note that the no-JS template converts to
  PDF cleanly via `weasyprint` or Playwright `page.pdf()`.
- **§4 Active Components** updated to document the new template and the
  computed-from-rule-prefix behaviour of the renderer.
- **§5.3 reinforced — script invocation is now mandatory.** When
  `scripts/audit_raml.py` is available in the skill folder, Claude must
  invoke it rather than perform a direct in-chat audit. A direct audit is
  only acceptable as a fallback when the install is genuinely incomplete
  (only `SKILL.md` present), and even then Claude must tell the user the
  analyzer is missing. The matching anti-pattern is added to §6.
- **`scripts/verify_install.py` — new install verifier.** Walks 5 steps
  (folder presence → version banner → file inventory → broken-fixture
  smoke test → clean-fixture smoke test) and exits with one of 5 codes.
  Designed to be invoked from a fresh Claude session to give an
  unambiguous answer to "is v1.3.0 correctly deployed?". Useful when
  diagnosing partial installs (the symptom that triggered v1.3.0's late
  additions of `INSTALL.md` and this verifier).
- **`INSTALL.md` added.** Documents the deployment procedure across three
  possible environments (admin console, Git-backed repo, direct
  filesystem access), with post-install verification steps and rollback
  guidance. This was the missing piece that made v1.2.0 → v1.3.0 a
  guess-the-deployment-path exercise.

### Notes
- No rule changes. The 7 audit categories and their rule IDs (`NAMING-*`,
  `APIC-*`, `REUSE-*`, `SPEC-*`, `SEC-*`, `VER-*`, `DOC-*`) are unchanged
  from v1.2.0, so existing audit results re-render under v1.3.0 without
  re-running the analysis.
- The Enterprise Edition note in §3 is preserved; the open-source v1.3
  template covers the Jasmine palette only via theme overrides, while the
  Enterprise Edition ships sector-specific rule packs and CI/CD integration.

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

## Roadmap — tentative

- **1.5.0** — `SPEC-005` JSON Schema validity check; `--strict` CI gate
  (non-zero exit on any BLOCKER); layer inference on nested resources.
- **Later** — OAS 3.0 ingestion; diff mode between two RAML versions;
  Anypoint Exchange governance ruleset export; GitHub Actions template.

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

## Historique du document

| Version | Date | Commentaire |
|---|---|---|
| 1.4.2 | 2026-10-25 | Changelogs of the repository (1.0.0–1.2.0) and of the released skill (1.3.0–1.4.1) merged; 1.4.2 entry; roadmap updated. |
