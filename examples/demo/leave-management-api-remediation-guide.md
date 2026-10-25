# Remediation guide — s-leave-management-api

**Source RAML:** `leave-management-api.raml`
**Refactored RAML:** `leave-management-api-best-practices.raml`
**Generated:** 2026-10-25
**Skill:** mulesoft-raml-validator v1.4.2


**API under audit:** Leave Management API (v1.0.3) — layer not declared

> Employee leave management. Employees submit leave requests (paid, sick or unpaid) and follow their status; managers approve them; everyone can check the remaining leave balance of an employee.

6 resources, 6 operations · base URI `https://api.demo.jasmineconseil.com/leaves`

---

## 1. Executive Summary

This guide documents the transformations applied to refactor the source RAML.
The original audit recorded **16 findings** with a score
of **26/100**. After applying the transformations described
below, the refactored RAML is expected to score **100/100** (verify by
re-running `audit_raml.py` on the refactored output).

A total of **15 transformations** were applied:

- 9 **mechanical** — deterministic fixes with high confidence (renames, format normalization, structural insertions).
- 6 **heuristic** — context-aware choices that are reasonable defaults but should be reviewed (placeholder examples, generated descriptions, default URIs).
- 0 **architectural** — significant choices about API layering or naming that have multiple valid alternatives.

**Inferred API layer:** `s-` — Default to System (s-) layer for noun-shaped resource specs; consider 'p-' or 'x-' if the API orchestrates or serves a specific channel

> ⚠ **6 transformations
> need human review** (heuristic
> or architectural choices, or low-confidence outputs). They are flagged
> individually in §3 below.

---

## 2. Transformations Table

| # | Rule | Kind | Confidence | Summary |
|---|---|---|---|---|
| 1 | `NAMING-001` | Mechanical | high | /leaveRequests → /leave-requests |
| 2 | `NAMING-002` | Mechanical | high | /employee → /employees |
| 3 | `NAMING-003` | Mechanical | high | GET /leave-requests?page_size → GET /leave-requests?pageSize |
| 4 | `NAMING-003` | Mechanical | high | GET /employees/{employeeId}/balance?page_size → GET /employees/{employeeId}/balance?pageSize |
| 5 | `NAMING-004` | Heuristic | medium | title: Leave Management API → title: s-leave-management-api |
| 6 | `VER-002` | Mechanical | high | baseUri: https://api.demo.jasmineconseil.com/leaves → baseUri: https://api.demo.jasmineconseil.com/le... |
| 7 | `VER-003` | Mechanical | high | version: v1.0.3 → version: v1 |
| 8 | `DOC-002` | Mechanical | high | 6 resources without description → all 6 resources now have a one-line description |
| 9 | `DOC-003` | Heuristic | medium | (no documentation section) → documentation: [Overview, Getting started, Error model] |
| 10 | `SEC-001` | Heuristic | medium | (no securitySchemes, no root securedBy) → OAuth 2.0 scheme + root securedBy: [ oauth_2_0 ] |
| 11 | `SPEC-003` | Mechanical | high | No 4xx/5xx responses defined on any endpoint → standardErrors trait defined and applied to 6 methods |
| 12 | `REUSE-001` | Mechanical | high | 2 GET methods with inline page/pageSize → pageable trait defined and applied to 2 methods |
| 13 | `SPEC-001` | Heuristic | low | 1 request bodies without example → placeholder examples added to 1 request bodies |
| 14 | `SPEC-002` | Heuristic | low | 3 response bodies without example → placeholder examples added to 3 response bodies |
| 15 | `SEC-002` | Heuristic | medium | 1 sensitive endpoints with no per-method securedBy → PUT /users/{userId}/password → scope 'users:cre... |

---

## 3. Detailed Transformations

### 1. `NAMING-001` — Mechanical (high)

**Before:**
```
/leaveRequests
```

**After:**
```
/leave-requests
```

**Reasoning:** Resource paths must be kebab-case (lowercase, hyphen-separated).


---
### 2. `NAMING-002` — Mechanical (high)

**Before:**
```
/employee
```

**After:**
```
/employees
```

**Reasoning:** Collection resources must be plural nouns.


---
### 3. `NAMING-003` — Mechanical (high)

**Before:**
```
GET /leave-requests?page_size
```

**After:**
```
GET /leave-requests?pageSize
```

**Reasoning:** Query parameters must be camelCase.


---
### 4. `NAMING-003` — Mechanical (high)

**Before:**
```
GET /employees/{employeeId}/balance?page_size
```

**After:**
```
GET /employees/{employeeId}/balance?pageSize
```

**Reasoning:** Query parameters must be camelCase.


---
### 5. `NAMING-004` — Heuristic (medium)

**Before:**
```
title: Leave Management API
```

**After:**
```
title: s-leave-management-api
```

**Reasoning:** Layer inferred: 's-'. Default to System (s-) layer for noun-shaped resource specs; consider 'p-' or 'x-' if the API orchestrates or serves a specific channel

> 🔍 **Please review.** This transformation applied a sensible default but
> the value is generic; replace with domain-specific content before
> production deployment.

---
### 6. `VER-002` — Mechanical (high)

**Before:**
```
baseUri: https://api.demo.jasmineconseil.com/leaves
```

**After:**
```
baseUri: https://api.demo.jasmineconseil.com/leaves/{version}
```

**Reasoning:** Version placeholder interpolated so consumers can pin to a major version via the URL.


---
### 7. `VER-003` — Mechanical (high)

**Before:**
```
version: v1.0.3
```

**After:**
```
version: v1
```

**Reasoning:** URI version reduced to major level; patch/minor levels belong in the changelog and response headers, not the URL.


---
### 8. `DOC-002` — Mechanical (high)

**Before:**
```
6 resources without description
```

**After:**
```
all 6 resources now have a one-line description
```

**Reasoning:** Auto-generated descriptions; edit them to capture domain-specific intent.


---
### 9. `DOC-003` — Heuristic (medium)

**Before:**
```
(no documentation section)
```

**After:**
```
documentation: [Overview, Getting started, Error model]
```

**Reasoning:** Skeleton documentation section added with three standard chapters. Edit each chapter to add domain-specific content.

> 🔍 **Please review.** This transformation applied a sensible default but
> the value is generic; replace with domain-specific content before
> production deployment.

---
### 10. `SEC-001` — Heuristic (medium)

**Before:**
```
(no securitySchemes, no root securedBy)
```

**After:**
```
OAuth 2.0 scheme + root securedBy: [ oauth_2_0 ]
```

**Reasoning:** OAuth 2.0 added with placeholder authorization/token URIs. Replace these with the real identity-provider URLs before deploying.

> 🔍 **Please review.** This transformation applied a sensible default but
> the value is generic; replace with domain-specific content before
> production deployment.

---
### 11. `SPEC-003` — Mechanical (high)

**Before:**
```
No 4xx/5xx responses defined on any endpoint
```

**After:**
```
standardErrors trait defined and applied to 6 methods
```

**Reasoning:** Single trait defining 400/401/403/404/429/500 ensures every method has a complete error contract.


---
### 12. `REUSE-001` — Mechanical (high)

**Before:**
```
2 GET methods with inline page/pageSize
```

**After:**
```
pageable trait defined and applied to 2 methods
```

**Reasoning:** Pagination parameters factored into a single reusable trait; future changes to defaults or limits propagate everywhere.


---
### 13. `SPEC-001` — Heuristic (low — please review)

**Before:**
```
1 request bodies without example
```

**After:**
```
placeholder examples added to 1 request bodies
```

**Reasoning:** Generic placeholder examples added; replace with realistic domain-specific values to make Mocking Service useful.

> 🔍 **Please review.** This transformation applied a sensible default but
> the value is generic; replace with domain-specific content before
> production deployment.

---
### 14. `SPEC-002` — Heuristic (low — please review)

**Before:**
```
3 response bodies without example
```

**After:**
```
placeholder examples added to 3 response bodies
```

**Reasoning:** Generic placeholder examples added; replace with realistic domain-specific values.

> 🔍 **Please review.** This transformation applied a sensible default but
> the value is generic; replace with domain-specific content before
> production deployment.

---
### 15. `SEC-002` — Heuristic (medium)

**Before:**
```
1 sensitive endpoints with no per-method securedBy
```

**After:**
```
PUT /users/{userId}/password → scope 'users:credentials:write'
```

**Reasoning:** Scoped securedBy added per sensitive endpoint with a narrow scope inferred from the path. Verify the scope name matches your identity-provider configuration.

> 🔍 **Please review.** This transformation applied a sensible default but
> the value is generic; replace with domain-specific content before
> production deployment.

---

## 4. Next Steps

1. **Review the refactored RAML** (`leave-management-api-best-practices.raml`). Pay special
   attention to the 6 transformations
   flagged for review in §3.
2. **Replace placeholder values.** Auto-generated descriptions (DOC-001, DOC-002,
   DOC-003), authentication URIs (SEC-001), and example payloads (SPEC-001,
   SPEC-002) are intentionally generic — they meet the rule requirements but
   carry no domain meaning. Replace them.
3. **Verify scope names** if SEC-002 was applied. The generator infers scope
   names from path tokens (e.g. `/users/{id}/password` → `users:credentials:write`).
   Confirm these match the names registered in your identity provider.
4. **Re-audit the refactored RAML** with `scripts/audit_raml.py` to confirm
   a 100/100 GO verdict. If anything other than 100 appears, file a bug — the
   round-trip should always close.
5. **Commit both files together** — the refactored RAML and this guide. The
   guide is the changelog of the refactor and tells future readers why each
   change was made.

---

*Generated by mulesoft-raml-validator v1.4.2 · 2026-10-25*