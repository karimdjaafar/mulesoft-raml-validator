#!/usr/bin/env python3
"""
render_remediation_guide.py — Render a personalized remediation guide
(Markdown + HTML) from a transformations.json produced by
generate_best_practices.py.

The guide explains every transformation applied during refactoring, with
before/after pairs, reasoning, confidence levels, and explicit human-review
flags for heuristic and architectural choices.

Usage:
    python render_remediation_guide.py \
        --transformations transformations.json \
        --findings findings.json \
        --out-md guide.md \
        --out-html guide.html
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
sys.path.insert(0, str(Path(__file__).resolve().parent))
from version import SKILL_VERSION, VERSION  # single source of the version
from i18n_fr import CONFIDENCE_LABEL_FR, KIND_LABEL_FR, UI_FR, layer_reasoning_fr, reasoning_fr


KIND_LABEL = {
    "mechanical":    "Mechanical",
    "heuristic":     "Heuristic",
    "architectural": "Architectural",
}
KIND_BADGE_CLASS = {
    "mechanical":    "kind-mechanical",
    "heuristic":     "kind-heuristic",
    "architectural": "kind-architectural",
}
CONFIDENCE_LABEL = {
    "high":   "high",
    "medium": "medium",
    "low":    "low — please review",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transformations", required=True)
    ap.add_argument("--findings", default=None,
                    help="Original findings.json (optional, used to count "
                         "starting findings for the executive summary)")
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-html", required=True)
    ap.add_argument("--lang", choices=["en", "fr"], default="en",
                    help="Guide language (default: en)")
    ap.add_argument("--api-description", default=None,
                    help="Description of the API to show instead of the one in the spec "
                         "(e.g. its French translation with --lang fr)")
    ap.add_argument("--template-dir",
                    default=str(Path(__file__).parent.parent / "templates"))
    args = ap.parse_args()

    payload = json.loads(Path(args.transformations).read_text())
    transformations = payload.get("transformations", [])

    starting_findings = 0
    starting_score = None
    api = None
    if args.findings:
        try:
            findings_data = json.loads(Path(args.findings).read_text())
            starting_findings = len(findings_data.get("findings", []))
            starting_score = findings_data.get("score")
            api = findings_data.get("api")   # v1.4.2: description of the audited API
        except Exception:
            pass

    # Group transformations by kind for the executive summary
    by_kind = {"mechanical": [], "heuristic": [], "architectural": []}
    for t in transformations:
        by_kind.setdefault(t["kind"], []).append(t)

    needs_review = [t for t in transformations
                    if t["kind"] in ("heuristic", "architectural")
                    or t.get("confidence") == "low"]

    context = {
        "title":             payload.get("title", "Remediation guide"),
        "source_raml":       payload.get("source_raml", "(unspecified)"),
        "refactored_raml":   payload.get("refactored_raml", "(unspecified)"),
        "date":              payload.get("date", datetime.date.today().isoformat()),
        "skill_version":     payload.get("skill_version",
                                          SKILL_VERSION),
        "inferred_layer":    payload.get("inferred_layer", "?"),
        "layer_reasoning":   payload.get("layer_reasoning", ""),
        "transformations":   transformations,
        "by_kind":           by_kind,
        "needs_review":      needs_review,
        "starting_findings": starting_findings,
        "starting_score":    starting_score,
        "api":               (dict(api, description=args.api_description.strip(), description_given=True)
                              if api and args.api_description else api),
        "kind_label":        KIND_LABEL,
        "kind_badge_class":  KIND_BADGE_CLASS,
        "confidence_label":  CONFIDENCE_LABEL,
    }

    if args.lang == "fr":
        context["title"] = context["title"].replace(UI_FR["guide_prefix_en"], UI_FR["guide_prefix_fr"])
        context["layer_reasoning"] = layer_reasoning_fr(context["layer_reasoning"])
        context["kind_label"] = KIND_LABEL_FR
        context["confidence_label"] = CONFIDENCE_LABEL_FR
        context["transformations"] = [dict(t, reasoning=reasoning_fr(t["reasoning"]))
                                      for t in transformations]
        context["by_kind"] = {k: [x for x in context["transformations"] if x["kind"] == k]
                              for k in by_kind}
        context["needs_review"] = [x for x in context["transformations"]
                                   if x["kind"] in ("heuristic", "architectural")
                                   or x.get("confidence") == "low"]
    suffix = "" if args.lang == "en" else ".fr"

    env = Environment(
        loader=FileSystemLoader(args.template_dir),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    md_tpl = env.get_template(f"remediation-guide{suffix}.md.j2")
    html_tpl = env.get_template(f"remediation-guide{suffix}.html.j2")

    Path(args.out_md).write_text(md_tpl.render(**context), encoding="utf-8")
    Path(args.out_html).write_text(html_tpl.render(**context), encoding="utf-8")

    print(f"Wrote {args.out_md} and {args.out_html}: "
          f"{len(transformations)} transformations documented "
          f"({len(needs_review)} need human review).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
