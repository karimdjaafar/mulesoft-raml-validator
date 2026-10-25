# RAML best-practices cheat sheet

> Internal reference for the `mulesoft-raml-validator` skill.
> Consulted at workflow step §5.2 before producing an audit.
> **Source of truth for rule IDs is `SKILL.md` §2.** This file is a
> condensed lookup, not a redefinition.

---

## 1. Rule reference (the 23 rules at a glance — 21 automated by `audit_raml.py`; `REUSE-002` and `SPEC-004` reviewed by Claude)

Severity weight in the score formula (§5.6): BLOCKER −15, MAJOR −5, MINOR −2, INFO 0.
GO requires score ≥ 80 **and** zero blockers (§6).

### Naming (`NAMING-*`)

| ID | Sev | Check | Quick fix |
|---|---|---|---|
| `NAMING-001` | MAJOR | Resources are kebab-case | `/customerOrders` → `/customer-orders` |
| `NAMING-002` | MAJOR | Resource collections are plural nouns | `/customer` → `/customers` (skip singletons under `/{id}/...`) |
| `NAMING-003` | MINOR | Query parameters are camelCase | `?sort_by=` → `?sortBy=` |
| `NAMING-004` | MAJOR | Title follows `s-/p-/x-` convention | `customerOrderAPI` → `s-customer-orders-api` |

### API-Led Connectivity (`APIC-*`)

| ID | Sev | Check | Quick fix |
|---|---|---|---|
| `APIC-001` | BLOCKER | Experience API does not reference DB-like resources | Remove `/sql-*`, `/db-*`, `/query`; route through a System API |
| `APIC-002` | MAJOR | System API does not contain orchestration verbs | Move `/process-*`, `/calculate-*` to a Process API; expose nouns instead |
| `APIC-003` | INFO | Title carries the layer prefix | Same fix as `NAMING-004` |

### Reuse (`REUSE-*`)

| ID | Sev | Check | Quick fix |
|---|---|---|---|
| `REUSE-001` | MAJOR | Pagination is a `trait`, not duplicated | Extract `pageable` trait, apply via `is: [ pageable ]` |
| `REUSE-002` | MAJOR | Error schemas are extracted, not duplicated | Move to `dataTypes/ErrorResponse.raml` and reference |
| `REUSE-003` | MINOR | Common security at root via `securedBy:` | `securedBy: [ oauth_2_0 ]` at root |

### Spec (`SPEC-*`)

| ID | Sev | Check | Quick fix |
|---|---|---|---|
| `SPEC-001` | MAJOR | Every request body has an `example` | Add inline `example:` or `!include examples/foo.json` |
| `SPEC-002` | MAJOR | Every response body has an `example` per status | Same — one example per `(status, mediaType)` |
| `SPEC-003` | BLOCKER | Every method declares 400, 401, 404, 500 | Apply a `standardErrors` trait via `is:` on every method |
| `SPEC-004` | MINOR | Inline schemas > 20 lines move to `dataTypes/` | Extract to `dataTypes/Foo.raml`; reference by name |

### Security (`SEC-*`)

| ID | Sev | Check | Quick fix |
|---|---|---|---|
| `SEC-001` | BLOCKER | `securitySchemes` declared **and** root `securedBy:` set | Declare OAuth 2.0; `securedBy: [ oauth_2_0 ]` at root |
| `SEC-002` | MAJOR | Sensitive endpoints have explicit `securedBy:` | Add per-method scope: `securedBy: [ oauth_2_0: { scopes: [ users:credentials:write ] } ]` |
| `SEC-003` | INFO | OAuth 2.0 is preferred over Basic | Replace Basic with OAuth 2.0 |

Tokens that mark an endpoint as sensitive: `payment`, `auth`, `user`, `password`, `credential`, `token`, `secret`. Match is on the path string, case-insensitive.

### Versioning (`VER-*`)

| ID | Sev | Check | Quick fix |
|---|---|---|---|
| `VER-001` | BLOCKER | `version:` field at root | `version: v1` |
| `VER-002` | MAJOR | `{version}` interpolated in `baseUri` | `baseUri: https://api.x.com/foo/{version}` |
| `VER-003` | INFO | Use `vN`, not `vN.M.P`, in URI | `version: v1.2.3` → `version: v1` (patch belongs in changelog) |

### Documentation (`DOC-*`)

| ID | Sev | Check | Quick fix |
|---|---|---|---|
| `DOC-001` | MAJOR | Root `description:` ≥ 50 chars | Rewrite as a 2–3 sentence purpose statement |
| `DOC-002` | MINOR | Every resource has a `description:` | One-liner per resource |
| `DOC-003` | INFO | Root `documentation:` section exists | Add Overview, Getting started, Error model |

---

## 2. Layer decision tree

When `NAMING-004` and `APIC-002` push back on the spec, the auditor needs to recommend a layer. Walk this tree:

```
Does the spec wrap a single back-end system or DB?
├── Yes → it is a SYSTEM API
│         title: s-{system}-{entity}-api
│         resources: nouns only, no orchestration verbs
│         consumers: Process APIs (server-to-server)
│
└── No, it composes 2+ APIs / coordinates a workflow?
    ├── Yes → it is a PROCESS API
    │         title: p-{capability}-api
    │         resources: still nouns, but verbs in the *capability* are OK
    │                   (e.g. /payment-instructions, /order-fulfilments)
    │         consumers: Experience APIs
    │
    └── No, it serves a specific UI / channel?
        └── EXPERIENCE API
            title: x-{channel}-{capability}-api
            resources: shaped to channel needs (mobile, web, partner)
            consumers: client apps; never another API
```

**Heuristics for ambiguous cases:**

- `/payment-process` in a noun-style spec → either rename to `/payments` (System) or extract to a Process API. Never both.
- A spec that mixes `/customers`, `/orders`, `/users` *and* `/process-payment` *and* `/calculate-total` is almost certainly a Process API forced into a System API skin. Recommend extraction.
- Single-channel projection of multiple back-ends with channel-specific shapes (e.g. mobile-friendly compact payloads) → Experience API.

---

## 3. Verb → layer mapping

When the auditor sees a verb-shaped path segment, this is the routing table:

| Verb stem in segment | Layer it belongs to | Notes |
|---|---|---|
| `process-`, `-process` | Process | `/payment-process`, `/order-process` |
| `calculate-`, `compute-` | Process | Computation across multiple back-ends |
| `orchestrate-`, `coordinate-` | Process | Self-evident |
| `validate-and-`, `submit-and-` | Process | Compound operations |
| `execute-` | Process | Command-style endpoints |
| `search-` (with cross-system semantics) | Process | Federated search |
| `get-`, `fetch-`, `list-` | **None — remove the verb** | HTTP method already conveys this; rename to the noun |
| `create-`, `update-`, `delete-` | **None — remove the verb** | Same; HTTP method conveys it |

The orchestration-verb list above mirrors the `ORCHESTRATION_VERBS` constant in `scripts/audit_raml.py`. When extending one, extend the other.

---

## 4. Remediation palette (most-asked snippets)

### OAuth 2.0 + scoped securedBy (fixes `SEC-001` + `SEC-002`)

```yaml
securitySchemes:
  oauth_2_0:
    type: OAuth 2.0
    describedBy:
      headers:
        Authorization:
          type: string
    settings:
      authorizationUri: https://auth.example.com/oauth/authorize
      accessTokenUri:   https://auth.example.com/oauth/token
      authorizationGrants: [ authorization_code, client_credentials ]
      scopes:
        - "orders:read"
        - "orders:write"
        - "users:read"
        - "users:credentials:write"

securedBy: [ oauth_2_0 ]

# Per-method scope on a sensitive endpoint:
/users/{userId}/password:
  put:
    securedBy:
      - oauth_2_0: { scopes: [ "users:credentials:write" ] }
```

### Standard error trait (fixes `SPEC-003` + pre-empts `REUSE-002`)

```yaml
traits:
  standardErrors:
    responses:
      400: { body: { application/json: { type: ErrorResponse } } }
      401: { body: { application/json: { type: ErrorResponse } } }
      403: { body: { application/json: { type: ErrorResponse } } }
      404: { body: { application/json: { type: ErrorResponse } } }
      429: { body: { application/json: { type: ErrorResponse } } }
      500: { body: { application/json: { type: ErrorResponse } } }

# Apply on every method:
/customer-orders:
  get:
    is: [ standardErrors ]
```

The analyzer at `scripts/audit_raml.py` follows `is:` clauses when computing the union of declared response codes — applying the trait satisfies `SPEC-003` even if the method's inline `responses:` block does not list 400/401/404/500.

### Pagination trait (fixes `REUSE-001`)

```yaml
traits:
  pageable:
    queryParameters:
      page:
        type: integer
        default: 1
        minimum: 1
      pageSize:
        type: integer
        default: 25
        minimum: 1
        maximum: 100

/customer-orders:
  get:
    is: [ pageable, standardErrors ]
```

### URI versioning (fixes `VER-002` + `VER-003`)

```yaml
version: v1
baseUri: https://api.example.com/customer-orders/{version}
```

Patch and minor levels (`v1.2.3`) live in the changelog, response headers, or Anypoint Exchange listing — never in the URI.

### ErrorResponse data type (supports `REUSE-002` + `SPEC-002`)

```yaml
# dataTypes/ErrorResponse.raml
#%RAML 1.0 DataType
type: object
additionalProperties: false
properties:
  code:
    type: string
    enum: [ VALIDATION_ERROR, UNAUTHENTICATED, FORBIDDEN, NOT_FOUND,
            CONFLICT, RATE_LIMITED, INTERNAL_ERROR ]
  message:    { type: string, minLength: 1, maxLength: 500 }
  traceId:    { type: string, pattern: "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" }
  timestamp:  { type: datetime }
```

---

## 5. Severity calibration guidance

The rules above carry a default severity. The auditor MAY adjust within a single step if the maturity context warrants it (§1):

| Maturity | Severity adjustment |
|---|---|
| v0 PoC, internal only | INFO and MINOR may be silenced (still listed, but flagged as "non-blocking for PoC") |
| v1 candidate, pre-production | Default severities apply |
| Production deployment | MAJORs may be promoted to BLOCKERs if they affect security or contract stability |

**Never** lower a BLOCKER below MAJOR. **Never** silence `SEC-001`, `SEC-002`, `SPEC-003`, `VER-001`, or `APIC-001` regardless of maturity. These guard the contract and the trust boundary.

---

## 6. Score interpretation guide

| Score band | Verdict | Typical meaning |
|---|---|---|
| 100 | GO | Spec passes every rule. Rare; usually means trait/library reuse is mature. |
| 80–99 | GO | Production-ready with cosmetic refinements. Ship and iterate. |
| 60–79 | NO-GO | Foundations are sound; remediation is mechanical. ~½ to 1 person-day. |
| 30–59 | NO-GO | Multiple structural issues. Re-architect before ship; expect 1–3 person-days. |
| 0–29 | NO-GO | Either a PoC mislabelled as a production candidate, or a layer mismatch. Re-discuss layer intent before remediation. |

A BLOCKER caps the score at 85 by arithmetic (100 − 15). Two BLOCKERs cap it at 70. The §6 anti-pattern *"score above 80 with any BLOCKER present"* is therefore mathematically impossible — listed in the spec as a guard against tampering with the score formula, not as a bound the auditor needs to enforce.

---

## 7. When this cheat sheet is wrong

If a rule in this file disagrees with `SKILL.md` §2, **§2 wins**. This file is regenerated when §2 changes; if you find a drift, file it as a CHANGELOG entry under the next minor version and update both in the same commit.
