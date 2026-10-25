# Test fixtures

The files below are reference inputs and outputs for the
`mulesoft-raml-validator` skill. They serve three purposes:

1. **Smoke test** after installation — verify that `audit_raml.py` and
   `render_report.py` are wired correctly.
2. **Regression baseline** — the broken-RAML findings.json is a known-good
   snapshot of the analyzer's output; if it changes after a code edit, the
   diff is the regression.
3. **Worked example** — show what a NO-GO and a GO audit look like end to
   end, against minimal but realistic specs.

## File index

| File | Purpose | Expected analyzer output |
|---|---|---|
| `customerOrderAPI.raml` | Deliberately broken RAML, ~60 lines, exercises 17 of the 23 rules | 17 findings (2 BLOCKER, 9 MAJOR, 2 MINOR, 4 INFO), score **21/100**, **NO-GO** |
| `customerOrderAPI-findings.json` | Snapshot of the analyzer's output for the file above | — |
| `s-customer-orders-api.raml` | Clean single-file RAML built to pass every rule | 0 findings, score **100/100**, **GO** |
| `s-customer-orders-api-findings.json` | Snapshot of the analyzer's output for the file above | — |

## Smoke test (post-install)

From the skill root directory:

```bash
# Re-run the analyzer on the broken fixture and compare to the snapshot
python scripts/audit_raml.py \
  --raml examples/customerOrderAPI.raml \
  --out /tmp/smoke-broken.json
diff <(jq -S . examples/customerOrderAPI-findings.json) \
     <(jq -S . /tmp/smoke-broken.json)
# Expect: no diff (the only volatile field is 'date', filtered by jq if needed)

# Render the HTML report
python scripts/render_report.py \
  --findings examples/customerOrderAPI-findings.json \
  --out /tmp/smoke-broken.html
# Expect: "Wrote /tmp/smoke-broken.html (17 findings, score 21, NO-GO)"

# Same for the clean fixture
python scripts/audit_raml.py \
  --raml examples/s-customer-orders-api.raml \
  --out /tmp/smoke-clean.json
python scripts/render_report.py \
  --findings examples/s-customer-orders-api-findings.json \
  --out /tmp/smoke-clean.html
# Expect: "Wrote /tmp/smoke-clean.html (0 findings, score 100, GO)"
```

## Regenerating the snapshots

If you change a rule, fix a false-positive, or add a check, the snapshots
must be regenerated **and** the diff inspected by hand to confirm the new
behavior is intentional.

```bash
python scripts/audit_raml.py \
  --raml examples/customerOrderAPI.raml \
  --out examples/customerOrderAPI-findings.json

python scripts/audit_raml.py \
  --raml examples/s-customer-orders-api.raml \
  --out examples/s-customer-orders-api-findings.json
```

The `date` field will change with every regeneration (it carries today's
date). All other fields should be stable across runs.

## Coverage map

The broken fixture exercises 17 of the 22 rules. The 5 rules **not**
exercised (and why):

| Rule | Why not exercised |
|---|---|
| `NAMING-002` | The broken spec uses plural `/customerOrders` and `/users`; the singleton `/{userId}/password` is correctly excluded by the parent-is-URI-param check. |
| `APIC-001` | The broken spec is layer-ambiguous (System-ish), not Experience. `APIC-001` only fires when the title carries the `x-` prefix and a DB-like resource is referenced. |
| `REUSE-002` | Requires schema-shape comparison across responses; not implemented in v1.3.0 (see `SKILL.md` §2 note and CHANGELOG). |
| `SPEC-004` | The broken spec has no inline JSON schemas at all (everything is `type: object` or `type: array`); nothing for the rule to flag. |
| `VER-001` | The broken spec declares `version: v1.2.3` at root, so the rule passes. (`VER-002` and `VER-003` flag the way the version is *used*.) |

If you want the broken fixture to exercise more rules, do not edit it —
add a separate fixture (e.g. `experience-api-bad.raml`) that targets the
specific gap. Keeping each fixture focused makes diff-driven regression
testing tractable.

## Reference demo API (`demo/`) — added in v1.5.0

`demo/` holds a complete, end-to-end worked example on a realistic API — an
employee **Leave Management API** — with every deliverable the skill produces.
It is the reference to read first, and `verify_install.py` (step 7) replays it.

| File | What it is | Expected result |
|---|---|---|
| `demo/leave-management-api.raml` | Input spec, written the way a first draft often is | 16 findings (2 BLOCKER, 8 MAJOR, 2 MINOR, 4 INFO), score **26/100**, **NO-GO** |
| `demo/leave-management-api-findings.json` | Analyzer output for the input | — |
| `demo/leave-management-api-report.html` / `.fr.html` | HTML audit report, English / French | — |
| `demo/leave-management-api-best-practices.raml` | Refactored spec from `generate_best_practices.py` | 0 findings, score **100/100**, **GO** |
| `demo/leave-management-api-best-practices-findings.json` | Re-audit of the refactored spec | — |
| `demo/leave-management-api-transformations.json` | Trace of the 15 transformations applied | — |
| `demo/leave-management-api-remediation-guide.md` / `.html` | Remediation guide (6 items flagged for human review) | — |
| `demo/leave-management-api-remediation-guide.fr.md` / `.fr.html` | Same guide in French | — |

The demo also exercises `NAMING-002` (`/employee` → `/employees`), which the
broken fixture above does not, and checks that singleton sub-resources under a
URI parameter (`/{employeeId}/balance`, `/users/{userId}/password`) are left
singular.

Regenerate it from the skill root with the `raml-validator` command:

```bash
raml-validator run examples/demo/leave-management-api.raml --out-dir examples/demo
FR="Gestion des congés des employés. Les employés déposent leurs demandes de congé (payé, maladie ou sans solde) et en suivent le statut ; les managers les approuvent ; chacun peut consulter le solde de congés restant d'un employé."
raml-validator run examples/demo/leave-management-api.raml --out-dir examples/demo --lang fr --api-description "$FR"
```

The same, script by script (what the command runs):

```bash
cd examples/demo
python ../../scripts/audit_raml.py --raml leave-management-api.raml --out leave-management-api-findings.json
python ../../scripts/render_report.py --findings leave-management-api-findings.json --out leave-management-api-report.html
python ../../scripts/generate_best_practices.py --raml leave-management-api.raml --findings leave-management-api-findings.json --out-raml leave-management-api-best-practices.raml --out-transformations leave-management-api-transformations.json
python ../../scripts/audit_raml.py --raml leave-management-api-best-practices.raml --out leave-management-api-best-practices-findings.json
python ../../scripts/render_remediation_guide.py --transformations leave-management-api-transformations.json --findings leave-management-api-findings.json --out-md leave-management-api-remediation-guide.md --out-html leave-management-api-remediation-guide.html
FR="Gestion des congés des employés. Les employés déposent leurs demandes de congé (payé, maladie ou sans solde) et en suivent le statut ; les managers les approuvent ; chacun peut consulter le solde de congés restant d'un employé."
python ../../scripts/render_report.py --findings leave-management-api-findings.json --out leave-management-api-report.fr.html --lang fr --api-description "$FR"
python ../../scripts/render_remediation_guide.py --transformations leave-management-api-transformations.json --findings leave-management-api-findings.json --out-md leave-management-api-remediation-guide.fr.md --out-html leave-management-api-remediation-guide.fr.html --lang fr --api-description "$FR"
```
