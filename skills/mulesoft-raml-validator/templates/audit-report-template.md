{# ===========================================================================
   audit-report-template.md — Markdown report template

   Used by:  §5.5 (fill each section) and §5.7 (deliver the Markdown report)
   Renders:  the same Markdown structure as the canonical audit produced for
             the customerOrderAPI spec — verdict line, summary table, findings
             table, detailed findings, strengths, score computation, next steps

   Two ways to use this file:

   1. Programmatic (preferred): pass it through Jinja2 with the same payload
      shape that scripts/render_report.py consumes — see the rendering
      example in references/raml-best-practices.md.

   2. Manual: copy this file, strip the Jinja control blocks (everything
      between curly-percent and percent-curly, plus the curly-hash comments)
      and fill the double-curly placeholders by hand. The structure
      (headings, table columns, finding card layout) is the contract — keep
      it identical so reports remain comparable across audits.

   The template never invents content. Every placeholder maps 1:1 to a field
   produced by audit_raml.py. If a field is missing, the template emits a
   sensible default rather than failing.
=========================================================================== #}
# {{ report.title | default("RAML Audit Report") }}

**Spec audited:** `{{ report.spec_path | default("(unspecified)") }}`
**Audit date:** {{ report.date }}
**Skill:** {{ report.skill_version | default("mulesoft-raml-validator v1.3.0") }}
**Verdict:** {{ "🟢 **GO for production**" if report.verdict == "GO" else "🔴 **NO-GO for production**" }}
**Readiness score:** **{{ report.score }} / 100**

---

## 1. Executive Summary

{# The executive summary is the only free-form section. It is filled by the
   auditor based on the dominant findings. Two paragraphs maximum:
   - paragraph 1: what is wrong at the top level (BLOCKERs, structural issues)
   - paragraph 2: what is right and what the remediation effort looks like
   When rendered programmatically without an auditor narrative, fall back to
   a templated summary derived from the findings counts. #}
{% if report.executive_summary %}
{{ report.executive_summary }}
{% else %}
This audit reports {{ totals.total }} finding{{ "s" if totals.total != 1 else "" }} against the specification at `{{ report.spec_path }}`:
{{ totals.blocker }} BLOCKER{{ "s" if totals.blocker != 1 else "" }},
{{ totals.major }} MAJOR{{ "s" if totals.major != 1 else "" }},
{{ totals.minor }} MINOR{{ "s" if totals.minor != 1 else "" }}, and
{{ totals.info }} INFO finding{{ "s" if totals.info != 1 else "" }}.
{% if totals.blocker > 0 %}
The presence of {{ totals.blocker }} BLOCKER finding{{ "s" if totals.blocker != 1 else "" }} alone is sufficient to fail the audit, regardless of the rest of the spec. These must be resolved before any further review.
{% elif totals.total == 0 %}
The spec passes every rule in §2 — production-ready as-is. No remediation is required.
{% elif report.score >= 80 %}
The spec is production-ready with cosmetic refinements. Address the listed findings and ship.
{% else %}
The spec is not yet production-ready, but no BLOCKERs are present. Remediation is mechanical and follows the snippets attached to each finding.
{% endif %}
{% endif %}

| Category | BLOCKER | MAJOR | MINOR | INFO |
|---|---:|---:|---:|---:|
{% for row in matrix -%}
| {{ row.name }}{% if row.suffix %} ({{ row.suffix }}){% endif %} | {{ row.blocker }} | {{ row.major }} | {{ row.minor }} | {{ row.info }} |
{% endfor -%}
| **Totals** | **{{ totals.blocker }}** | **{{ totals.major }}** | **{{ totals.minor }}** | **{{ totals.info }}** |

---

## 2. Findings Table

{% if findings %}
| # | Severity | Rule | Location | Summary |
|---|---|---|---|---|
{% for f in findings -%}
| {{ loop.index }} | {{ "🔴 BLOCKER" if f.severity == "BLOCKER" else ("🟠 MAJOR" if f.severity == "MAJOR" else ("🟡 MINOR" if f.severity == "MINOR" else "⚪ INFO")) }} | `{{ f.rule }}` | {{ f.location }} | {{ f.summary }} |
{% endfor %}
{% else %}
_No findings — the spec passes every rule in §2._
{% endif %}

---

## 3. Detailed Findings

{% if not findings %}
_Nothing to detail. The spec passes every rule._
{% else %}
{% for f in findings %}
### {{ "🔴 BLOCKER" if f.severity == "BLOCKER" else ("🟠 MAJOR" if f.severity == "MAJOR" else ("🟡 MINOR" if f.severity == "MINOR" else "⚪ INFO")) }} · `{{ f.rule }}` — {{ f.summary }}

**Location:** {{ f.location }}
{% if f.impact %}
**Impact:** {{ f.impact }}
{% endif %}
{% if f.remediation_text %}

**Remediation:** {{ f.remediation_text }}
{% endif %}
{% if f.remediation_code %}

**Remediation:**
```yaml
{{ f.remediation_code }}
```
{% endif %}

---
{% endfor %}
{% endif %}

## 4. Strengths

{# Strengths are recorded by the auditor based on what the spec does right.
   Even on a low-scoring audit, naming this list explicitly is important —
   it prevents the report from reading as purely punitive and tells the
   author what *not* to change. #}
{% if report.strengths %}
{% for s in report.strengths %}
- ✅ {{ s }}
{% endfor %}
{% else %}
_No strengths recorded for this audit. (The auditor has not filled this section, or the spec is in a state where remediation precedes reinforcement.)_
{% endif %}

---

## 5. Score Computation

Per the §5.6 scoring rule: start at 100, subtract 15 per BLOCKER, 5 per MAJOR, 2 per MINOR, 0 per INFO; floor at 0.

| Severity | Count | Penalty per finding | Subtotal |
|---|---:|---:|---:|
| BLOCKER | {{ totals.blocker }} | × 15 | −{{ totals.blocker * 15 }} |
| MAJOR | {{ totals.major }} | × 5 | −{{ totals.major * 5 }} |
| MINOR | {{ totals.minor }} | × 2 | −{{ totals.minor * 2 }} |
| INFO | {{ totals.info }} | × 0 | 0 |
|  |  | **Total penalty** | **−{{ totals.blocker * 15 + totals.major * 5 + totals.minor * 2 }}** |

**Final score: 100 − {{ totals.blocker * 15 + totals.major * 5 + totals.minor * 2 }} = {{ report.score }} / 100**

GO requires score ≥ 80 **and** zero BLOCKERs. Verdict: **{{ report.verdict }}**.

---

## 6. Next Steps

{# Next steps are the remediation roadmap, ordered by leverage rather than by
   severity. The auditor fills this with 4–7 numbered actions; the template
   provides a sensible default ordering when no narrative is supplied. #}
{% if report.next_steps %}
{% for step in report.next_steps %}
{{ loop.index }}. {{ step }}
{% endfor %}
{% elif totals.total == 0 %}
1. **Maintain the bar.** Re-run this audit on every spec change and gate merges on a GO verdict.
2. **Track drift.** When the rule set evolves (new minor/major version of the skill), re-audit existing specs to catch newly-introduced findings.
{% else %}
{% if totals.blocker > 0 %}
1. **Resolve every BLOCKER first.** See §3 above for remediation snippets. Without this, no other improvement matters — the spec cannot ship.
{% endif %}
{% if matrix | selectattr("major", "gt", 0) | list | length > 0 %}
{{ "2" if totals.blocker > 0 else "1" }}. **Address MAJOR findings by category**, in this order: Security → Spec → API-Led layer → Naming → Reuse → Versioning → Documentation. Within a category, fix the rule that affects the most endpoints first.
{% endif %}
{{ "3" if totals.blocker > 0 else "2" }}. **Apply MINOR refinements** once MAJORs are clear. These are usually one-line edits.
{{ "4" if totals.blocker > 0 else "3" }}. **Re-run this audit.** Target ≥ 80/100 before promoting to QA. The analyzer at `scripts/audit_raml.py` is idempotent; you can run it as a pre-commit hook or in CI.
{{ "5" if totals.blocker > 0 else "4" }}. **Add a `documentation:` section** if not already present. Even when not strictly required, a 3-paragraph onboarding guide measurably improves Anypoint Exchange consumption.
{% endif %}

---

{# Footer — kept minimal. The HTML report has its own footer; the Markdown
   one stays unobtrusive so the file reads cleanly when version-controlled. #}
*Generated by `{{ report.skill_version | default("mulesoft-raml-validator v1.3.0") }}` · {{ report.date }}*
