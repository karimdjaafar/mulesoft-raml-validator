# RAML Audit Report — `bad-customer-orders.raml`

**Audited file:** `bad-customer-orders.raml`
**API title (declared):** `customerOrderAPI`
**Declared version:** `v1.2.3`
**Audit date:** 2026-05-04
**Audit standard:** MuleSoft RAML 1.0 + API-Led Connectivity best practices
**Auditor skill:** `mulesoft-raml-validator` v1.2.0

---

## 1. Executive Summary

This RAML specification is **not production-ready**. The audit identified **2 BLOCKERs**, **9 MAJORs**, and **3 MINORs** across all seven audit categories, including a complete absence of security declarations and no documented error responses. Beyond mechanical violations, the API also exhibits a **layer-identity problem**: the title and most resources resemble a System API, yet `/payment-process` is an orchestration verb that belongs to a Process API — the spec straddles two API-Led Connectivity layers without committing to either.

| Metric | Value |
|---|---|
| **Readiness score** | **19 / 100** |
| **Verdict** | 🛑 **NO-GO — do not publish to Anypoint Exchange or deploy** |
| **BLOCKERs** | 2 |
| **MAJORs** | 9 |
| **MINORs** | 3 |
| **INFOs** | 4 |
| **Estimated remediation effort** | ~1 to 1.5 day for a single developer |

The spec is **structurally parseable** but would fail a peer review, a security review, and an Anypoint Exchange publication checklist. Recommended action: do **not** use this RAML as a contract for downstream implementation; remediate the BLOCKERs and MAJORs first, then re-audit.

---

## 2. Findings Table

| # | ID | Severity | Category | Location | One-line summary |
|---|---|---|---|---|---|
| 1 | `SEC-001` | 🛑 BLOCKER | Security | root | No `securitySchemes` and no `securedBy:` — the API is fully open. |
| 2 | `SPEC-003` | 🛑 BLOCKER | Examples & schemas | all endpoints | No `4xx`/`5xx` responses defined anywhere. |
| 3 | `NAMING-001` | ⚠️ MAJOR | Naming | `/customerOrders` (line 9) | Resource uses camelCase instead of kebab-case. |
| 4 | `NAMING-004` | ⚠️ MAJOR | Naming | `title:` (line 2) | Title doesn't follow `s-`/`p-`/`x-` API-Led prefix convention. |
| 5 | `APIC-002` | ⚠️ MAJOR | API-Led layer | `/payment-process` (line 41) | Orchestration verb in resource name suggests Process layer intent in an otherwise System-style spec. |
| 6 | `REUSE-001` | ⚠️ MAJOR | Reuse | `/customerOrders`, `/users` | Pagination repeated on 2+ resources without a `trait`. |
| 7 | `SPEC-001` | ⚠️ MAJOR | Examples & schemas | POST/PUT bodies | No `example` on any request body. |
| 8 | `SPEC-002` | ⚠️ MAJOR | Examples & schemas | all responses | No `example` on any response body. |
| 9 | `SEC-002` | ⚠️ MAJOR | Security | `/payment-process` POST, `/users/{userId}/password` PUT | Sensitive endpoints (`payment`, `password`) without explicit `securedBy:`. |
| 10 | `VER-002` | ⚠️ MAJOR | Versioning | `baseUri` (line 4) | `{version}` placeholder absent from `baseUri`. |
| 11 | `DOC-001` | ⚠️ MAJOR | Documentation | root `description:` (line 7) | Root description is 16 characters — far below the 50-character minimum. |
| 12 | `NAMING-003` | 🔵 MINOR | Naming | `sort_by` (line 12) | Query parameter uses snake_case instead of camelCase. |
| 13 | `REUSE-003` | 🔵 MINOR | Reuse | root | Common security scheme not declared at root via `securedBy:`. |
| 14 | `DOC-002` | 🔵 MINOR | Documentation | every resource | No resource-level `description:` field anywhere. |
| 15 | `APIC-003` | ⚪ INFO | API-Led layer | `title:` | Title should start with `s-`/`p-`/`x-` for instant layer identification. |
| 16 | `VER-003` | ⚪ INFO | Versioning | `version:` (line 3) | Avoid patch-level versions (`v1.2.3`) in the public version string — use `v1`. |
| 17 | `SEC-003` | ⚪ INFO | Security | — | OAuth 2.0 should be preferred over basic auth for production APIs. |
| 18 | `DOC-003` | ⚪ INFO | Documentation | root | No `documentation:` section with usage examples or onboarding guide. |

---

## 3. Detailed Findings

### 🛑 BLOCKER — `SEC-001` · No security declared at all

**Location:** root of the RAML
**Why it matters:** The spec defines no `securitySchemes` and applies no `securedBy:` anywhere. As written, every operation — including `POST /payment-process` and `PUT /users/{userId}/password` — is publicly callable. This is a contract-level vulnerability: anyone implementing against this RAML would be implementing an open API. This alone disqualifies the spec from production.

**Remediation:**

```yaml
#%RAML 1.0
title: s-customer-orders-api
version: v1
baseUri: https://api.jasmine-conseil.com/{version}/customer-orders

securitySchemes:
  oauth2:
    type: OAuth 2.0
    settings:
      authorizationUri: https://login.jasmine-conseil.com/oauth/authorize
      accessTokenUri: https://login.jasmine-conseil.com/oauth/token
      authorizationGrants: [ client_credentials, authorization_code ]
      scopes: [ orders:read, orders:write, payments:execute, users:admin ]

securedBy: [ oauth2 ]
```

---

### 🛑 BLOCKER — `SPEC-003` · No `4xx`/`5xx` responses documented

**Location:** every operation in the spec (`GET /customerOrders`, `POST /customerOrders`, `GET /customerOrders/{orderId}`, `POST /payment-process`, `GET /users`, `PUT /users/{userId}/password`)
**Why it matters:** Consumers receive zero contract for error handling. They cannot generate typed error clients, cannot anticipate rate-limit responses, and cannot distinguish a transient `503` from a permanent `400`. Per the audit standard, every endpoint must document at least `400`, `401`, `404`, and `500`.

**Remediation (extract to a `traits/standard-errors.raml` or use a global trait):**

```yaml
traits:
  standardErrors:
    responses:
      400:
        description: Validation error
        body:
          application/json:
            type: ErrorResponse
            example: { code: "VALIDATION_FAILED", message: "Field 'orderId' is required" }
      401:
        description: Authentication required
        body:
          application/json:
            type: ErrorResponse
            example: { code: "UNAUTHORIZED", message: "Missing or invalid token" }
      404:
        description: Resource not found
        body:
          application/json:
            type: ErrorResponse
            example: { code: "NOT_FOUND", message: "Order 12345 not found" }
      500:
        description: Internal server error
        body:
          application/json:
            type: ErrorResponse
            example: { code: "INTERNAL", message: "Unexpected error — correlation id abc-123" }

/customer-orders:
  get:
    is: [ standardErrors ]
```

---

### ⚠️ MAJOR — `NAMING-001` · Resource uses camelCase

**Location:** line 9, `/customerOrders`
**Why it matters:** REST conventions and the Anypoint API Designer linter both expect kebab-case in URI segments. URLs are case-sensitive; mixed-case resources cause downstream client bugs and break the consistency expected at the Exchange-portal level.

**Remediation:**

```yaml
# Replace
/customerOrders:

# With
/customer-orders:
```

---

### ⚠️ MAJOR — `NAMING-004` · Title does not follow API-Led prefix convention

**Location:** line 2, `title: customerOrderAPI`
**Why it matters:** The current title is camelCase, singular, and carries no layer information. In an API-Led Connectivity portfolio, a reader should know within a glance whether they are looking at a System, Process, or Experience API. The title is also an Exchange asset name — it propagates to every published version.

**Remediation:** Decide the layer first (see `APIC-002` below), then rename:

```yaml
# If System layer (entity-level access to the orders system of record):
title: s-orders-api

# If Process layer (orchestrates orders + payment + user):
title: p-order-fulfillment-api
```

---

### ⚠️ MAJOR — `APIC-002` · Orchestration verb in a System-shaped API

**Location:** line 41, `/payment-process`
**Why it matters:** `/payment-process` is a **verb-named** resource, which is the textbook signature of a Process API operation. The rest of the spec (`/customerOrders`, `/users`) is entity-shaped, which is System-API style. Mixing the two in the same RAML is a layer-identity violation: it forces Process logic to live alongside SoR access, which defeats the purpose of API-Led layering and creates tight coupling between business orchestration and underlying system data.

**Remediation:** Pick one of two paths.

**Option A — Keep this as a System API** (recommended given the entity resources):

```yaml
# Remove /payment-process entirely from this RAML.
# Move the orchestration to a separate Process API:
#   p-payment-execution-api  →  composes s-orders-api + s-payments-api + s-customers-api
```

**Option B — Convert the whole spec to a Process API:**

```yaml
title: p-order-fulfillment-api
# Then /payment-process becomes legitimate as one orchestration step,
# but /users and /customer-orders should be removed in favor of capability-named
# resources like /order-fulfillments and /payment-executions.
```

---

### ⚠️ MAJOR — `REUSE-001` · Pagination duplicated without a trait

**Location:** `/customerOrders` (lines 11–17) and `/users` (lines 54–58)
**Why it matters:** The same `page` / `pageSize` query parameters are declared twice. When (not if) pagination semantics evolve — adding a `cursor`, a `Link` header, a `total` count — every duplicate must be edited in lockstep. A trait fixes this once.

**Remediation:**

```yaml
traits:
  paginated:
    queryParameters:
      page:
        type: integer
        minimum: 1
        default: 1
        example: 1
      pageSize:
        type: integer
        minimum: 1
        maximum: 200
        default: 50
        example: 50

/customer-orders:
  get:
    is: [ paginated ]

/users:
  get:
    is: [ paginated ]
```

---

### ⚠️ MAJOR — `SPEC-001` · No examples on any request body

**Location:** `POST /customerOrders` (line 24), `POST /payment-process` (line 43), `PUT /users/{userId}/password` (line 65)
**Why it matters:** Consumers and the mocking service in Anypoint API Designer cannot produce realistic test payloads. Examples are also the primary onboarding artifact for downstream developers reading the Exchange portal.

**Remediation:**

```yaml
post:
  body:
    application/json:
      type: NewOrder
      example:
        customerId: "CUST-00042"
        items:
          - sku: "SKU-1234"
            quantity: 2
            unitPrice: 19.99
        shippingAddress:
          line1: "12 rue de la Liberté"
          city: "Dakar"
          country: "SN"
```

---

### ⚠️ MAJOR — `SPEC-002` · No examples on any response body

**Location:** every response in the file
**Why it matters:** Same reasoning as `SPEC-001`, applied to the response side. Without response examples, the mocking service returns empty objects/arrays, and consumer integration tests cannot be written ahead of the implementation.

**Remediation:**

```yaml
responses:
  200:
    body:
      application/json:
        type: Order[]
        example:
          - orderId: "ORD-00001"
            customerId: "CUST-00042"
            status: "CONFIRMED"
            total: 39.98
          - orderId: "ORD-00002"
            customerId: "CUST-00043"
            status: "SHIPPED"
            total: 120.00
```

---

### ⚠️ MAJOR — `SEC-002` · Sensitive endpoints with no `securedBy:`

**Location:** `POST /payment-process` (line 42), `PUT /users/{userId}/password` (line 65)
**Why it matters:** Both endpoints touch payment and credential surfaces. Even after fixing `SEC-001` with a root-level `securedBy:`, sensitive endpoints deserve an **explicit** declaration so the security posture is auditable directly at the operation level. Implicit inheritance is too easy to lose during refactoring.

**Remediation:**

```yaml
/payment-executions:        # renamed to drop the orchestration verb
  post:
    securedBy: [ oauth2: { scopes: [ payments:execute ] } ]
    # ...

/users/{userId}/password:
  put:
    securedBy: [ oauth2: { scopes: [ users:admin ] } ]
    # ...
```

---

### ⚠️ MAJOR — `VER-002` · `{version}` missing from `baseUri`

**Location:** line 4, `baseUri: https://api.jasmine-conseil.com/customer-orders`
**Why it matters:** Without `{version}` in the URI, breaking changes cannot coexist with the previous major version. Consumers are forced to migrate atomically, which is rarely possible in production portfolios.

**Remediation:**

```yaml
version: v1
baseUri: https://api.jasmine-conseil.com/{version}/customer-orders
```

---

### ⚠️ MAJOR — `DOC-001` · Root description is too short

**Location:** line 7, `description: API for orders.`
**Why it matters:** The current description is 16 characters; the standard requires at least 50. The root description is the first paragraph a consumer reads on Exchange — it must communicate scope, layer, and consumer audience.

**Remediation:**

```yaml
description: |
  System API exposing the orders system of record (Salesforce Commerce Cloud).
  Provides CRUD access to customer orders for downstream Process and Experience
  APIs. Not intended for direct consumption by end-user applications — use the
  p-order-fulfillment-api or x-mobile-orders-api instead.
```

---

### 🔵 MINOR — `NAMING-003` · Query parameter in snake_case

**Location:** line 12, `sort_by`
**Why it matters:** Inconsistent with the other parameters in the same operation (`page`, `pageSize`) which use camelCase. Pick one convention; the audit standard is camelCase.

**Remediation:**

```yaml
queryParameters:
  sortBy:
    type: string
    enum: [ createdAt, total, status ]
    default: createdAt
```

---

### 🔵 MINOR — `REUSE-003` · No root-level `securedBy:`

**Location:** root
**Why it matters:** Once `SEC-001` is fixed by declaring a `securitySchemes` block, the cleanest pattern is to apply the default scheme at the root via `securedBy:` and override only when an endpoint deviates. This minimizes copy-paste and makes the open endpoints (if any) visually obvious.

**Remediation:** see the snippet under `SEC-001` (the `securedBy: [ oauth2 ]` line at the root).

---

### 🔵 MINOR — `DOC-002` · No resource-level descriptions

**Location:** every resource (`/customerOrders`, `/customerOrders/{orderId}`, `/payment-process`, `/users`, `/users/{userId}/password`)
**Why it matters:** Resource descriptions show up in the Exchange UI as the first hint of intent for each endpoint. Their absence forces consumers to read the operations one by one to understand the resource's purpose.

**Remediation:**

```yaml
/customer-orders:
  description: |
    Customer orders held in the orders system of record. One order represents
    a confirmed purchase by a single customer; line items are accessible via
    the nested /items collection.
  get:
    # ...
```

---

### ⚪ INFO — `APIC-003`, `VER-003`, `SEC-003`, `DOC-003`

These are upgrade hints rather than violations. Briefly:

- **`APIC-003`** — Add the layer prefix to the title (covered jointly with `NAMING-004`).
- **`VER-003`** — `v1.2.3` belongs in release notes, not in the public version string. Use `v1`; track patches via implementation versions in API Manager or via Exchange asset versions.
- **`SEC-003`** — OAuth 2.0 (already proposed in `SEC-001`) is preferred over basic auth in production.
- **`DOC-003`** — Add a `documentation:` block with at least a "Getting started" and "Pagination & error handling" article.

```yaml
documentation:
  - title: Getting started
    content: |
      How to obtain credentials, register an application, and call the first
      endpoint. Includes a curl example end-to-end.
  - title: Pagination & error handling
    content: |
      All list endpoints use the `paginated` trait. Errors follow the
      ErrorResponse type documented under "Data Types".
```

---

## 4. Strengths

The spec is not without merit. Acknowledged positives:

- **Parseable and structurally valid RAML 1.0** — the file would load in Anypoint API Designer without syntax errors. That alone is worth noting.
- **Plural resource names** for `/customerOrders` and `/users` (`NAMING-002` passes). Most pluralization mistakes happen at the same time as the kebab-case mistake; here, only the case is wrong.
- **Consistent `mediaType`** declared at the root (`application/json`) rather than repeated per operation.
- **`{orderId}` URI parameter** correctly used as a path parameter rather than a query parameter — a common beginner mistake that this spec avoids.
- **`/users/{userId}/password`** is at least correctly nested under `/users/{userId}` rather than flattened to `/user-passwords`. The structure is right; only the security and verb (PUT vs. POST for a password change is debatable but defensible) need attention.

These strengths suggest the author understands RAML mechanics; the missing pieces are mostly governance and security discipline rather than syntax.

---

## 5. Next Steps

Recommended remediation order, sized for a single developer:

1. **Day 0.5 — Unblock production readiness (BLOCKERs).**
   1. Add `securitySchemes` (OAuth 2.0) and root `securedBy:` → fixes `SEC-001`, `REUSE-003`, `SEC-003`.
   2. Define a `standardErrors` trait and apply it everywhere → fixes `SPEC-003`.

2. **Day 0.5 — Fix governance & layer identity (MAJORs).**
   3. Rename `title:` to `s-orders-api` (or `p-order-fulfillment-api` after layer decision) → fixes `NAMING-004`, `APIC-003`.
   4. Decide on layer; if System, **remove** `/payment-process` → fixes `APIC-002`.
   5. Rename `/customerOrders` → `/customer-orders` and `sort_by` → `sortBy` → fixes `NAMING-001`, `NAMING-003`.
   6. Extract a `paginated` trait → fixes `REUSE-001`.
   7. Add `{version}` placeholder to `baseUri`; downgrade `v1.2.3` to `v1` → fixes `VER-002`, `VER-003`.
   8. Expand the root `description:` and add resource descriptions → fixes `DOC-001`, `DOC-002`.
   9. Add explicit `securedBy:` with scopes on the two sensitive endpoints → fixes `SEC-002`.

3. **Day 0.25 — Polish (MINORs & INFOs).**
   10. Add request and response `example`s on every body → fixes `SPEC-001`, `SPEC-002`.
   11. Add a `documentation:` block with onboarding articles → fixes `DOC-003`.

4. **Re-audit** with this skill to confirm score ≥ 85/100 before publishing to Anypoint Exchange.

---

## 6. Appendix — Score Calculation

Starting at 100, applying the standard scoring rule (-15 per BLOCKER, -5 per MAJOR, -2 per MINOR, 0 per INFO):

| Severity | Count | Weight | Subtotal |
|---|---|---|---|
| BLOCKER | 2 | -15 | -30 |
| MAJOR | 9 | -5 | -45 |
| MINOR | 3 | -2 | -6 |
| INFO | 4 | 0 | 0 |
| **Total** | **18** | | **-81** |

**Final score: 100 − 81 = 19 / 100.**

Per the audit standard, any score below 80/100 with at least one BLOCKER yields an automatic NO-GO verdict.

---

*Report generated by the `mulesoft-raml-validator` skill (v1.2.0) — Karim DJAAFAR, Jasmine Conseil.*
