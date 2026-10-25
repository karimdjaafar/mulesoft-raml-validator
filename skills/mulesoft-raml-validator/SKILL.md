---
name: mulesoft-raml-validator
description: Audit a MuleSoft RAML 1.0 API spec for production readiness, and optionally generate a refactored "best-practices" version of the RAML with a remediation guide. Use whenever a user asks to review, audit, validate, check, fix, refactor, remediate, regenerate, or generate a best-practices version of a RAML file against MuleSoft and API-Led Connectivity guidelines.
---

<!--
═══════════════════════════════════════════════════════════════════════════════
  Skill name:    mulesoft-raml-validator
  Version:       1.5.0
  Released:      2026-10-25

  Copyright (c) 2026 Karim DJAAFAR — Jasmine Conseil

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at:

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  See NOTICE file for attribution requirements.
  See CHANGELOG.md for version history and roadmap.
═══════════════════════════════════════════════════════════════════════════════
-->

This skill audits a MuleSoft RAML 1.0 specification and produces a structured quality report with severity-ranked findings, remediation guidance, and a production-readiness score. The audit covers naming conventions, API-Led Connectivity layer alignment, traits and resourceTypes reuse, examples coverage, security schemes, versioning strategy, and documentation completeness.

The user provides a RAML file (uploaded, pasted, or referenced by path). They may include context about the API's intended layer (System / Process / Experience), the target runtime (CloudHub 2.0, RTF, Hybrid), and the consumer profile.

---

## §1. Context & Thinking

Before producing the audit, understand the context and commit to an audit posture:

- **Purpose**: Is this a pre-deployment audit, a peer review, or a learning exercise? The tone differs.
- **Layer**: Which layer does the RAML claim to be? (System / Process / Experience). Many violations are layer-specific.
- **Maturity**: Is this a v0 PoC RAML or a v1 production candidate? Calibrate severity accordingly.
- **Differentiation**: A good audit doesn't just list problems — it ranks them by business impact and gives a concrete fix snippet.

**CRITICAL**: An audit must be actionable. Every finding gets a severity (BLOCKER / MAJOR / MINOR / INFO), a precise location (line / section), and a remediation example. Vague comments like "improve naming" are useless.

Then produce a structured report that is:
- Scannable: severity icons, grouped by category
- Actionable: every finding has a fix snippet
- Prioritized: BLOCKERs first, INFOs last
- Honest: include a global readiness score (0–100) and a go/no-go recommendation

---

## §2. Audit Rules (the substance)

The audit checks 7 categories. Each rule has an ID for traceability.

**Naming conventions** (`NAMING-*`)
- `NAMING-001` (MAJOR): Resources MUST use kebab-case (`/customer-orders`, not `/customerOrders` or `/CustomerOrders`).
- `NAMING-002` (MAJOR): Resource names MUST be plural nouns (`/customers`, not `/customer` or `/getCustomer`).
- `NAMING-003` (MINOR): Query parameters MUST use camelCase (`?sortBy=date`, not `?sort_by=date`).
- `NAMING-004` (MAJOR): API title in `title:` MUST follow `s-{system}-{entity}-api`, `p-{capability}-api`, or `x-{channel}-{capability}-api` per the API-Led layer.

**API-Led Connectivity alignment** (`APIC-*`)
- `APIC-001` (BLOCKER): An Experience API MUST NOT reference database-like resources directly (`/sql-query`, `/db-table`).
- `APIC-002` (MAJOR): A System API MUST NOT contain orchestration verbs (`/process-order`, `/calculate-total`) — those belong to Process APIs.
- `APIC-003` (INFO): API titles SHOULD start with the layer prefix (`s-`, `p-`, `x-`) for instant identification.

**Traits & resourceTypes** (`REUSE-*`)
- `REUSE-001` (MAJOR): If pagination appears on 2+ resources, it MUST be defined as a `trait` and applied via `is:`.
- `REUSE-002` (MAJOR): If error response schemas are duplicated, they MUST be extracted to a shared library or trait.
- `REUSE-003` (MINOR): Common security schemes (OAuth, client-id-enforcement) SHOULD be declared at the root via `securedBy:`.

**Examples & schemas** (`SPEC-*`)
- `SPEC-001` (MAJOR): Every request body MUST have at least one `example`.
- `SPEC-002` (MAJOR): Every response body MUST have at least one `example` per status code.
- `SPEC-003` (BLOCKER): No response defined for `4xx` and `5xx` — every endpoint MUST document at least `400`, `401`, `404`, `500`.
- `SPEC-004` (MINOR): Inline JSON schemas longer than 20 lines SHOULD be moved to `dataTypes/` files.

**Security** (`SEC-*`)
- `SEC-001` (BLOCKER): No `securitySchemes` declared and no `securedBy:` at root — API is fully open.
- `SEC-002` (MAJOR): Sensitive endpoints (POST/PUT/DELETE on resources containing `payment`, `auth`, `user`, `password`) MUST have explicit `securedBy:`.
- `SEC-003` (INFO): OAuth 2.0 SHOULD be preferred over basic auth for production APIs.

**Versioning** (`VER-*`)
- `VER-001` (BLOCKER): No `version:` field at root.
- `VER-002` (MAJOR): The `version:` MUST appear in the `baseUri` (`https://api.example.com/{version}`).
- `VER-003` (INFO): Use semantic versioning (`v1`, `v2`) — avoid `v1.0.3` in the URI.

**Documentation** (`DOC-*`)
- `DOC-001` (MAJOR): Root `description:` is missing or shorter than 50 characters.
- `DOC-002` (MINOR): Resources without a `description:` field.
- `DOC-003` (INFO): No `documentation:` section with usage examples or onboarding guide.

NEVER produce: a pass-only audit (no findings), a flat unranked list, or findings without remediation snippets. If the RAML is genuinely perfect, say so explicitly with proof points — but that's rare.

---

## §3. Outputs & Deliverables

When invoked, this skill produces a structured audit report in one of two formats:

**Markdown** (conversational): inline in chat with this exact structure:
1. Executive summary, findings table, detailed findings, strengths, next steps.

**HTML** *(default deliverable starting in v1.3.0)*: a self-contained,
single-file HTML report with the v1.3 branded design — cyan header band,
severity-pill matrix grouped by the 7 audit categories, navy totals strip,
and per-finding cards with severity-coloured left borders and remediation
code blocks. Generated via `scripts/render_report.py`. Suitable for sharing
audit results with stakeholders or embedding in documentation portals.

If the user uploaded a RAML file, the script `scripts/audit_raml.py` produces a
machine-readable JSON pre-analysis. The render script then consumes that JSON
to produce the chosen output format.

The HTML template uses no JavaScript, so it converts to PDF cleanly via
`weasyprint` or Playwright's `page.pdf()` for downstream archival.

> **Need a branded palette, sector-specific rules, or CI/CD integration?**
> The Enterprise Edition of this skill, available from Jasmine Conseil,
> ships the Jasmine charter (orange/anthracite palette) as a drop-in CSS
> variable override and adds vertical-specific rule packs (banking, retail,
> healthcare). Contact kdjaafar@jasmineconseil.com for details.

---

## §3bis. Output Language *(added in v1.2.0, target language since v1.5.0)*

Every deliverable is produced in **one target language: English (`en`, the
default) or French (`fr`)**. No other language is supported.

- **Default: English.** Use English unless the user asks for French.
- **French on request.** When the user asks for the report in French ("en
  français", "rapport en français", "in French"), the target is `fr` for the
  whole run: `raml-validator run … --lang fr`, so the audit report and the
  generation (remediation) report are both in French. Do not mix languages between the
  two reports of one run.
- Writing to the user in French is **not** by itself a request for a French
  report: keep English and mention in one line that French is available.
- **Language-neutral content** stays as is in both languages: rule IDs
  (`SEC-001`…), RAML paths, YAML remediation snippets, the refactored RAML
  itself, and the JSON files (`findings.json`, `transformations.json` are
  always English).
- **The API description** shown in both reports comes from the RAML and is
  kept in its original language **by default**. Translating it is the user's
  choice: when the target is `fr` and the description is in another language,
  offer the translation in one line; if the user accepts (or asked for
  everything in French), translate it faithfully and pass it with
  `--api-description "…"` on the `raml-validator` command — the reports then mark it
  "(description traduite)". The RAML itself is never changed. The reference
  demo (`examples/demo/`) shows the translated variant. Other quoted user
  content keeps its original language.
- The **chat reply** that presents the reports follows the user's language.

---

## §3ter. Best-Practices Generator *(added in v1.4.0)*

In addition to the audit, the skill can produce a **personalized
remediation deliverable** that refactors the audited RAML to resolve all
findings, accompanied by a guide explaining each transformation.

This is invoked when the user explicitly asks for a remediation, a
refactor, a "fixed version", or "best-practices version" of their RAML.
It is NOT invoked silently after every audit — auditing and remediating
are distinct user intents.

The generator produces three artifacts:

1. **Refactored RAML** (`<source>-refactored.raml`) — the original spec with
   every detected finding resolved. Mono-file output. The contract is that
   re-auditing this file yields **0 findings, score 100/100, GO**.
2. **Transformations log** (`<source>-transformations.json`) — a structured
   JSON tracing every transformation applied: rule, kind (mechanical /
   heuristic / architectural), before/after pair, reasoning, and confidence
   level (high / medium / low).
3. **Remediation guide** (`<source>-remediation-guide.md` and `.html`) —
   a human-readable guide that explains each transformation, flags the
   ones requiring human review, and provides clear next steps.

The pipeline is:

```
audit_raml.py → findings.json
                     ↓
generate_best_practices.py + RAML  →  refactored.raml + transformations.json
                                             ↓
render_remediation_guide.py  →  guide.md + guide.html
```

**Three transformation kinds** are distinguished, with different review
expectations:

- **Mechanical** (high confidence): renames, format normalization,
  structural insertions. Applied directly; no human review needed.
- **Heuristic** (medium confidence): context-aware defaults like
  generated descriptions, placeholder examples, default authentication
  URIs. Flagged for review with a "replace with domain-specific content"
  note.
- **Architectural** (medium confidence): significant choices like layer
  inference (`s-` / `p-` / `x-`) or orchestration-verb resolution. Applied
  with a default but the alternative is documented in the guide.

If a finding cannot be remediated mechanically (typically because it
requires domain knowledge the generator does not have), the guide
explicitly tells the user what choice was made, why, and what the
alternative would be.

---

## §4. Active Components

- **`bin/raml-validator`** *(new in v1.5.0)* — The one command to use, for
  Claude and for people: `audit`, `fix`, `run`, `verify`, `--version`, with
  `--out-dir`, `--lang en|fr` and `--api-description`. It runs
  `scripts/raml_validator.py`, which chains the scripts below; nobody needs to
  call them one by one any more.

- **`scripts/audit_raml.py`** *(implemented in v1.3.0)* — Parses a RAML file
  with PyYAML, applies 21 of the 23 rules from §2 (`REUSE-002` and
  `SPEC-004` are left to Claude's review), and emits a JSON of findings.
  Trait-aware for SPEC-003 (follows `is:` clauses when computing the union
  of declared response codes). Aggregates same-rule findings to one entry
  per rule with all affected locations listed in the `location` field. Run
  with: `python scripts/audit_raml.py --raml path/to/spec.raml --out findings.json`.
- **`scripts/verify_install.py`** *(new in v1.3.0)* — Self-contained
  install verifier. Walks 5 steps (folder presence → version banner →
  file inventory → broken-fixture smoke test → clean-fixture smoke test)
  and exits with one of 5 codes (0 healthy, 1 regression, 2 wrong
  version, 3 partial install, 4 missing entirely). Designed to be run
  in a fresh Claude session with no inherited context, to give an
  unambiguous answer to the question "is this version correctly deployed?".
  Since v1.5.0 it is path-agnostic (it checks the folder it ships in, or
  `--root PATH`), reads the expected version from `scripts/version.py`,
  and adds a round-trip on the reference demo in `examples/demo/`.
  Run with: `python3 scripts/verify_install.py`.
- **`scripts/render_report.py`** *(rewritten in v1.3.0)* — Renders an HTML
  report from the JSON findings using the v1.3 branded template. Severity
  counts in the matrix are computed strictly from rule-ID prefixes (`SEC-*`,
  `NAMING-*`, etc.) so the matrix can never drift from the detailed findings
  list. Score and verdict are computed in-script per the §5.6 + §6 rules.
  Run with: `python scripts/render_report.py --findings findings.json --out report.html`
  (add `--lang fr` for a French report, §3bis).
- **`templates/report.html.j2`** *(new in v1.3.0)* — Single-file Jinja2
  template carrying the HTML structure and CSS for the branded report.
  Themeable via 6 CSS custom properties (`--header-blue`, `--footer-navy`,
  `--sev-blocker`, `--sev-major`, `--sev-minor`, `--sev-info`).
- **`templates/audit-report-template.md`** *(materialised in v1.3.0)* —
  Jinja2-compatible Markdown template that produces the canonical audit
  report structure (verdict, summary table, findings table, detailed
  findings cards, strengths, score computation, next steps). Consumes the
  same `findings.json` payload as the HTML renderer. Handles both the
  NO-GO branch (BLOCKER warning + numbered remediation roadmap) and the
  GO branch (production-ready acknowledgement + maintenance steps).
- **`references/raml-best-practices.md`** *(materialised in v1.3.0)* —
  Condensed cheat sheet for the auditor: 23-row rules table, layer
  decision tree, verb→layer mapping, remediation snippet palette,
  severity calibration guidance, and score interpretation bands. The
  source of truth for rule IDs remains §2 of this document; the cheat
  sheet is regenerated when §2 changes.
- **`examples/`** *(new in v1.3.0)* — Two reference fixtures and their
  analyzer-generated findings.json snapshots:
  `customerOrderAPI.raml` (deliberately broken, 17 findings, 21/100,
  NO-GO) and `s-customer-orders-api.raml` (clean, 0 findings, 100/100,
  GO). Used for post-install smoke testing and as a regression baseline
  when rule definitions change. See `examples/README.md` for the full
  index and regeneration commands.
- **`scripts/generate_best_practices.py`** *(new in v1.4.0)* — Refactors
  a RAML to resolve every finding from an audit. Takes the source RAML
  + findings.json as input, applies one transformation per rule (skipping
  silently if the finding is absent — idempotent), and writes both the
  refactored RAML and a transformations.json that traces every change.
  Inferences for layer prefix (`s-`/`p-`/`x-`), orchestration-verb
  resolution, and scope naming are heuristic and flagged for human
  review in the transformations log. Run with:
  `python scripts/generate_best_practices.py --raml input.raml --findings findings.json --out-raml refactored.raml --out-transformations transformations.json`.
- **`scripts/render_remediation_guide.py`** *(new in v1.4.0)* — Renders
  the remediation guide (Markdown + HTML) from a transformations.json.
  HTML uses the same v1.3 branded design language adapted for the
  remediation context (kind badges instead of severity pills, before/after
  diff cards, review-flag callouts). Run with:
  `python scripts/render_remediation_guide.py --transformations transformations.json --findings findings.json --out-md guide.md --out-html guide.html`
  (add `--lang fr` for a French guide, §3bis).
- **`templates/remediation-guide.md.j2`** and
  **`templates/remediation-guide.html.j2`** *(new in v1.4.0)* — Jinja2
  templates for the remediation guide. The HTML template reuses 6 of
  the 8 CSS custom properties from `report.html.j2` and adds 3 new
  ones for the kind palette (`--mechanical`, `--heuristic`,
  `--architectural`).

When the user's request maps to one of these resources, view the resource first
and use it as the starting point — do not regenerate from scratch.

---

## §5. Workflow

1. **Receive** the RAML (uploaded file, pasted text, or path). If pasted, save to `/tmp/audit-input.raml`.
2. **Read** `references/raml-best-practices.md` to anchor rule IDs.
3. **Run the `raml-validator` command** from the skill folder:
   `sh bin/raml-validator run <spec.raml> --out-dir /mnt/user-data/outputs [--lang fr] [--api-description "…"]`
   (`audit` for the audit only, `fix` for the refactor and guide only). It
   chains the analyzer, the report, the generator, the guide and the re-audit,
   and names every file after the spec. This step is **mandatory** when the
   command is available in the skill folder
   — never replace it with a direct in-chat audit. The script is the single
   source of truth for the rule mechanics; bypassing it produces findings
   that drift from the analyzer's behaviour and breaks the regression
   baseline in `examples/`. The only acceptable fallback is when the script
   is genuinely missing from the installation (e.g. on a v1.2.0 install
   where only `SKILL.md` is present); in that case, perform a direct audit
   following §2, and tell the user explicitly that the analyzer is missing
   so they can complete the install.
4. **Enrich** with semantic findings (layer alignment, naming intent, business-impact severity adjustments).
5. **Open** `templates/audit-report-template.md` and fill each section.
6. **Compute** the readiness score: start at 100, subtract 15 per BLOCKER, 5 per MAJOR, 2 per MINOR, 0 per INFO. Floor at 0.
7. **Deliver** the report. Starting in v1.3.0, produce both formats by default:
   the Markdown report (for in-chat inspection and version-controlled review)
   and the HTML report (for stakeholder sharing). Both go to
   `/mnt/user-data/outputs/` and are presented to the user via `present_files`.
   If the user explicitly asks for one format only, honour the request.

---

## §6. Anti-patterns to refuse

This skill REFUSES to produce:

- An audit report without severity rankings (defeats the purpose).
- A report in a language other than the target (English by default, French
  on request), or an audit report and a remediation guide of the same run in
  two different languages (violates §3bis).
- An audit that copy-pastes the entire RAML into the report (the user already has it).
- A "looks good to me" verdict without checking the 7 categories explicitly.
- Findings without remediation snippets (every finding gets a fix).
- A score above 80/100 if any BLOCKER is present (mathematically impossible per the scoring rule).
- **A direct in-chat audit when `scripts/audit_raml.py` is available in the
  skill folder** (violates §5.3). The script is mandatory whenever it is
  present. Direct audits are reserved for the genuine fallback case where
  the install is incomplete (only `SKILL.md` present), and even then the
  user must be told the analyzer is missing.

If the user insists on a quick informal review, produce a condensed version (executive summary + top 5 findings only) and flag explicitly: `// NOTE: Quick review mode — full audit recommended before production deployment.`
