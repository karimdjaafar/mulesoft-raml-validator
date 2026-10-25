#!/usr/bin/env python3
"""
audit_raml.py — Structural and semantic analyzer for RAML 1.0 specs.

Applies the rules defined in §2 of SKILL.md and emits a machine-readable
findings.json consumable by render_report.py.

Usage:
    python audit_raml.py --raml path/to/spec.raml --out findings.json
    python audit_raml.py --raml path/to/spec.raml --out findings.json \
        --title-override "RAML Audit Report — myAPI"

Exit codes:
    0   audit completed successfully (regardless of GO/NO-GO verdict)
    2   could not parse the RAML file
    3   missing required argument or file not found
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
sys.path.insert(0, str(Path(__file__).resolve().parent))
from version import SKILL_VERSION, VERSION  # single source of the version

# ---------------------------------------------------------------------------
# YAML setup: register !include as a no-op so RAML parses as plain YAML.
# We do not follow includes here — structural analysis works on the root file.
# ---------------------------------------------------------------------------

class _Include:
    """Stand-in for a !include directive. We record the target but do not
    resolve it; rules that need to inspect included content are out of
    scope for this analyzer."""
    __slots__ = ("path",)

    def __init__(self, path: str) -> None:
        self.path = path

    def __repr__(self) -> str:  # pragma: no cover
        return f"<!include {self.path}>"


def _include_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> _Include:
    return _Include(loader.construct_scalar(node))


yaml.SafeLoader.add_constructor("!include", _include_constructor)


# ---------------------------------------------------------------------------
# Severity penalties (mirrors §5.6 — kept here so the analyzer can self-score
# even when the renderer is not invoked).
# ---------------------------------------------------------------------------

PENALTY = {"BLOCKER": 15, "MAJOR": 5, "MINOR": 2, "INFO": 0}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
WRITE_METHODS = {"post", "put", "patch", "delete"}

KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
CAMEL_RE = re.compile(r"^[a-z][a-zA-Z0-9]*$")
URI_PARAM_RE = re.compile(r"^\{[^}]+\}$")
LAYER_PREFIX_RE = re.compile(r"^(s|p|x)-[a-z0-9]")
# v1.4.2: the full title must be kebab-case after the prefix (no spaces,
# no capitals) — "s-leave management-api" used to pass NAMING-004.
TITLE_RE = re.compile(r"^(s|p|x)-[a-z0-9]+(?:-[a-z0-9]+)*$")
ORCHESTRATION_VERBS = (
    "process", "calculate", "compute", "orchestrate", "validate-and-",
    "submit-and-", "execute"
)
DATABASE_HINTS = ("sql-", "db-", "table-", "/query", "/sql")
SENSITIVE_TOKENS = ("payment", "auth", "user", "password", "credential",
                    "token", "secret")


def is_kebab_case(s: str) -> bool:
    return bool(KEBAB_RE.match(s))


def is_camel_case(s: str) -> bool:
    return bool(CAMEL_RE.match(s))


def looks_plural(name: str) -> bool:
    """Conservative pluralization check. A path segment is plural-ish if it
    ends in s/es/ies, OR is a known invariant noun. We accept ambiguous
    cases to avoid false positives on words like 'data' or 'media'."""
    invariants = {"data", "media", "audio", "video", "info"}
    if name.lower() in invariants:
        return True
    return name.endswith("s") or name.endswith("es") or name.endswith("ies")


def walk_resources(node: dict, prefix: str = ""):
    """Yield (path, resource_dict) for every resource in the tree."""
    for key, value in node.items():
        if not isinstance(key, str) or not key.startswith("/"):
            continue
        full_path = prefix + key
        if isinstance(value, dict):
            yield full_path, value
            yield from walk_resources(value, full_path)


def each_method(resource: dict):
    """Yield (method_name, method_dict) for each HTTP method on a resource."""
    for k, v in resource.items():
        if isinstance(k, str) and k.lower() in HTTP_METHODS and isinstance(v, dict):
            yield k.lower(), v


def has_example(body_node: Any) -> bool:
    """A RAML body has an example if any of these are set:
       - example: <scalar or include>
       - examples: <map>
       - the body is a TypeExpression that references a type with example
         (we cannot resolve here, so we treat type-only as 'no inline example')."""
    if not isinstance(body_node, dict):
        return False
    return "example" in body_node or "examples" in body_node


def infer_layer(title: str | None) -> str:
    """Returns 'system', 'process', 'experience', or 'unknown'."""
    if not title:
        return "unknown"
    m = LAYER_PREFIX_RE.match(title)
    if not m:
        return "unknown"
    return {"s": "system", "p": "process", "x": "experience"}[m.group(1)]


# ---------------------------------------------------------------------------
# Rule implementations — one function per category
# ---------------------------------------------------------------------------

def check_naming(spec: dict) -> list[dict]:
    findings: list[dict] = []

    # NAMING-001: kebab-case resources
    # NAMING-002: plural nouns (collection resources only)
    # NAMING-003: camelCase query parameters
    for path, resource in walk_resources(spec):
        segments = [s for s in path.split("/") if s]
        last_segment = segments[-1]

        # URI params like /{orderId} are not resource names — skip
        if URI_PARAM_RE.match(last_segment):
            pass
        else:
            if not is_kebab_case(last_segment):
                findings.append({
                    "rule": "NAMING-001",
                    "severity": "MAJOR",
                    "location": path,
                    "summary": f"Resource segment '{last_segment}' is not kebab-case.",
                    "impact": "Inconsistent URL ergonomics and against MuleSoft naming guidance.",
                    "remediation_code": f"# rename to kebab-case, e.g.\n# {path}  →  /{_to_kebab(last_segment)}"
                })
            # NAMING-002 only applies to *collection* resources. Skip:
            #   - segments containing an orchestration verb (APIC-002 catches them)
            #   - singleton sub-resources nested under a URI parameter
            #     (e.g. /users/{userId}/password is a legitimate singleton — only
            #     one password per user — and is a recognised REST pattern)
            parent_is_uri_param = (
                len(segments) >= 2 and URI_PARAM_RE.match(segments[-2]) is not None
            )
            verb_in_segment = any(v.rstrip("-") in last_segment for v in ORCHESTRATION_VERBS)

            if (
                is_kebab_case(last_segment)
                and not looks_plural(last_segment)
                and not parent_is_uri_param
                and not verb_in_segment
            ):
                findings.append({
                    "rule": "NAMING-002",
                    "severity": "MAJOR",
                    "location": path,
                    "summary": f"Resource segment '{last_segment}' looks singular; collection resources must be plural nouns.",
                    "impact": "Singular collection names confuse REST consumers expecting list semantics.",
                    "remediation_text": f"Rename '{last_segment}' to its plural form."
                })

        # NAMING-003 — query parameters on every method
        for method_name, method in each_method(resource):
            qparams = method.get("queryParameters") or {}
            if isinstance(qparams, dict):
                for qname in qparams.keys():
                    if isinstance(qname, str) and not is_camel_case(qname):
                        findings.append({
                            "rule": "NAMING-003",
                            "severity": "MINOR",
                            "location": f"{method_name.upper()} {path}?{qname}",
                            "summary": f"Query parameter '{qname}' is not camelCase.",
                            "remediation_code": f"queryParameters:\n  {_to_camel(qname)}:\n    type: string"
                        })

    # NAMING-004: title follows s-/p-/x- convention
    title = spec.get("title")
    if isinstance(title, str) and not TITLE_RE.match(title):
        findings.append({
            "rule": "NAMING-004",
            "severity": "MAJOR",
            "location": "title",
            "summary": f"Title '{title}' does not follow the s-/p-/x- layer convention.",
            "impact": "API-Led catalogs sort and filter by layer prefix; this API will not be discoverable as System / Process / Experience in Anypoint Exchange.",
            "remediation_code": "title: s-customer-orders-api    # System layer\n# or\ntitle: p-order-management-api  # Process layer\n# or\ntitle: x-web-orders-api        # Experience layer"
        })

    return findings


def check_apic(spec: dict) -> list[dict]:
    findings: list[dict] = []
    title = spec.get("title")
    layer = infer_layer(title if isinstance(title, str) else None)

    for path, _ in walk_resources(spec):
        last_segment = path.rstrip("/").split("/")[-1]
        if URI_PARAM_RE.match(last_segment):
            continue

        # APIC-001: Experience API must not reference DB-like resources
        if layer == "experience" and any(h in path.lower() for h in DATABASE_HINTS):
            findings.append({
                "rule": "APIC-001",
                "severity": "BLOCKER",
                "location": path,
                "summary": f"Experience API references a database-like resource ('{path}').",
                "impact": "Experience APIs must consume Process or System APIs, not databases directly. This breaks the API-Led layering and prevents reuse.",
                "remediation_text": "Remove the database-style resource and route through the appropriate System API instead."
            })

        # APIC-002: System API must not contain orchestration verbs
        # We apply this even when layer is 'unknown', because the violation is
        # structural (verb in a noun-resource context). Severity stays MAJOR.
        # Verbs may appear anywhere in the segment: 'process-order', 'order-process',
        # 'calculate-total', etc. Strip trailing '-' from the marker before matching.
        verb_markers = [v.rstrip("-") for v in ORCHESTRATION_VERBS]
        if any(marker in last_segment for marker in verb_markers):
            findings.append({
                "rule": "APIC-002",
                "severity": "MAJOR",
                "location": path,
                "summary": f"Orchestration verb in resource path ('{last_segment}') — belongs to a Process API, not a System API.",
                "impact": "Mixing nouns with orchestration verbs in the same spec means the API layer is undeclared and violates Single Responsibility per layer.",
                "remediation_text": "Either expose the entity as a noun (System API) or extract this resource into a separate Process API."
            })

    # APIC-003: title should start with the layer prefix (INFO duplicate of NAMING-004)
    if isinstance(title, str) and not LAYER_PREFIX_RE.match(title):
        findings.append({
            "rule": "APIC-003",
            "severity": "INFO",
            "location": "title",
            "summary": "Title should start with the layer prefix (s-/p-/x-) for instant identification."
        })

    return findings


def check_reuse(spec: dict) -> list[dict]:
    findings: list[dict] = []

    # REUSE-001: pagination duplicated across resources
    # We detect inline page/pageSize/offset/limit on 2+ GETs without a trait reference.
    pagination_keys = {"page", "pagesize", "offset", "limit"}
    inline_paginated: list[str] = []

    for path, resource in walk_resources(spec):
        for method_name, method in each_method(resource):
            if method_name != "get":
                continue
            qparams = method.get("queryParameters") or {}
            if not isinstance(qparams, dict):
                continue
            qnames_lower = {str(k).lower() for k in qparams.keys()}
            if pagination_keys & qnames_lower:
                # If the method declares 'is: [ pageable ]' (or any trait), it's covered
                if "is" not in method:
                    inline_paginated.append(f"GET {path}")

    if len(inline_paginated) >= 2:
        findings.append({
            "rule": "REUSE-001",
            "severity": "MAJOR",
            "location": ", ".join(inline_paginated),
            "summary": f"Pagination duplicated on {len(inline_paginated)} resources without a trait.",
            "impact": "Future pagination changes (defaults, max page size, link headers) require editing every resource.",
            "remediation_code": "traits:\n  pageable:\n    queryParameters:\n      page:     { type: integer, default: 1, minimum: 1 }\n      pageSize: { type: integer, default: 25, minimum: 1, maximum: 100 }\n\n/customer-orders:\n  get:\n    is: [ pageable ]"
        })

    # REUSE-002: duplicated error response shapes — out of scope without
    # following includes; we emit it when SPEC-003 flagged absent errors AND
    # there are inline body schemas in 2+ responses (best-effort heuristic).
    # Not implemented in v1.3.0 to avoid false positives.

    # REUSE-003: common security schemes should be declared at root
    if "securitySchemes" in spec and "securedBy" not in spec:
        findings.append({
            "rule": "REUSE-003",
            "severity": "MINOR",
            "location": "root",
            "summary": "securitySchemes is declared but no root-level securedBy: — every endpoint must repeat the binding.",
            "remediation_code": "securedBy: [ oauth_2_0 ]"
        })

    return findings


def _trait_response_codes(spec: dict, trait_name: str) -> set[int]:
    """Return the set of response codes a named trait contributes. We can only
    resolve traits defined inline in the same RAML file (not via !include)."""
    traits = spec.get("traits") or {}
    if not isinstance(traits, dict):
        return set()
    trait = traits.get(trait_name)
    # External !include — analyzer cannot follow; assume the trait covers errors
    # rather than emit a false positive. This keeps SPEC-003 conservative.
    if isinstance(trait, _Include):
        return {400, 401, 403, 404, 429, 500}
    if not isinstance(trait, dict):
        return set()
    responses = trait.get("responses") or {}
    if not isinstance(responses, dict):
        return set()
    out: set[int] = set()
    for code in responses:
        try:
            out.add(int(code))
        except (TypeError, ValueError):
            continue
    return out


def _applied_trait_names(method: dict) -> list[str]:
    """Extract trait names from a method's 'is:' clause. Each entry can be a
    string (trait name) or a single-key dict (parameterised trait)."""
    is_clause = method.get("is")
    if not is_clause:
        return []
    if not isinstance(is_clause, list):
        return []
    names: list[str] = []
    for entry in is_clause:
        if isinstance(entry, str):
            names.append(entry)
        elif isinstance(entry, dict) and len(entry) == 1:
            names.append(next(iter(entry.keys())))
    return names


def check_spec(spec: dict) -> list[dict]:
    findings: list[dict] = []

    # SPEC-001: every request body must have at least one example
    # SPEC-002: every response body must have at least one example
    # SPEC-003: every endpoint must declare 400, 401, 404, 500
    request_no_example: list[str] = []
    response_no_example: list[str] = []
    missing_errors: list[str] = []

    REQUIRED_ERROR_CODES = {400, 401, 404, 500}

    for path, resource in walk_resources(spec):
        for method_name, method in each_method(resource):
            method_label = f"{method_name.upper()} {path}"

            # SPEC-001
            body = method.get("body")
            if isinstance(body, dict):
                for media_type, body_def in body.items():
                    if not has_example(body_def):
                        request_no_example.append(f"{method_label} ({media_type})")

            # SPEC-002 + SPEC-003 — union of method-declared and trait-contributed codes
            declared_codes: set[int] = set()
            responses = method.get("responses")
            if isinstance(responses, dict):
                for code, resp in responses.items():
                    try:
                        code_int = int(code)
                    except (TypeError, ValueError):
                        continue
                    declared_codes.add(code_int)
                    if not isinstance(resp, dict):
                        continue
                    rbody = resp.get("body")
                    if isinstance(rbody, dict):
                        for media_type, body_def in rbody.items():
                            if not has_example(body_def):
                                response_no_example.append(
                                    f"{method_label} → {code_int} ({media_type})"
                                )

            for trait_name in _applied_trait_names(method):
                declared_codes |= _trait_response_codes(spec, trait_name)

            missing = REQUIRED_ERROR_CODES - declared_codes
            if missing:
                missing_errors.append(f"{method_label} (missing {sorted(missing)})")

    if request_no_example:
        findings.append({
            "rule": "SPEC-001",
            "severity": "MAJOR",
            "location": "; ".join(request_no_example[:5]) + (
                f" (+{len(request_no_example)-5} more)" if len(request_no_example) > 5 else ""),
            "summary": f"{len(request_no_example)} request bodies have no inline example.",
            "impact": "Mocking Service, API Designer 'Try it', and consumer SDK generators all rely on `example`.",
            "remediation_code": "post:\n  body:\n    application/json:\n      type: CustomerOrderRequest\n      example:\n        customerId: \"CUST-00042\"\n        items: [ { sku: \"SKU-001\", quantity: 2 } ]"
        })

    if response_no_example:
        findings.append({
            "rule": "SPEC-002",
            "severity": "MAJOR",
            "location": "; ".join(response_no_example[:5]) + (
                f" (+{len(response_no_example)-5} more)" if len(response_no_example) > 5 else ""),
            "summary": f"{len(response_no_example)} response bodies have no inline example per status code.",
            "impact": "Consumers cannot stub or mock against the contract."
        })

    if missing_errors:
        findings.append({
            "rule": "SPEC-003",
            "severity": "BLOCKER",
            "location": "; ".join(missing_errors[:3]) + (
                f" (+{len(missing_errors)-3} more)" if len(missing_errors) > 3 else ""),
            "summary": f"{len(missing_errors)} methods do not declare the full required error set (400/401/404/500).",
            "impact": "Consumers have no contract for failure modes. Code generation, mocking, and MUnit are all impacted.",
            "remediation_code": "traits:\n  standardErrors:\n    responses:\n      400: { body: { application/json: { type: ErrorResponse } } }\n      401: { body: { application/json: { type: ErrorResponse } } }\n      404: { body: { application/json: { type: ErrorResponse } } }\n      500: { body: { application/json: { type: ErrorResponse } } }"
        })

    return findings


def check_security(spec: dict) -> list[dict]:
    findings: list[dict] = []

    has_schemes = bool(spec.get("securitySchemes"))
    root_secured = "securedBy" in spec

    # SEC-001: no schemes AND no root securedBy
    if not has_schemes and not root_secured:
        findings.append({
            "rule": "SEC-001",
            "severity": "BLOCKER",
            "location": "root",
            "summary": "No securitySchemes and no root securedBy: — API is fully open.",
            "impact": "Any client can call any endpoint. Hard fail for any non-public API.",
            "remediation_code": "securitySchemes:\n  oauth_2_0:\n    type: OAuth 2.0\n    settings:\n      authorizationUri: https://auth.example.com/oauth/authorize\n      accessTokenUri: https://auth.example.com/oauth/token\n      authorizationGrants: [ authorization_code, client_credentials ]\n\nsecuredBy: [ oauth_2_0 ]"
        })

    # SEC-002: sensitive endpoints must have explicit securedBy
    sec002_locations: list[str] = []
    for path, resource in walk_resources(spec):
        is_sensitive_path = any(token in path.lower() for token in SENSITIVE_TOKENS)
        for method_name, method in each_method(resource):
            if method_name not in WRITE_METHODS:
                continue
            if not is_sensitive_path:
                continue
            if "securedBy" not in method:
                sec002_locations.append(f"{method_name.upper()} {path}")
    if sec002_locations:
        findings.append({
            "rule": "SEC-002",
            "severity": "MAJOR",
            "location": "; ".join(sec002_locations),
            "summary": f"{len(sec002_locations)} sensitive endpoint(s) lack an explicit securedBy: with a narrow scope.",
            "impact": "Sensitive routes (payment, auth, password, credentials) should declare a method-specific scope, not inherit the root scope.",
            "remediation_code": "/users/{userId}/password:\n  put:\n    securedBy:\n      - oauth_2_0: { scopes: [ \"users:credentials:write\" ] }"
        })

    # SEC-003: prefer OAuth 2.0 over basic auth — informational, only if a
    # non-OAuth scheme is declared.
    schemes = spec.get("securitySchemes") or {}
    if isinstance(schemes, dict):
        for name, scheme in schemes.items():
            if isinstance(scheme, dict):
                stype = scheme.get("type", "")
                if isinstance(stype, str) and "Basic" in stype:
                    findings.append({
                        "rule": "SEC-003",
                        "severity": "INFO",
                        "location": f"securitySchemes.{name}",
                        "summary": "Basic auth declared — OAuth 2.0 is preferred for production APIs."
                    })

    # If neither schemes nor root securedBy is set, also emit SEC-003 as advisory
    if not has_schemes and not root_secured:
        findings.append({
            "rule": "SEC-003",
            "severity": "INFO",
            "location": "n/a",
            "summary": "Once authentication is added, prefer OAuth 2.0 over basic auth."
        })

    return findings


def check_versioning(spec: dict) -> list[dict]:
    findings: list[dict] = []
    version = spec.get("version")
    base_uri = spec.get("baseUri")

    # VER-001: no version field at root
    if version is None:
        findings.append({
            "rule": "VER-001",
            "severity": "BLOCKER",
            "location": "root",
            "summary": "No version: field declared at root.",
            "impact": "Without a version, consumers cannot pin to a contract and breaking changes cannot be rolled out in parallel.",
            "remediation_code": "version: v1"
        })

    # VER-002: version not interpolated in baseUri
    if isinstance(base_uri, str) and version is not None and "{version}" not in base_uri:
        findings.append({
            "rule": "VER-002",
            "severity": "MAJOR",
            "location": "baseUri",
            "summary": "{version} placeholder is not interpolated in baseUri.",
            "impact": "Consumers cannot pin to a major version via the URL; parallel rollout (v1 → v2) is impossible.",
            "remediation_code": "baseUri: https://api.example.com/customer-orders/{version}"
        })

    # VER-003: avoid v1.0.3 in URI — recommend v1
    if isinstance(version, str):
        # Heuristic: anything beyond a single "vN" segment triggers INFO
        if not re.match(r"^v\d+$", version):
            findings.append({
                "rule": "VER-003",
                "severity": "INFO",
                "location": f"version: {version}",
                "summary": "Use semantic versioning (v1, v2) in the URI; reserve patch/minor for the changelog.",
                "remediation_code": "version: v1   # patch level v1.2.3 belongs in changelogs/headers"
            })

    return findings


def check_documentation(spec: dict) -> list[dict]:
    findings: list[dict] = []

    # DOC-001: root description missing or shorter than 50 chars
    desc = spec.get("description")
    if not isinstance(desc, str) or len(desc.strip()) < 50:
        actual_len = len(desc.strip()) if isinstance(desc, str) else 0
        findings.append({
            "rule": "DOC-001",
            "severity": "MAJOR",
            "location": "description",
            "summary": f"Root description is {actual_len} characters (minimum 50).",
            "impact": "Anypoint Exchange listing will be uninformative; downstream developers cannot determine fit-for-purpose.",
            "remediation_code": "description: |\n  System API exposing customer orders and user account operations\n  for the retail platform. Backed by the OMS and IAM service.\n  Consumed by the Order Management Process API."
        })

    # DOC-002: resources without description
    undocumented: list[str] = []
    for path, resource in walk_resources(spec):
        if "description" not in resource:
            undocumented.append(path)
    if undocumented:
        findings.append({
            "rule": "DOC-002",
            "severity": "MINOR",
            "location": "; ".join(undocumented[:5]) + (
                f" (+{len(undocumented)-5} more)" if len(undocumented) > 5 else ""),
            "summary": f"{len(undocumented)} resources have no description: field.",
            "remediation_text": "Add a one-line description on every resource."
        })

    # DOC-003: no documentation: section
    if "documentation" not in spec:
        findings.append({
            "rule": "DOC-003",
            "severity": "INFO",
            "location": "root",
            "summary": "No documentation: section with onboarding guide.",
            "remediation_code": "documentation:\n  - title: Overview\n    content: |\n      This API exposes ...\n  - title: Getting started\n    content: !include docs/getting-started.md"
        })

    return findings


# ---------------------------------------------------------------------------
# Small naming helpers
# ---------------------------------------------------------------------------

def _to_kebab(s: str) -> str:
    # camelCase or snake_case → kebab-case
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s)
    s = s.replace("_", "-")
    return s.lower()


def _to_camel(s: str) -> str:
    parts = re.split(r"[_\-]", s)
    if not parts:
        return s
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

CHECKS = [
    check_naming,
    check_apic,
    check_reuse,
    check_spec,
    check_security,
    check_versioning,
    check_documentation,
]


def parse_raml(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    # Skip the #%RAML 1.0 header line — PyYAML cannot parse it.
    lines = text.splitlines()
    if lines and lines[0].startswith("#%RAML"):
        text = "\n".join(lines[1:])
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        print(f"ERROR: failed to parse RAML as YAML: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict):
        print("ERROR: RAML root is not a mapping", file=sys.stderr)
        sys.exit(2)
    return data


def compute_score(findings: list[dict]) -> tuple[int, str]:
    blockers = sum(1 for f in findings if f["severity"] == "BLOCKER")
    score = 100 - sum(PENALTY[f["severity"]] for f in findings)
    score = max(score, 0)
    verdict = "GO" if (score >= 80 and blockers == 0) else "NO-GO"
    return score, verdict


def api_profile(spec: dict) -> dict:
    """Describe the API under audit, as written in the spec (v1.4.2).

    Facts only — nothing is inferred except the API-Led layer, which is read
    from the title prefix ('unknown' when there is none).
    """
    def _s(v):
        return v.strip() if isinstance(v, str) else None
    resources, methods, operations = 0, {}, []
    for path, res in walk_resources(spec):
        resources += 1
        for m, mdef in each_method(res):
            methods[m.upper()] = methods.get(m.upper(), 0) + 1
            operations.append({"method": m.upper(), "path": path,
                               "description": _s(mdef.get("description")) or ""})
    schemes = spec.get("securitySchemes")
    types = spec.get("types")
    traits = spec.get("traits")
    return {
        "title": _s(spec.get("title")) or "(untitled)",
        "version": _s(str(spec["version"])) if spec.get("version") is not None else None,
        "base_uri": _s(spec.get("baseUri")),
        "media_type": _s(spec.get("mediaType")) if isinstance(spec.get("mediaType"), str) else None,
        "layer": infer_layer(spec.get("title") if isinstance(spec.get("title"), str) else None),
        "description": _s(spec.get("description")),
        "resources": resources,
        "operations": len(operations),
        "methods": dict(sorted(methods.items())),
        "operation_list": operations,
        "security_schemes": sorted(schemes.keys()) if isinstance(schemes, dict) else [],
        "types": sorted(types.keys()) if isinstance(types, dict) else [],
        "traits": sorted(traits.keys()) if isinstance(traits, dict) else [],
    }


def aggregate_by_rule(findings: list[dict]) -> list[dict]:
    """Merge findings that share a rule ID into one entry (v1.4.2).

    §4 promises one entry per rule with every affected location listed;
    without this, a rule hit in N places was penalised N times (e.g. the
    same snake_case query parameter on two resources).
    """
    merged: dict[str, dict] = {}
    order: list[str] = []
    for f in findings:
        rid = f["rule"]
        if rid not in merged:
            merged[rid] = dict(f)
            merged[rid]["_count"] = 1
            order.append(rid)
            continue
        m = merged[rid]
        m["_count"] += 1
        m["location"] = f"{m['location']}; {f['location']}"
    out = []
    for rid in order:
        m = merged.pop(rid)
        n = m.pop("_count")
        if n > 1:
            m["summary"] = f"{n} occurrences — {m['summary']}"
        out.append(m)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raml", required=True, help="Path to the RAML spec to audit")
    ap.add_argument("--out", required=True, help="Path to write findings JSON")
    ap.add_argument("--title-override", default=None,
                    help="Override the report title (default: derived from RAML title)")
    args = ap.parse_args()

    raml_path = Path(args.raml)
    if not raml_path.exists():
        print(f"ERROR: file not found: {raml_path}", file=sys.stderr)
        return 3

    spec = parse_raml(raml_path)

    # Run all checks
    findings: list[dict] = []
    for check in CHECKS:
        findings.extend(check(spec))

    findings = aggregate_by_rule(findings)

    # Sort: severity first, then rule ID
    sev_order = {"BLOCKER": 0, "MAJOR": 1, "MINOR": 2, "INFO": 3}
    findings.sort(key=lambda f: (sev_order[f["severity"]], f["rule"]))

    score, verdict = compute_score(findings)

    raml_title = spec.get("title") if isinstance(spec.get("title"), str) else "(untitled)"
    report_title = args.title_override or f"RAML Audit Report — {raml_title}"

    payload = {
        "title": report_title,
        "subtitle": "MuleSoft RAML 1.0 production-readiness audit",
        "spec_path": str(raml_path),
        "date": datetime.date.today().isoformat(),
        "skill_version": SKILL_VERSION,
        "score": score,
        "verdict": verdict,
        "findings": findings,
        "api": api_profile(spec),
    }

    Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    blockers = sum(1 for f in findings if f["severity"] == "BLOCKER")
    majors   = sum(1 for f in findings if f["severity"] == "MAJOR")
    minors   = sum(1 for f in findings if f["severity"] == "MINOR")
    infos    = sum(1 for f in findings if f["severity"] == "INFO")
    print(f"Wrote {args.out}: {len(findings)} findings "
          f"({blockers} blockers, {majors} majors, {minors} minors, {infos} info) "
          f"— score {score}/100, verdict {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
