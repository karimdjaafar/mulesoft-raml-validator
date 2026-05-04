# RAML Best Practices — Quick Reference

> Cheat sheet for the 23 audit rules enforced by `mulesoft-raml-validator`.
> Each rule has a stable ID, a severity, and a one-line definition. Use this
> as a checklist during RAML authoring or a glossary while reading audit
> reports.

---

## API-Led Connectivity refresher

Three layers, three intents:

| Layer | Prefix | Purpose | Examples |
|---|---|---|---|
| **System** | `s-` | Direct, entity-shaped access to a system of record | `s-orders-api`, `s-customers-api`, `s-payments-api` |
| **Process** | `p-` | Composes multiple System APIs into business capabilities | `p-order-fulfillment-api`, `p-customer-onboarding-api` |
| **Experience** | `x-` | Tailored payloads for a specific channel | `x-mobile-orders-api`, `x-partner-portal-api` |

A well-named API tells you the layer in 2 seconds. A poorly-named one forces you to read the resource list.

---

## Naming (`NAMING-*`)

| ID | Severity | Rule |
|---|---|---|
| `NAMING-001` | MAJOR | Resources MUST use kebab-case (`/customer-orders`, never `/customerOrders`). |
| `NAMING-002` | MAJOR | Resource names MUST be plural nouns (`/customers`, never `/customer` or `/getCustomer`). |
| `NAMING-003` | MINOR | Query parameters MUST use camelCase (`?sortBy=date`, never `?sort_by=date`). |
| `NAMING-004` | MAJOR | API title MUST follow `s-{system}-{entity}-api`, `p-{capability}-api`, or `x-{channel}-{capability}-api`. |

**Tip:** If you find yourself wanting a verb in a resource name, you're probably writing the wrong layer. See `APIC-002`.

---

## API-Led Connectivity (`APIC-*`)

| ID | Severity | Rule |
|---|---|---|
| `APIC-001` | BLOCKER | Experience APIs MUST NOT reference DB-like resources (`/sql-query`, `/db-table`). |
| `APIC-002` | MAJOR | System APIs MUST NOT contain orchestration verbs (`/process-order`, `/calculate-total`). |
| `APIC-003` | INFO | API titles SHOULD start with `s-`, `p-`, or `x-` for instant identification. |

**Layer test:** Read your resource list aloud. If it sounds like nouns ("orders", "customers"), you're in System or Experience. If it sounds like verbs ("approve", "calculate"), you're in Process. Mixed = problem.

---

## Reuse (`REUSE-*`)

| ID | Severity | Rule |
|---|---|---|
| `REUSE-001` | MAJOR | Pagination on 2+ resources MUST be defined as a `trait` and applied via `is:`. |
| `REUSE-002` | MAJOR | Duplicated error response schemas MUST be extracted to a shared library or trait. |
| `REUSE-003` | MINOR | Common security schemes SHOULD be declared at the root via `securedBy:`. |

**Rule of thumb:** If you copy-paste the same YAML block twice, it's a trait waiting to happen.

---

## Spec quality (`SPEC-*`)

| ID | Severity | Rule |
|---|---|---|
| `SPEC-001` | MAJOR | Every request body MUST have at least one `example`. |
| `SPEC-002` | MAJOR | Every response body MUST have at least one `example` per status code. |
| `SPEC-003` | BLOCKER | Every endpoint MUST document at least `400`, `401`, `404`, `500`. |
| `SPEC-004` | MINOR | Inline JSON schemas longer than 20 lines SHOULD be moved to `dataTypes/` files. |

**Why examples matter:** The Anypoint API Designer mocking service uses them to return realistic payloads. Without examples, your consumers cannot test integrations before your implementation is live.

---

## Security (`SEC-*`)

| ID | Severity | Rule |
|---|---|---|
| `SEC-001` | BLOCKER | No `securitySchemes` declared and no `securedBy:` at root → API is fully open. |
| `SEC-002` | MAJOR | Sensitive endpoints (POST/PUT/DELETE on `payment`, `auth`, `user`, `password`) MUST have explicit `securedBy:`. |
| `SEC-003` | INFO | OAuth 2.0 SHOULD be preferred over basic auth for production APIs. |

**Anti-pattern:** Relying on Anypoint API Manager policies to enforce security that the RAML doesn't declare. The contract is the source of truth for consumers — the policy layer is enforcement, not specification.

---

## Versioning (`VER-*`)

| ID | Severity | Rule |
|---|---|---|
| `VER-001` | BLOCKER | No `version:` field at root. |
| `VER-002` | MAJOR | The `version:` MUST appear in the `baseUri` (`https://api.example.com/{version}/...`). |
| `VER-003` | INFO | Use semantic major versions (`v1`, `v2`) — avoid `v1.0.3` in the public URI. |

**Why patch versions don't belong in URIs:** A patch by definition is non-breaking. If consumers don't need to migrate, the URI shouldn't change. Track patches via API Manager or Exchange asset versions.

---

## Documentation (`DOC-*`)

| ID | Severity | Rule |
|---|---|---|
| `DOC-001` | MAJOR | Root `description:` MUST be at least 50 characters. |
| `DOC-002` | MINOR | Resources without a `description:` field. |
| `DOC-003` | INFO | No `documentation:` section with usage examples or onboarding guide. |

**The 30-second test:** A new developer lands on your Exchange portal. Can they understand what your API does, who should use it, and how to make their first call — without reading the operations one by one?

---

## Severity scoring

Audit findings are weighted to compute the production-readiness score:

| Severity | Weight | Meaning |
|---|---|---|
| BLOCKER | -15 | Must be fixed before deployment. Auto-NO-GO regardless of total score. |
| MAJOR | -5 | Should be fixed before deployment. Affects governance, security, or maintainability. |
| MINOR | -2 | Should be fixed soon. Affects readability or consistency. |
| INFO | 0 | Recommendation. No score impact, but worth considering. |

Score starts at 100, floor at 0. A score ≥ 85 with no BLOCKERs is the bar for production readiness.

---

## Verdict thresholds

| Score | BLOCKERs | Verdict |
|---|---|---|
| ≥ 85 | 0 | ✅ GO |
| 70–84 | 0 | ⚠️ GO-WITH-RESERVATIONS |
| < 70 | 0 | 🛑 NO-GO |
| any | ≥ 1 | 🛑 NO-GO (forced) |

---

## See also

- [`SKILL.md`](../SKILL.md) — full skill manifest with audit posture and workflow.
- [`CHANGELOG.md`](../CHANGELOG.md) — version history.
- [Anypoint API Governance](https://docs.mulesoft.com/api-governance/) — MuleSoft's native ruleset enforcement (Enterprise Edition integration).
- [API Design Patterns](https://www.manning.com/books/api-design-patterns) by JJ Geewax — the canonical reference behind several `SPEC-*` and `REUSE-*` rules.
