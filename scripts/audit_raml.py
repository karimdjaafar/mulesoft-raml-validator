#!/usr/bin/env python3
"""
audit_raml.py — Deterministic structural audit of a MuleSoft RAML 1.0 spec.

Parses a RAML file with PyYAML, runs structural checks across the 7 audit
categories defined in SKILL.md §2, and emits a JSON of findings consumable
by render_report.py.

Usage:
    python scripts/audit_raml.py --raml path/to/spec.raml --out findings.json

Exit codes:
    0  — audit completed (regardless of findings)
    1  — file not found, parse error, or invalid RAML
    2  — unexpected internal error

Copyright (c) 2026 Karim DJAAFAR — Jasmine Conseil
Licensed under the Apache License, Version 2.0.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "ERROR: PyYAML is required. Install with: pip install pyyaml\n"
    )
    sys.exit(1)


# ── Severity weights for scoring (per SKILL.md §5 step 6) ───────────────────
SEVERITY_WEIGHTS = {"BLOCKER": -15, "MAJOR": -5, "MINOR": -2, "INFO": 0}

# ── Sensitive resource keywords (per SEC-002) ───────────────────────────────
SENSITIVE_KEYWORDS = ("payment", "auth", "password", "credential", "token")

# ── Mutating HTTP methods that trigger sensitive-endpoint checks ────────────
MUTATING_METHODS = ("post", "put", "patch", "delete")


@dataclass
class Finding:
    """Structured audit finding."""
    rule_id: str
    severity: str
    category: str
    location: str
    summary: str
    detail: str
    remediation: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditResult:
    """Container for an audit run."""
    raml_path: str
    findings: list[Finding] = field(default_factory=list)
    parse_ok: bool = True
    parse_error: str | None = None

    def add(self, **kwargs: Any) -> None:
        self.findings.append(Finding(**kwargs))

    def score(self) -> int:
        total = 100
        for f in self.findings:
            total += SEVERITY_WEIGHTS.get(f.severity, 0)
        return max(0, total)

    def has_blocker(self) -> bool:
        return any(f.severity == "BLOCKER" for f in self.findings)

    def verdict(self) -> str:
        if self.has_blocker():
            return "NO-GO"
        if self.score() >= 85:
            return "GO"
        if self.score() >= 70:
            return "GO-WITH-RESERVATIONS"
        return "NO-GO"

    def summary(self) -> dict[str, Any]:
        counts = {"BLOCKER": 0, "MAJOR": 0, "MINOR": 0, "INFO": 0}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return {
            "raml_path": self.raml_path,
            "score": self.score(),
            "verdict": self.verdict(),
            "counts": counts,
            "total_findings": len(self.findings),
            "findings": [f.as_dict() for f in self.findings],
        }


# ─── RAML loading ───────────────────────────────────────────────────────────


def load_raml(path: Path) -> dict[str, Any]:
    """Load a RAML 1.0 file, stripping the #%RAML 1.0 header line."""
    text = path.read_text(encoding="utf-8")
    if not text.lstrip().startswith("#%RAML 1.0"):
        raise ValueError(
            f"File does not start with '#%RAML 1.0' header: {path}"
        )
    # Strip the header line so PyYAML can parse it as plain YAML.
    lines = text.splitlines()
    yaml_text = "\n".join(lines[1:])
    return yaml.safe_load(yaml_text) or {}


# ─── Helpers ────────────────────────────────────────────────────────────────


def walk_resources(
    node: dict[str, Any],
    prefix: str = "",
) -> Iterable[tuple[str, dict[str, Any]]]:
    """Yield (path, resource_dict) for every resource in the RAML tree."""
    if not isinstance(node, dict):
        return
    for key, value in node.items():
        if isinstance(key, str) and key.startswith("/") and isinstance(value, dict):
            full_path = prefix + key
            yield full_path, value
            yield from walk_resources(value, full_path)


def operations(resource: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    """Yield (method, operation_dict) pairs for an HTTP-method resource."""
    methods = ("get", "post", "put", "patch", "delete", "head", "options")
    for m in methods:
        op = resource.get(m)
        if isinstance(op, dict):
            yield m, op


def is_kebab_case(segment: str) -> bool:
    """Check whether a path segment is valid kebab-case."""
    # Strip leading slash and URI parameters like {orderId}
    seg = segment.lstrip("/")
    if seg.startswith("{") and seg.endswith("}"):
        return True  # URI parameters are not subject to kebab-case
    return re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", seg) is not None


def looks_singular(noun: str) -> bool:
    """Heuristic: detect singular resource names (very rough)."""
    n = noun.lstrip("/").rstrip("s")
    # If stripping 's' gives us back the original (no 's'), likely singular.
    # But common English plurals end in 'ies' or 'es', so we're conservative.
    if noun.endswith("s") or noun.endswith("ies") or noun.endswith("es"):
        return False
    if len(noun.lstrip("/")) <= 2:
        return False  # Too short to judge
    return True


def has_orchestration_verb(segment: str) -> bool:
    """Detect verb-style resource names that belong to a Process API."""
    verbs = (
        "process", "calculate", "validate", "compute", "execute",
        "approve", "reject", "submit", "confirm", "trigger",
    )
    seg = segment.lstrip("/").lower()
    return any(v in seg for v in verbs)


def is_sensitive_path(path: str) -> bool:
    """Return True if the path contains a sensitive keyword."""
    p = path.lower()
    return any(kw in p for kw in SENSITIVE_KEYWORDS)


# ─── Audit checks ───────────────────────────────────────────────────────────


def check_naming(spec: dict[str, Any], result: AuditResult) -> None:
    """NAMING-001 to NAMING-004."""
    title = spec.get("title", "")

    # NAMING-004: title prefix
    if not re.match(r"^[spx]-[a-z0-9]+(-[a-z0-9]+)*$", title or ""):
        result.add(
            rule_id="NAMING-004",
            severity="MAJOR",
            category="Naming",
            location=f"title: {title!r}",
            summary="API title does not follow API-Led prefix convention.",
            detail=(
                "Titles must follow s-{system}-{entity}-api, p-{capability}-api, "
                "or x-{channel}-{capability}-api per API-Led layer."
            ),
            remediation="title: s-orders-api  # or p-... / x-... per layer",
        )

    # Walk resources for NAMING-001, NAMING-002, NAMING-003
    for path, resource in walk_resources(spec):
        last_segment = path.rsplit("/", 1)[-1]

        # NAMING-001: kebab-case
        if not is_kebab_case("/" + last_segment):
            if not (last_segment.startswith("{") and last_segment.endswith("}")):
                result.add(
                    rule_id="NAMING-001",
                    severity="MAJOR",
                    category="Naming",
                    location=f"resource {path}",
                    summary="Resource is not in kebab-case.",
                    detail=(
                        "URI segments must use kebab-case for consistency "
                        "and case-insensitive client compatibility."
                    ),
                    remediation=f"# Rename {path} to use kebab-case (e.g., /customer-orders).",
                )

        # NAMING-002: plural nouns (skip URI parameters)
        if not last_segment.startswith("{"):
            if looks_singular("/" + last_segment):
                result.add(
                    rule_id="NAMING-002",
                    severity="MAJOR",
                    category="Naming",
                    location=f"resource {path}",
                    summary="Resource name appears to be singular.",
                    detail="Collection resources should use plural nouns.",
                    remediation=f"# Pluralize the last segment of {path}.",
                )

        # NAMING-003: query parameter camelCase
        for _, op in operations(resource):
            qparams = op.get("queryParameters", {}) or {}
            for qname in qparams:
                if "_" in qname or qname != qname.lower() and not re.match(
                    r"^[a-z][a-zA-Z0-9]*$", qname
                ):
                    if "_" in qname:
                        result.add(
                            rule_id="NAMING-003",
                            severity="MINOR",
                            category="Naming",
                            location=f"{path} → queryParameter {qname!r}",
                            summary="Query parameter uses snake_case.",
                            detail="Query parameters must use camelCase.",
                            remediation=(
                                f"# Rename {qname!r} to camelCase "
                                f"(e.g., {to_camel(qname)!r})."
                            ),
                        )


def to_camel(snake: str) -> str:
    parts = snake.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def check_apic(spec: dict[str, Any], result: AuditResult) -> None:
    """APIC-001 to APIC-003."""
    title = spec.get("title", "") or ""

    # APIC-003: layer prefix
    if not re.match(r"^[spx]-", title):
        result.add(
            rule_id="APIC-003",
            severity="INFO",
            category="API-Led Connectivity",
            location=f"title: {title!r}",
            summary="Title should start with layer prefix (s-, p-, or x-).",
            detail="Layer prefixes enable instant API-Led identification.",
            remediation="# Add 's-', 'p-', or 'x-' prefix to title per layer.",
        )

    has_orchestration = False
    has_entity = False
    for path, _ in walk_resources(spec):
        last = path.rsplit("/", 1)[-1]
        if has_orchestration_verb(last):
            has_orchestration = True
            result.add(
                rule_id="APIC-002",
                severity="MAJOR",
                category="API-Led Connectivity",
                location=f"resource {path}",
                summary="Orchestration verb in resource name.",
                detail=(
                    "Verbs like 'process', 'calculate', 'execute' belong to "
                    "Process APIs, not System APIs."
                ),
                remediation=f"# Move {path} to a Process API or rename to a noun.",
            )
        elif not last.startswith("{") and last:
            has_entity = True

    # APIC-001: Experience APIs and DB-like resources
    for path, _ in walk_resources(spec):
        if any(kw in path.lower() for kw in ("/sql-query", "/db-table", "/raw-sql")):
            if title.startswith("x-"):
                result.add(
                    rule_id="APIC-001",
                    severity="BLOCKER",
                    category="API-Led Connectivity",
                    location=f"resource {path}",
                    summary="Experience API references database-like resource.",
                    detail=(
                        "Experience APIs must consume Process or System APIs, "
                        "never database primitives directly."
                    ),
                    remediation=f"# Remove {path}; route through a System API.",
                )


def check_reuse(spec: dict[str, Any], result: AuditResult) -> None:
    """REUSE-001 to REUSE-003."""
    traits = spec.get("traits") or {}
    paginated_resources: list[str] = []

    for path, resource in walk_resources(spec):
        for _, op in operations(resource):
            qp = op.get("queryParameters") or {}
            param_names = set(qp.keys()) if isinstance(qp, dict) else set()
            if {"page", "pageSize"}.issubset(param_names) or {
                "page", "limit"
            }.issubset(param_names):
                paginated_resources.append(path)

    # REUSE-001: pagination duplication
    if len(paginated_resources) >= 2 and not traits:
        result.add(
            rule_id="REUSE-001",
            severity="MAJOR",
            category="Reuse",
            location=", ".join(paginated_resources),
            summary="Pagination duplicated on 2+ resources without a trait.",
            detail=(
                "Pagination semantics will drift across copies as the API evolves. "
                "Extract to a trait."
            ),
            remediation=(
                "traits:\n"
                "  paginated:\n"
                "    queryParameters:\n"
                "      page: { type: integer, default: 1 }\n"
                "      pageSize: { type: integer, default: 50 }"
            ),
        )

    # REUSE-003: root securedBy:
    if spec.get("securitySchemes") and not spec.get("securedBy"):
        result.add(
            rule_id="REUSE-003",
            severity="MINOR",
            category="Reuse",
            location="root",
            summary="securitySchemes declared but not applied at root.",
            detail=(
                "Apply default scheme via root-level 'securedBy:' to minimize "
                "duplication."
            ),
            remediation="securedBy: [ oauth2 ]",
        )


def check_spec_quality(spec: dict[str, Any], result: AuditResult) -> None:
    """SPEC-001 to SPEC-004."""
    required_errors = {"400", "401", "404", "500"}

    for path, resource in walk_resources(spec):
        for method, op in operations(resource):
            location = f"{method.upper()} {path}"

            # SPEC-003: error responses
            responses = op.get("responses") or {}
            response_codes = {str(k) for k in responses}
            missing_errors = required_errors - response_codes
            if missing_errors:
                result.add(
                    rule_id="SPEC-003",
                    severity="BLOCKER",
                    category="Spec quality",
                    location=location,
                    summary=f"Missing error responses: {', '.join(sorted(missing_errors))}.",
                    detail=(
                        "Every endpoint must document at least 400, 401, 404, 500 "
                        "for consumer error handling."
                    ),
                    remediation=(
                        "responses:\n"
                        "  400: { body: { application/json: { type: ErrorResponse }}}\n"
                        "  401: { body: { application/json: { type: ErrorResponse }}}\n"
                        "  404: { body: { application/json: { type: ErrorResponse }}}\n"
                        "  500: { body: { application/json: { type: ErrorResponse }}}"
                    ),
                )

            # SPEC-001: request body example
            req_body = op.get("body")
            if isinstance(req_body, dict):
                for media_type, body_def in req_body.items():
                    if isinstance(body_def, dict) and "example" not in body_def:
                        result.add(
                            rule_id="SPEC-001",
                            severity="MAJOR",
                            category="Spec quality",
                            location=f"{location} → request body ({media_type})",
                            summary="Request body has no example.",
                            detail=(
                                "Examples enable mocking, consumer onboarding, "
                                "and integration testing."
                            ),
                            remediation=(
                                "body:\n"
                                "  application/json:\n"
                                "    type: NewOrder\n"
                                "    example: { customerId: 'CUST-1', total: 99.99 }"
                            ),
                        )

            # SPEC-002: response body examples
            for code, response_def in responses.items():
                if not isinstance(response_def, dict):
                    continue
                resp_body = response_def.get("body") or {}
                if not isinstance(resp_body, dict):
                    continue
                for media_type, body_def in resp_body.items():
                    if isinstance(body_def, dict) and "example" not in body_def:
                        result.add(
                            rule_id="SPEC-002",
                            severity="MAJOR",
                            category="Spec quality",
                            location=f"{location} → response {code} ({media_type})",
                            summary="Response body has no example.",
                            detail="Same reasoning as SPEC-001 applied to responses.",
                            remediation=(
                                "responses:\n"
                                "  200:\n"
                                "    body:\n"
                                "      application/json:\n"
                                "        example: { id: 'ORD-1', status: 'CONFIRMED' }"
                            ),
                        )


def check_security(spec: dict[str, Any], result: AuditResult) -> None:
    """SEC-001 to SEC-003."""
    schemes = spec.get("securitySchemes")
    root_secured = spec.get("securedBy")

    # SEC-001: nothing declared
    if not schemes and not root_secured:
        result.add(
            rule_id="SEC-001",
            severity="BLOCKER",
            category="Security",
            location="root",
            summary="No security declared anywhere.",
            detail="The API is fully open as written. This blocks production deployment.",
            remediation=(
                "securitySchemes:\n"
                "  oauth2:\n"
                "    type: OAuth 2.0\n"
                "    settings: { ... }\n"
                "securedBy: [ oauth2 ]"
            ),
        )

    # SEC-003: prefer OAuth 2.0
    if isinstance(schemes, dict):
        types = set()
        for s in schemes.values():
            if isinstance(s, dict):
                t = s.get("type", "")
                types.add(t)
        if "Basic Authentication" in types and "OAuth 2.0" not in types:
            result.add(
                rule_id="SEC-003",
                severity="INFO",
                category="Security",
                location="securitySchemes",
                summary="Basic auth declared without OAuth 2.0 alternative.",
                detail="OAuth 2.0 is preferred over basic auth for production.",
                remediation="# Add an OAuth 2.0 scheme alongside or instead of basic auth.",
            )

    # SEC-002: sensitive endpoints without explicit securedBy:
    for path, resource in walk_resources(spec):
        if not is_sensitive_path(path):
            continue
        for method, op in operations(resource):
            if method not in MUTATING_METHODS:
                continue
            if "securedBy" not in op:
                result.add(
                    rule_id="SEC-002",
                    severity="MAJOR",
                    category="Security",
                    location=f"{method.upper()} {path}",
                    summary="Sensitive endpoint without explicit securedBy:.",
                    detail=(
                        f"Path contains sensitive keyword. {method.upper()} mutations "
                        "must declare security at the operation level."
                    ),
                    remediation=(
                        f"{method}:\n"
                        "  securedBy: [ oauth2: { scopes: [ '...' ] } ]"
                    ),
                )


def check_versioning(spec: dict[str, Any], result: AuditResult) -> None:
    """VER-001 to VER-003."""
    version = spec.get("version")
    base_uri = spec.get("baseUri", "") or ""

    # VER-001
    if not version:
        result.add(
            rule_id="VER-001",
            severity="BLOCKER",
            category="Versioning",
            location="root",
            summary="No 'version:' field declared.",
            detail="Versioning is mandatory for any production API.",
            remediation="version: v1",
        )
        return  # Other version checks pointless without a version

    # VER-002: version in baseUri
    if "{version}" not in base_uri:
        result.add(
            rule_id="VER-002",
            severity="MAJOR",
            category="Versioning",
            location=f"baseUri: {base_uri!r}",
            summary="'{version}' placeholder missing from baseUri.",
            detail=(
                "Without {version} in the URI, breaking changes cannot coexist "
                "with previous major versions."
            ),
            remediation="baseUri: https://api.example.com/{version}/your-api",
        )

    # VER-003: avoid patch versions
    if re.match(r"^v?\d+\.\d+\.\d+", str(version)):
        result.add(
            rule_id="VER-003",
            severity="INFO",
            category="Versioning",
            location=f"version: {version!r}",
            summary="Version contains patch level — use major version only.",
            detail=(
                f"'{version}' should be 'v1' in the public version string. "
                "Track patches via implementation versions."
            ),
            remediation="version: v1",
        )


def check_documentation(spec: dict[str, Any], result: AuditResult) -> None:
    """DOC-001 to DOC-003."""
    description = spec.get("description") or ""
    if len(description.strip()) < 50:
        result.add(
            rule_id="DOC-001",
            severity="MAJOR",
            category="Documentation",
            location="root description:",
            summary=(
                f"Root description is {len(description.strip())} characters "
                "(< 50 minimum)."
            ),
            detail=(
                "The root description is the first paragraph consumers read on "
                "Exchange — it must communicate scope, layer, and audience."
            ),
            remediation=(
                "description: |\n"
                "  System API exposing the orders system of record. Provides CRUD\n"
                "  access for downstream Process and Experience APIs."
            ),
        )

    # DOC-002: resource descriptions
    missing = []
    for path, resource in walk_resources(spec):
        if not isinstance(resource, dict):
            continue
        if "description" not in resource:
            missing.append(path)
    if missing:
        result.add(
            rule_id="DOC-002",
            severity="MINOR",
            category="Documentation",
            location=f"{len(missing)} resources",
            summary=f"{len(missing)} resource(s) without a description.",
            detail=(
                "Resource descriptions appear in the Exchange UI as the first "
                "hint of intent."
            ),
            remediation=(
                "/customer-orders:\n"
                "  description: Customer orders held in the orders SoR.\n"
                "  get: ..."
            ),
        )

    # DOC-003: documentation: section
    if not spec.get("documentation"):
        result.add(
            rule_id="DOC-003",
            severity="INFO",
            category="Documentation",
            location="root",
            summary="No 'documentation:' section.",
            detail="Add usage examples and onboarding articles for consumers.",
            remediation=(
                "documentation:\n"
                "  - title: Getting started\n"
                "    content: |\n"
                "      How to obtain credentials and call the first endpoint."
            ),
        )


# ─── Orchestrator ───────────────────────────────────────────────────────────


CHECKS = [
    ("naming", check_naming),
    ("apic", check_apic),
    ("reuse", check_reuse),
    ("spec_quality", check_spec_quality),
    ("security", check_security),
    ("versioning", check_versioning),
    ("documentation", check_documentation),
]


def audit(raml_path: Path) -> AuditResult:
    result = AuditResult(raml_path=str(raml_path))
    try:
        spec = load_raml(raml_path)
    except FileNotFoundError:
        result.parse_ok = False
        result.parse_error = f"File not found: {raml_path}"
        return result
    except (yaml.YAMLError, ValueError) as exc:
        result.parse_ok = False
        result.parse_error = str(exc)
        return result

    for _, check_fn in CHECKS:
        try:
            check_fn(spec, result)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(
                f"WARNING: check {check_fn.__name__} failed: {exc}\n"
            )

    # Sort findings: BLOCKER first, then MAJOR, MINOR, INFO
    severity_order = {"BLOCKER": 0, "MAJOR": 1, "MINOR": 2, "INFO": 3}
    result.findings.sort(
        key=lambda f: (severity_order.get(f.severity, 99), f.rule_id)
    )
    return result


# ─── CLI entry point ────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit a MuleSoft RAML 1.0 spec for production readiness."
    )
    parser.add_argument(
        "--raml",
        type=Path,
        required=True,
        help="Path to the RAML file to audit.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("findings.json"),
        help="Path to the output JSON file (default: findings.json).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code if any BLOCKER is found.",
    )
    args = parser.parse_args()

    try:
        result = audit(args.raml)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"ERROR: {exc}\n")
        return 2

    if not result.parse_ok:
        sys.stderr.write(f"ERROR: {result.parse_error}\n")
        return 1

    payload = result.summary()
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    counts = payload["counts"]
    sys.stdout.write(
        f"✓ Audit complete: {payload['total_findings']} findings, "
        f"score {payload['score']}/100, verdict {payload['verdict']}\n"
        f"  BLOCKER: {counts['BLOCKER']}  MAJOR: {counts['MAJOR']}  "
        f"MINOR: {counts['MINOR']}  INFO: {counts['INFO']}\n"
        f"  → {args.out}\n"
    )

    if args.strict and result.has_blocker():
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
