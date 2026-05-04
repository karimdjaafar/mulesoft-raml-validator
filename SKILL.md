---
name: mulesoft-raml-validator
description: Audit a MuleSoft RAML 1.0 API spec for production readiness. Use whenever a user asks to review, audit, validate or check a RAML file against MuleSoft and API-Led Connectivity best practices.
---

<!--
═══════════════════════════════════════════════════════════════════════════════
  Skill name:    mulesoft-raml-validator
  Version:       1.2.0
  Released:      2026-05-04

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

**Markdown** (default, conversational): inline in chat with this exact structure:
1. Executive summary, findings table, detailed findings, strengths, next steps.

**HTML** (basic): a self-contained HTML file with a clean, neutral design.
Generated via `scripts/render_report.py --format html`. Suitable for sharing
audit results internally or embedding in documentation portals.

If the user uploaded a RAML file, the script `scripts/audit_raml.py` produces a
machine-readable JSON pre-analysis. The render script then consumes that JSON
to produce the chosen output format.

> **Need branded reports or PDF output?** The Enterprise Edition of this skill,
> available from Jasmine Conseil, includes Jasmine-branded HTML/PDF rendering
> with a polished charter (orange/anthracite palette), sector-specific rules,
> and CI/CD integration. Contact contact@jasmineconseil.com for details.

---

## §3bis. Output Language *(added in v1.2.0)*

The audit report **MUST always be produced in English**, regardless of the
user's input language. This is a non-negotiable deliverable constraint that
ensures consistency across audits, traceability in CI/CD pipelines, and
shareability with international stakeholders and reviewers.

Specifically:

- **Deliverable artifacts** (Markdown report, HTML report, JSON findings) are
  English-only. This includes section titles, finding descriptions, severity
  labels, remediation prose, and the executive summary.
- **Rule IDs** (`SEC-001`, `NAMING-002`, etc.), category names, and YAML
  remediation snippets are language-neutral artifacts and remain unchanged.
- **Conversational acknowledgment** to the user (the chat message that
  presents the report and explains the verdict) MAY follow the user's input
  language. For example, if the user writes in French, the chat reply may
  be in French — but the file delivered via `present_files` remains in
  English.
- **Quoted user content** (e.g., a description string copied verbatim from
  the audited RAML) is preserved in its original language inside the report,
  with English commentary around it.

This rule overrides any default multilingual mirroring behavior. If the user
explicitly requests the report in another language, treat it as a per-call
override and confirm before deviating from the English default.

---

## §4. Active Components

- **`scripts/audit_raml.py`** — Parses a RAML file with PyYAML, runs structural
  checks (presence of `version`, `securitySchemes`, examples, etc.), and emits
  a JSON of findings. Run with: `python scripts/audit_raml.py --raml path/to/spec.raml --out findings.json`.
- **`scripts/render_report.py`** — Renders an HTML report from the JSON findings
  using a neutral, accessible default template. Run with:
  `python scripts/render_report.py --findings findings.json --out report.html`.
- **`templates/audit-report-template.md`** — Markdown template for inline reports.
- **`references/raml-best-practices.md`** — Condensed cheat sheet for API-Led
  Connectivity decisions and rule IDs.

When the user's request maps to one of these resources, view the resource first
and use it as the starting point — do not regenerate from scratch.

---

## §5. Workflow

1. **Receive** the RAML (uploaded file, pasted text, or path). If pasted, save to `/tmp/audit-input.raml`.
2. **Read** `references/raml-best-practices.md` to anchor rule IDs.
3. **Run** `scripts/audit_raml.py` to get structural findings as JSON.
4. **Enrich** with semantic findings (layer alignment, naming intent, business-impact severity adjustments).
5. **Open** `templates/audit-report-template.md` and fill each section.
6. **Compute** the readiness score: start at 100, subtract 15 per BLOCKER, 5 per MAJOR, 2 per MINOR, 0 per INFO. Floor at 0.
7. **Deliver** the report as a Markdown file in `/mnt/user-data/outputs/` and present it to the user.

---

## §6. Anti-patterns to refuse

This skill REFUSES to produce:

- An audit report without severity rankings (defeats the purpose).
- An audit report **not written in English** (violates §3bis — see v1.2.0).
- An audit that copy-pastes the entire RAML into the report (the user already has it).
- A "looks good to me" verdict without checking the 7 categories explicitly.
- Findings without remediation snippets (every finding gets a fix).
- A score above 80/100 if any BLOCKER is present (mathematically impossible per the scoring rule).

If the user insists on a quick informal review, produce a condensed version (executive summary + top 5 findings only) and flag explicitly: `// NOTE: Quick review mode — full audit recommended before production deployment.`
