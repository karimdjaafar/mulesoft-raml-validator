#!/usr/bin/env python3
"""
generate_best_practices.py — Refactor a RAML to resolve every finding from
an audit, producing a corrected RAML and a transformations.json that traces
each transformation.

Usage:
    python generate_best_practices.py \
        --raml input.raml \
        --findings findings.json \
        --out-raml refactored.raml \
        --out-transformations transformations.json

Design principles:
    - One transformation per rule. Idempotent: if the finding is absent, the
      transformation is a silent no-op.
    - Mechanical fixes are applied directly. Heuristic fixes log their
      reasoning. Architectural fixes (where multiple valid choices exist)
      apply a default and flag it for human review.
    - The output RAML is parsed by audit_raml.py to verify zero findings —
      that round-trip is the contract.

Exit codes:
    0   refactor completed (transformations.json may be empty if no findings)
    2   could not parse the RAML or findings JSON
    3   missing required argument or file not found
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
sys.path.insert(0, str(Path(__file__).resolve().parent))
from version import SKILL_VERSION, VERSION  # single source of the version

# ---------------------------------------------------------------------------
# YAML setup — same _Include machinery as audit_raml.py
# ---------------------------------------------------------------------------

class _Include:
    __slots__ = ("path",)
    def __init__(self, path: str) -> None: self.path = path
    def __repr__(self) -> str: return f"<!include {self.path}>"

def _include_constructor(loader, node) -> _Include:
    return _Include(loader.construct_scalar(node))

yaml.SafeLoader.add_constructor("!include", _include_constructor)

# Preserve insertion order so the output reads top-down naturally.
class _OrderedDumper(yaml.SafeDumper):
    pass

def _dict_representer(dumper, data):
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())

_OrderedDumper.add_representer(dict, _dict_representer)
_OrderedDumper.add_representer(OrderedDict, _dict_representer)


def _str_representer(dumper, data):
    # v1.5.0: keep multi-line text (descriptions, documentation) as a literal
    # block "|" instead of a quoted string with doubled line breaks.
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_OrderedDumper.add_representer(str, _str_representer)

# ---------------------------------------------------------------------------
# Helpers (mirrors audit_raml.py — kept compatible)
# ---------------------------------------------------------------------------

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
WRITE_METHODS = {"post", "put", "patch", "delete"}
URI_PARAM_RE = re.compile(r"^\{[^}]+\}$")
LAYER_PREFIX_RE = re.compile(r"^(s|p|x)-[a-z0-9]")
TITLE_RE = re.compile(r"^(s|p|x)-[a-z0-9]+(?:-[a-z0-9]+)*$")
ORCHESTRATION_VERBS = (
    "process", "calculate", "compute", "orchestrate", "validate-and-",
    "submit-and-", "execute"
)
ORCHESTRATION_NOUNS = {
    "process": "instructions",
    "calculate": "calculations",
    "compute": "computations",
    "orchestrate": "orchestrations",
    "execute": "executions",
}
SENSITIVE_TOKENS = ("payment", "auth", "user", "password", "credential",
                    "token", "secret")
SCOPE_HINTS = {
    "payment":    "payments:write",
    "auth":       "auth:write",
    "password":   "users:credentials:write",
    "credential": "users:credentials:write",
    "user":       "users:write",
    "token":      "auth:write",
    "secret":     "secrets:write",
}


def kebab(s: str) -> str:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s)
    s = re.sub(r"[\s_]+", "-", s.strip())  # v1.5.0: spaces too
    s = re.sub(r"-{2,}", "-", s)
    return s.lower()


def camel(s: str) -> str:
    parts = re.split(r"[_\-]", s)
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


def pluralize(s: str) -> str:
    if s.endswith("s") or s.endswith("data"):
        return s
    if s.endswith("y") and len(s) > 1 and s[-2] not in "aeiou":
        return s[:-1] + "ies"
    return s + "s"


def has_finding(findings: list[dict], rule: str) -> bool:
    return any(f["rule"] == rule for f in findings)


def get_finding(findings: list[dict], rule: str) -> dict | None:
    for f in findings:
        if f["rule"] == rule:
            return f
    return None


# ---------------------------------------------------------------------------
# Transformation dataclass (lightweight)
# ---------------------------------------------------------------------------

def make_transformation(rule: str, kind: str, before: str, after: str,
                         reasoning: str, confidence: str = "high") -> dict:
    """kind: 'mechanical' | 'heuristic' | 'architectural'
       confidence: 'high' | 'medium' | 'low'"""
    return {
        "rule": rule,
        "kind": kind,
        "before": before,
        "after": after,
        "reasoning": reasoning,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Layer inference (heuristic) — drives several transformations
# ---------------------------------------------------------------------------

def infer_layer(spec: dict) -> tuple[str, str]:
    """Returns (layer, reasoning). layer in {'s','p','x'}."""
    title = spec.get("title", "") or ""
    m = LAYER_PREFIX_RE.match(title)
    if m:
        return m.group(1), f"Title already declares layer prefix '{m.group(1)}-'"

    # Heuristic: presence of orchestration verbs in resource paths → Process layer
    has_verbs = False
    for k in spec.keys():
        if isinstance(k, str) and k.startswith("/"):
            seg = k.lstrip("/").split("/")[0]
            if any(v.rstrip("-") in seg for v in ORCHESTRATION_VERBS):
                has_verbs = True
                break

    if has_verbs:
        return "p", "Resources contain orchestration verbs (e.g. /payment-process); Process layer is the natural fit"
    # Default to System for noun-shaped specs
    return "s", "Default to System (s-) layer for noun-shaped resource specs; consider 'p-' or 'x-' if the API orchestrates or serves a specific channel"


def infer_api_name(spec: dict) -> str:
    """Heuristic name for the API. Used when title needs rebuilding."""
    title = spec.get("title", "") or ""
    # If title has a layer prefix, strip it and kebab-case the rest
    m = LAYER_PREFIX_RE.match(title)
    if m:
        rest = title[m.end()-1:]  # keep from the second char
        return kebab(rest)
    # Otherwise kebab-case the whole title minus 'API' suffix
    base = re.sub(r"(API|api)$", "", title).strip()
    if not base:
        # Fall back to the first resource
        for k in spec.keys():
            if isinstance(k, str) and k.startswith("/"):
                base = kebab(k.lstrip("/").split("/")[0])
                break
    base = kebab(base) if base else "api"
    if not base.endswith("-api"):
        base = base + "-api"
    return base


# ---------------------------------------------------------------------------
# Resource walking — needs to mutate paths so we work with the raw dict
# ---------------------------------------------------------------------------

def walk_resources(node: dict, prefix: str = ""):
    for k, v in list(node.items()):
        if not isinstance(k, str) or not k.startswith("/"):
            continue
        full = prefix + k
        if isinstance(v, dict):
            yield full, k, v, node
            yield from walk_resources(v, full)


def each_method(resource: dict):
    for k, v in list(resource.items()):
        if isinstance(k, str) and k.lower() in HTTP_METHODS and isinstance(v, dict):
            yield k.lower(), v


# ---------------------------------------------------------------------------
# Transformations — one function per rule (or rule group)
# ---------------------------------------------------------------------------

def _kebab_path_segments(path_key: str) -> str:
    """Apply kebab-case to each non-URI-param segment of a path key.
       Path keys can be composite, e.g. '/{userId}/password' has two
       segments ['{userId}', 'password']; only the second should be
       kebab-cased."""
    if not path_key.startswith("/"):
        return path_key
    parts = path_key.lstrip("/").split("/")
    new_parts = []
    for p in parts:
        if URI_PARAM_RE.match(p):
            new_parts.append(p)  # preserve {userId} verbatim
        else:
            new_parts.append(kebab(p))
    return "/" + "/".join(new_parts)


def fix_naming_001_kebab_paths(spec: dict, findings: list[dict],
                                transformations: list[dict]) -> None:
    """Rename camelCase / snake_case resource path segments to kebab-case.
       URI parameters like {userId} inside composite paths are preserved."""
    if not has_finding(findings, "NAMING-001"):
        return
    renames: list[tuple[dict, str, str]] = []
    for full, key, value, parent in walk_resources(spec):
        new_key = _kebab_path_segments(key)
        if new_key != key:
            renames.append((parent, key, new_key))

    for parent, old, new in renames:
        # Preserve insertion order: rebuild the dict
        new_parent = OrderedDict()
        for k, v in parent.items():
            new_parent[new if k == old else k] = v
        parent.clear()
        parent.update(new_parent)
        transformations.append(make_transformation(
            "NAMING-001", "mechanical",
            before=old, after=new,
            reasoning="Resource paths must be kebab-case (lowercase, hyphen-separated)."
        ))


def fix_naming_002_pluralize(spec: dict, findings: list[dict],
                              transformations: list[dict]) -> None:
    """Pluralize singular collection resources (skip singletons under URI-param parents)."""
    if not has_finding(findings, "NAMING-002"):
        return
    renames: list[tuple[dict, str, str]] = []
    # Need to track parent URI params for the singleton-exception
    def walk(node, parent_was_uri_param=False):
        for k, v in list(node.items()):
            if not isinstance(k, str) or not k.startswith("/"):
                continue
            # v1.5.0: a key can hold several segments ("/users/{userId}/password");
            # judge only its last segment, like the analyzer does.
            parts = k.lstrip("/").split("/")
            last = parts[-1]
            if URI_PARAM_RE.match(last):
                if isinstance(v, dict):
                    walk(v, parent_was_uri_param=True)
                continue
            prev_is_uri = (URI_PARAM_RE.match(parts[-2]) is not None
                           if len(parts) >= 2 else parent_was_uri_param)
            # Skip if singleton under URI-param (e.g. /{userId}/password)
            if not prev_is_uri:
                # Skip verbs (APIC-002 handles them)
                if not any(verb.rstrip("-") in last for verb in ORCHESTRATION_VERBS):
                    plural = pluralize(last)
                    if plural != last:
                        renames.append((node, k, "/" + "/".join(parts[:-1] + [plural])))
            if isinstance(v, dict):
                walk(v, parent_was_uri_param=False)
    walk(spec)

    for parent, old, new in renames:
        new_parent = OrderedDict()
        for k, v in parent.items():
            new_parent[new if k == old else k] = v
        parent.clear()
        parent.update(new_parent)
        transformations.append(make_transformation(
            "NAMING-002", "mechanical",
            before=old, after=new,
            reasoning="Collection resources must be plural nouns."
        ))


def fix_naming_003_camel_query_params(spec: dict, findings: list[dict],
                                        transformations: list[dict]) -> None:
    """Convert snake_case query parameters to camelCase."""
    if not has_finding(findings, "NAMING-003"):
        return
    for full, key, value, parent in walk_resources(spec):
        for method_name, method in each_method(value):
            qp = method.get("queryParameters")
            if not isinstance(qp, dict):
                continue
            renames = []
            for qname in list(qp.keys()):
                if not isinstance(qname, str):
                    continue
                if not re.match(r"^[a-z][a-zA-Z0-9]*$", qname):
                    new_name = camel(qname)
                    if new_name != qname:
                        renames.append((qname, new_name))
            for old, new in renames:
                # Preserve order
                new_qp = OrderedDict()
                for k, v in qp.items():
                    new_qp[new if k == old else k] = v
                qp.clear()
                qp.update(new_qp)
                transformations.append(make_transformation(
                    "NAMING-003", "mechanical",
                    before=f"{method_name.upper()} {full}?{old}",
                    after=f"{method_name.upper()} {full}?{new}",
                    reasoning="Query parameters must be camelCase."
                ))


def fix_naming_004_title_layer_prefix(spec: dict, findings: list[dict],
                                        transformations: list[dict],
                                        layer: str, layer_reasoning: str) -> None:
    """Add the s-/p-/x- layer prefix to the title."""
    if not has_finding(findings, "NAMING-004"):
        return
    old_title = spec.get("title", "") or ""
    if TITLE_RE.match(old_title):
        return  # already prefixed and kebab-case
    api_name = infer_api_name(spec)
    new_title = f"{layer}-{api_name}"
    spec["title"] = new_title
    transformations.append(make_transformation(
        "NAMING-004", "heuristic",
        before=f"title: {old_title}",
        after=f"title: {new_title}",
        reasoning=f"Layer inferred: '{layer}-'. {layer_reasoning}",
        confidence="medium"
    ))


def fix_apic_002_orchestration_verbs(spec: dict, findings: list[dict],
                                       transformations: list[dict]) -> None:
    """Rename orchestration verbs to noun forms (e.g. /payment-process → /payment-instructions)."""
    if not has_finding(findings, "APIC-002"):
        return
    renames: list[tuple[dict, str, str]] = []
    for full, key, value, parent in walk_resources(spec):
        seg = key.lstrip("/")
        if URI_PARAM_RE.match(seg):
            continue
        for verb_marker in (v.rstrip("-") for v in ORCHESTRATION_VERBS):
            if verb_marker in seg:
                # Replace verb with its noun form, e.g. payment-process → payment-instructions
                noun = ORCHESTRATION_NOUNS.get(verb_marker, "operations")
                new_seg = re.sub(rf"\b{verb_marker}\b", noun, seg)
                # Ensure it ends in plural/noun form
                if new_seg != seg:
                    # Make sure the ending is plural-ish
                    if not new_seg.endswith("s"):
                        new_seg = pluralize(new_seg)
                    renames.append((parent, key, "/" + new_seg))
                break  # one rename per resource
    for parent, old, new in renames:
        new_parent = OrderedDict()
        for k, v in parent.items():
            new_parent[new if k == old else k] = v
        parent.clear()
        parent.update(new_parent)
        transformations.append(make_transformation(
            "APIC-002", "architectural",
            before=old, after=new,
            reasoning=("Orchestration verbs in resource paths belong to a Process API. "
                       "Renamed to a noun form. If this is a System API, consider extracting "
                       "the orchestration to a separate Process API instead of just renaming."),
            confidence="medium"
        ))


def fix_doc_001_root_description(spec: dict, findings: list[dict],
                                   transformations: list[dict],
                                   layer: str) -> None:
    """Expand the root description to >= 50 chars."""
    if not has_finding(findings, "DOC-001"):
        return
    old_desc = spec.get("description", "") or ""
    layer_word = {"s": "System", "p": "Process", "x": "Experience"}[layer]
    api_name = infer_api_name(spec)
    new_desc = (
        f"{layer_word} API exposing {api_name.replace('-api','').replace('-',' ')} "
        f"capabilities. Auto-generated description from generate_best_practices.py "
        f"(v{VERSION}). Edit this paragraph to describe the actual purpose, owners, "
        f"backing systems, and consumers of this API."
    )
    spec["description"] = new_desc
    transformations.append(make_transformation(
        "DOC-001", "heuristic",
        before=f"description: {old_desc}" if old_desc else "(no description field)",
        after=f"description: <expanded paragraph, {len(new_desc)} chars>",
        reasoning="Auto-generated placeholder description meeting the 50-char minimum. Edit to describe the actual API.",
        confidence="low"
    ))


def fix_doc_002_resource_descriptions(spec: dict, findings: list[dict],
                                        transformations: list[dict]) -> None:
    """Add a one-line description to every resource."""
    if not has_finding(findings, "DOC-002"):
        return
    added_count = 0
    for full, key, value, parent in walk_resources(spec):
        if "description" not in value:
            seg = key.lstrip("/")
            if URI_PARAM_RE.match(seg):
                # singleton or item resource
                value["description"] = f"Single resource identified by the {seg.strip('{}')} path parameter."
            else:
                value["description"] = f"Operations on the {seg.replace('-', ' ')} resource."
            # Move description to first position for readability
            new_value = OrderedDict([("description", value["description"])])
            for k, v in value.items():
                if k != "description":
                    new_value[k] = v
            value.clear()
            value.update(new_value)
            added_count += 1
    if added_count:
        transformations.append(make_transformation(
            "DOC-002", "mechanical",
            before=f"{added_count} resources without description",
            after=f"all {added_count} resources now have a one-line description",
            reasoning="Auto-generated descriptions; edit them to capture domain-specific intent."
        ))


def fix_doc_003_documentation_section(spec: dict, findings: list[dict],
                                        transformations: list[dict]) -> None:
    """Add a root documentation: section."""
    if not has_finding(findings, "DOC-003"):
        return
    if "documentation" in spec:
        return
    spec["documentation"] = [
        OrderedDict([
            ("title", "Overview"),
            ("content", "High-level description of the API. Edit this section to describe the API's purpose, scope, and ownership."),
        ]),
        OrderedDict([
            ("title", "Getting started"),
            ("content", "How consumers should authenticate and call the API. Edit this section with concrete onboarding steps."),
        ]),
        OrderedDict([
            ("title", "Error model"),
            ("content", "All errors follow the ErrorResponse schema. Codes are stable; messages are advisory."),
        ]),
    ]
    transformations.append(make_transformation(
        "DOC-003", "heuristic",
        before="(no documentation section)",
        after="documentation: [Overview, Getting started, Error model]",
        reasoning="Skeleton documentation section added with three standard chapters. Edit each chapter to add domain-specific content.",
        confidence="medium"
    ))


def fix_ver_002_baseuri_version(spec: dict, findings: list[dict],
                                  transformations: list[dict]) -> None:
    """Interpolate {version} into baseUri."""
    if not has_finding(findings, "VER-002"):
        return
    base_uri = spec.get("baseUri", "") or ""
    if "{version}" in base_uri:
        return
    # Append /{version} if not present
    new_base = base_uri.rstrip("/") + "/{version}"
    spec["baseUri"] = new_base
    transformations.append(make_transformation(
        "VER-002", "mechanical",
        before=f"baseUri: {base_uri}",
        after=f"baseUri: {new_base}",
        reasoning="Version placeholder interpolated so consumers can pin to a major version via the URL."
    ))


def fix_ver_003_simplify_version(spec: dict, findings: list[dict],
                                   transformations: list[dict]) -> None:
    """Reduce version: vN.M.P → vN."""
    if not has_finding(findings, "VER-003"):
        return
    version = spec.get("version", "") or ""
    if not isinstance(version, str):
        return
    m = re.match(r"^v(\d+)", version)
    if not m:
        return
    new_version = f"v{m.group(1)}"
    if new_version == version:
        return
    spec["version"] = new_version
    transformations.append(make_transformation(
        "VER-003", "mechanical",
        before=f"version: {version}",
        after=f"version: {new_version}",
        reasoning="URI version reduced to major level; patch/minor levels belong in the changelog and response headers, not the URL."
    ))


def fix_sec_001_security_schemes(spec: dict, findings: list[dict],
                                   transformations: list[dict]) -> None:
    """Add OAuth 2.0 securitySchemes and root securedBy."""
    if not has_finding(findings, "SEC-001"):
        return
    if "securitySchemes" not in spec:
        spec["securitySchemes"] = OrderedDict([
            ("oauth_2_0", OrderedDict([
                ("type", "OAuth 2.0"),
                ("describedBy", OrderedDict([
                    ("headers", OrderedDict([
                        ("Authorization", OrderedDict([
                            ("type", "string"),
                            ("example", "Bearer eyJhbGc..."),
                        ])),
                    ])),
                ])),
                ("settings", OrderedDict([
                    ("authorizationUri", "https://auth.example.com/oauth/authorize"),
                    ("accessTokenUri", "https://auth.example.com/oauth/token"),
                    ("authorizationGrants", ["authorization_code", "client_credentials"]),
                    ("scopes", _gather_scopes(spec)),
                ])),
            ])),
        ])
    if "securedBy" not in spec:
        spec["securedBy"] = ["oauth_2_0"]
    transformations.append(make_transformation(
        "SEC-001", "heuristic",
        before="(no securitySchemes, no root securedBy)",
        after="OAuth 2.0 scheme + root securedBy: [ oauth_2_0 ]",
        reasoning="OAuth 2.0 added with placeholder authorization/token URIs. Replace these with the real identity-provider URLs before deploying.",
        confidence="medium"
    ))


def _gather_scopes(spec: dict) -> list[str]:
    """Heuristic: derive scope names from resource path segments."""
    scopes = set()
    for k in spec.keys():
        if isinstance(k, str) and k.startswith("/"):
            seg = k.lstrip("/").split("/")[0]
            base = re.sub(r"s$", "", seg.replace("-", "_"))
            scopes.add(f"{base}:read")
            scopes.add(f"{base}:write")
    return sorted(scopes) if scopes else ["api:read", "api:write"]


def fix_sec_002_sensitive_endpoints(spec: dict, findings: list[dict],
                                     transformations: list[dict]) -> None:
    """Add explicit per-method securedBy with narrow scopes on sensitive endpoints."""
    if not has_finding(findings, "SEC-002"):
        return
    affected = []
    for full, key, value, parent in walk_resources(spec):
        is_sensitive = any(tok in full.lower() for tok in SENSITIVE_TOKENS)
        if not is_sensitive:
            continue
        for method_name, method in each_method(value):
            if method_name not in WRITE_METHODS:
                continue
            if "securedBy" in method:
                continue
            scope = next((s for tok, s in SCOPE_HINTS.items() if tok in full.lower()),
                         "api:write")
            method["securedBy"] = [
                OrderedDict([("oauth_2_0", OrderedDict([("scopes", [scope])]))])
            ]
            affected.append(f"{method_name.upper()} {full} → scope '{scope}'")
    if affected:
        transformations.append(make_transformation(
            "SEC-002", "heuristic",
            before=f"{len(affected)} sensitive endpoints with no per-method securedBy",
            after="\n  ".join(affected),
            reasoning="Scoped securedBy added per sensitive endpoint with a narrow scope inferred from the path. Verify the scope name matches your identity-provider configuration.",
            confidence="medium"
        ))


def fix_spec_003_standard_errors(spec: dict, findings: list[dict],
                                   transformations: list[dict]) -> None:
    """Add a standardErrors trait and apply it to every method via is:."""
    if not has_finding(findings, "SPEC-003"):
        return

    # Ensure ErrorResponse type exists
    if "types" not in spec:
        spec["types"] = OrderedDict()
    if "ErrorResponse" not in spec["types"]:
        spec["types"]["ErrorResponse"] = OrderedDict([
            ("type", "object"),
            ("properties", OrderedDict([
                ("code",     OrderedDict([("type", "string"), ("example", "VALIDATION_ERROR")])),
                ("message",  OrderedDict([("type", "string"), ("example", "Field 'foo' is required")])),
                ("traceId",  OrderedDict([("type", "string"), ("example", "8c7e1f6a-3d2b-4c5e-9a1b-7f3d4c5e9a1b")])),
            ])),
        ])

    # Define standardErrors trait
    if "traits" not in spec:
        spec["traits"] = OrderedDict()
    err_codes = [(400, "VALIDATION_ERROR"), (401, "UNAUTHENTICATED"),
                 (403, "FORBIDDEN"), (404, "NOT_FOUND"),
                 (429, "RATE_LIMITED"), (500, "INTERNAL_ERROR")]
    if "standardErrors" not in spec["traits"]:
        spec["traits"]["standardErrors"] = OrderedDict([
            ("responses", OrderedDict([
                (str(code), OrderedDict([
                    ("body", OrderedDict([
                        ("application/json", OrderedDict([
                            ("type", "ErrorResponse"),
                            ("example", OrderedDict([
                                ("code", code_name),
                                ("message", f"Example {code_name} message"),
                                ("traceId", "8c7e1f6a-3d2b-4c5e-9a1b-7f3d4c5e9a1b"),
                            ])),
                        ])),
                    ])),
                ])) for code, code_name in err_codes
            ])),
        ])

    # Apply trait to every method
    methods_updated = 0
    for full, key, value, parent in walk_resources(spec):
        for method_name, method in each_method(value):
            existing_is = method.get("is")
            if existing_is is None:
                method["is"] = ["standardErrors"]
            elif isinstance(existing_is, list) and "standardErrors" not in existing_is:
                method["is"] = list(existing_is) + ["standardErrors"]
            else:
                continue
            methods_updated += 1

    transformations.append(make_transformation(
        "SPEC-003", "mechanical",
        before="No 4xx/5xx responses defined on any endpoint",
        after=f"standardErrors trait defined and applied to {methods_updated} methods",
        reasoning="Single trait defining 400/401/403/404/429/500 ensures every method has a complete error contract."
    ))


def fix_reuse_001_pageable_trait(spec: dict, findings: list[dict],
                                   transformations: list[dict]) -> None:
    """Extract inline pagination into a pageable trait."""
    if not has_finding(findings, "REUSE-001"):
        return

    if "traits" not in spec:
        spec["traits"] = OrderedDict()
    if "pageable" not in spec["traits"]:
        spec["traits"]["pageable"] = OrderedDict([
            ("queryParameters", OrderedDict([
                ("page",     OrderedDict([("type", "integer"), ("default", 1), ("minimum", 1)])),
                ("pageSize", OrderedDict([("type", "integer"), ("default", 25),
                                            ("minimum", 1), ("maximum", 100)])),
            ])),
        ])

    methods_updated = 0
    for full, key, value, parent in walk_resources(spec):
        for method_name, method in each_method(value):
            if method_name != "get":
                continue
            qp = method.get("queryParameters")
            if not isinstance(qp, dict):
                continue
            qkeys_lower = {str(k).lower() for k in qp.keys()}
            if not ({"page", "pagesize"} & qkeys_lower):
                continue
            # Strip page/pageSize from inline qparams
            new_qp = OrderedDict()
            for k, v in qp.items():
                if str(k).lower() not in ("page", "pagesize"):
                    new_qp[k] = v
            if new_qp:
                method["queryParameters"] = new_qp
            else:
                method.pop("queryParameters", None)
            # Apply trait
            existing_is = method.get("is")
            if existing_is is None:
                method["is"] = ["pageable"]
            elif isinstance(existing_is, list) and "pageable" not in existing_is:
                method["is"] = ["pageable"] + list(existing_is)
            methods_updated += 1

    if methods_updated:
        transformations.append(make_transformation(
            "REUSE-001", "mechanical",
            before=f"{methods_updated} GET methods with inline page/pageSize",
            after=f"pageable trait defined and applied to {methods_updated} methods",
            reasoning="Pagination parameters factored into a single reusable trait; future changes to defaults or limits propagate everywhere."
        ))


def fix_spec_001_002_examples(spec: dict, findings: list[dict],
                                transformations: list[dict]) -> None:
    """Add minimal examples to request/response bodies that lack them."""
    needs_001 = has_finding(findings, "SPEC-001")
    needs_002 = has_finding(findings, "SPEC-002")
    if not (needs_001 or needs_002):
        return

    request_count = 0
    response_count = 0

    for full, key, value, parent in walk_resources(spec):
        for method_name, method in each_method(value):
            # Request body
            if needs_001:
                body = method.get("body")
                if isinstance(body, dict):
                    for media_type, body_def in body.items():
                        if not isinstance(body_def, dict):
                            # Convert "type: object" shorthand to dict form
                            method["body"][media_type] = OrderedDict([
                                ("type", body_def if isinstance(body_def, str) else "object"),
                                ("example", _placeholder_example()),
                            ])
                            request_count += 1
                        elif "example" not in body_def and "examples" not in body_def:
                            body_def["example"] = _placeholder_example()
                            request_count += 1

            # Response bodies
            if needs_002:
                responses = method.get("responses")
                if isinstance(responses, dict):
                    for code, resp in responses.items():
                        if not isinstance(resp, dict):
                            continue
                        rbody = resp.get("body")
                        if isinstance(rbody, dict):
                            for media_type, body_def in rbody.items():
                                if not isinstance(body_def, dict):
                                    rbody[media_type] = OrderedDict([
                                        ("type", body_def if isinstance(body_def, str) else "object"),
                                        ("example", _placeholder_example()),
                                    ])
                                    response_count += 1
                                elif "example" not in body_def and "examples" not in body_def:
                                    body_def["example"] = _placeholder_example()
                                    response_count += 1

    if request_count:
        transformations.append(make_transformation(
            "SPEC-001", "heuristic",
            before=f"{request_count} request bodies without example",
            after=f"placeholder examples added to {request_count} request bodies",
            reasoning="Generic placeholder examples added; replace with realistic domain-specific values to make Mocking Service useful.",
            confidence="low"
        ))
    if response_count:
        transformations.append(make_transformation(
            "SPEC-002", "heuristic",
            before=f"{response_count} response bodies without example",
            after=f"placeholder examples added to {response_count} response bodies",
            reasoning="Generic placeholder examples added; replace with realistic domain-specific values.",
            confidence="low"
        ))


def _placeholder_example() -> dict:
    return OrderedDict([
        ("id", "EXAMPLE-001"),
        ("status", "ACTIVE"),
        ("createdAt", "2026-05-06T12:00:00Z"),
    ])


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def parse_raml(path: Path) -> tuple[dict, str]:
    """Returns (parsed_spec, raml_header_line)."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    header = lines[0] if lines and lines[0].startswith("#%RAML") else "#%RAML 1.0"
    body = "\n".join(lines[1:]) if header == lines[0] else text
    try:
        data = yaml.safe_load(body)
    except yaml.YAMLError as exc:
        print(f"ERROR: failed to parse RAML: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict):
        print("ERROR: RAML root is not a mapping", file=sys.stderr)
        sys.exit(2)
    return data, header


def serialize_raml(spec: dict, header: str) -> str:
    """Re-emit the spec as RAML 1.0. Strips the !include placeholders since
    we don't follow them — any such reference becomes a literal string,
    which is fine for the single-file output mode."""
    body = yaml.dump(spec, Dumper=_OrderedDumper, default_flow_style=False,
                     sort_keys=False, allow_unicode=True, width=120)
    return header + "\n" + body


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raml", required=True)
    ap.add_argument("--findings", required=True)
    ap.add_argument("--out-raml", required=True)
    ap.add_argument("--out-transformations", required=True)
    args = ap.parse_args()

    raml_path = Path(args.raml)
    findings_path = Path(args.findings)
    if not raml_path.exists():
        print(f"ERROR: RAML not found: {raml_path}", file=sys.stderr); return 3
    if not findings_path.exists():
        print(f"ERROR: findings not found: {findings_path}", file=sys.stderr); return 3

    spec, header = parse_raml(raml_path)
    findings_data = json.loads(findings_path.read_text(encoding="utf-8"))
    findings = findings_data.get("findings", [])

    spec_copy = deepcopy(spec)  # work on a copy
    transformations: list[dict] = []

    # Infer layer once — drives several fixes
    layer, layer_reasoning = infer_layer(spec_copy)

    # Apply fixes in dependency order:
    #   1. Naming (paths) before APIC (which renames paths too)
    #   2. SEC-001 (root scheme) before SEC-002 (per-method scopes)
    #   3. Trait definitions before trait applications
    fix_naming_001_kebab_paths(spec_copy, findings, transformations)
    fix_apic_002_orchestration_verbs(spec_copy, findings, transformations)
    fix_naming_002_pluralize(spec_copy, findings, transformations)
    fix_naming_003_camel_query_params(spec_copy, findings, transformations)
    fix_naming_004_title_layer_prefix(spec_copy, findings, transformations,
                                        layer, layer_reasoning)
    fix_ver_002_baseuri_version(spec_copy, findings, transformations)
    fix_ver_003_simplify_version(spec_copy, findings, transformations)
    fix_doc_001_root_description(spec_copy, findings, transformations, layer)
    fix_doc_002_resource_descriptions(spec_copy, findings, transformations)
    fix_doc_003_documentation_section(spec_copy, findings, transformations)
    fix_sec_001_security_schemes(spec_copy, findings, transformations)
    fix_spec_003_standard_errors(spec_copy, findings, transformations)
    fix_reuse_001_pageable_trait(spec_copy, findings, transformations)
    fix_spec_001_002_examples(spec_copy, findings, transformations)
    fix_sec_002_sensitive_endpoints(spec_copy, findings, transformations)

    # Write outputs
    refactored = serialize_raml(spec_copy, header)
    Path(args.out_raml).write_text(refactored, encoding="utf-8")

    summary_payload = {
        "title": f"Remediation guide — {spec_copy.get('title', 'API')}",
        "source_raml": str(raml_path),
        "refactored_raml": args.out_raml,
        "date": datetime.date.today().isoformat(),
        "skill_version": SKILL_VERSION,
        "inferred_layer": layer,
        "layer_reasoning": layer_reasoning,
        "transformations": transformations,
        "transformation_count": len(transformations),
        "transformation_kinds": {
            "mechanical":    sum(1 for t in transformations if t["kind"] == "mechanical"),
            "heuristic":     sum(1 for t in transformations if t["kind"] == "heuristic"),
            "architectural": sum(1 for t in transformations if t["kind"] == "architectural"),
        },
    }
    Path(args.out_transformations).write_text(
        json.dumps(summary_payload, indent=2), encoding="utf-8"
    )

    print(f"Wrote {args.out_raml} and {args.out_transformations}: "
          f"{len(transformations)} transformations applied "
          f"({summary_payload['transformation_kinds']['mechanical']} mechanical, "
          f"{summary_payload['transformation_kinds']['heuristic']} heuristic, "
          f"{summary_payload['transformation_kinds']['architectural']} architectural).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
