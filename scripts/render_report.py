#!/usr/bin/env python3
"""
render_report.py — Render an HTML audit report matching the v1.3 visual design.

Usage:
  python render_report.py --findings findings.json --out report.html
"""
import argparse, json, sys, html, datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
sys.path.insert(0, str(Path(__file__).resolve().parent))
from version import SKILL_VERSION, VERSION  # single source of the version
from i18n_fr import CATEGORIES_FR, REMEDIATION_FR, RULES_FR, UI_FR

CATEGORIES = [
    ("Naming",              "",                       "NAMING"),
    ("API-Led Connectivity","",                       "APIC"),
    ("Reuse",               "traits / resourceTypes", "REUSE"),
    ("Spec",                "examples / schemas",     "SPEC"),
    ("Security",            "",                       "SEC"),
    ("Versioning",          "",                       "VER"),
    ("Documentation",       "",                       "DOC"),
]
SEV_PENALTY = {"BLOCKER": 15, "MAJOR": 5, "MINOR": 2, "INFO": 0}
SEV_ORDER   = {"BLOCKER": 0,  "MAJOR": 1, "MINOR": 2, "INFO": 3}

def build_matrix(findings):
    matrix = []
    for name, suffix, prefix in CATEGORIES:
        row = {"name": name, "suffix": suffix,
               "blocker": 0, "major": 0, "minor": 0, "info": 0}
        for f in findings:
            if f["rule"].startswith(prefix + "-"):
                row[f["severity"].lower()] += 1
        matrix.append(row)
    return matrix

def compute_totals(findings):
    t = {"blocker": 0, "major": 0, "minor": 0, "info": 0}
    for f in findings:
        t[f["severity"].lower()] += 1
    t["total"] = sum(t.values())
    return t

def compute_score(totals):
    score = 100 - (15*totals["blocker"] + 5*totals["major"]
                   + 2*totals["minor"] + 0*totals["info"])
    return max(score, 0)

def verdict_for(score, totals):
    return "GO" if (score >= 80 and totals["blocker"] == 0) else "NO-GO"

def render_finding_body(f, lang="en"):
    parts = []
    L = ("Impact", "Remediation") if lang == "en" else (UI_FR["impact"], UI_FR["remediation"])
    if f.get("impact"):
        parts.append(f"<p><strong>{L[0]}{'' if lang == 'en' else ' '}:</strong> {html.escape(f['impact'])}</p>")
    if f.get("remediation_text"):
        text = f["remediation_text"] if lang == "en" else REMEDIATION_FR.get(f["rule"], f["remediation_text"])
        parts.append(f"<p><strong>{L[1]}{'' if lang == 'en' else ' '}:</strong> {html.escape(text)}</p>")
    if f.get("remediation_code"):
        parts.append(f"<pre>{html.escape(f['remediation_code'])}</pre>")
    return "\n".join(parts)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", required=True, help="Path to findings JSON")
    ap.add_argument("--template-dir", default=str(Path(__file__).parent.parent / "templates"))
    ap.add_argument("--out", required=True, help="Output HTML path")
    ap.add_argument("--lang", choices=["en", "fr"], default="en",
                    help="Report language (default: en)")
    ap.add_argument("--api-description", default=None,
                    help="Description of the API to show instead of the one in the spec "
                         "(e.g. its French translation with --lang fr)")
    args = ap.parse_args()

    data = json.loads(Path(args.findings).read_text())
    findings = data["findings"]

    # Sort: severity first (BLOCKER → INFO), then by rule ID
    findings.sort(key=lambda f: (SEV_ORDER[f["severity"]], f["rule"]))

    # Enrich for template
    for f in findings:
        f["severity_lower"] = f["severity"].lower()
        if args.lang == "fr" and f["rule"] in RULES_FR:
            n = f["summary"].split(" occurrences — ")[0] if " occurrences — " in f["summary"] else None
            f["summary"] = (UI_FR["occurrences"].format(n=n) if n and n.isdigit() else "") + RULES_FR[f["rule"]][0]
            f["impact"] = RULES_FR[f["rule"]][1]
        f["body_html"] = render_finding_body(f, args.lang)

    matrix = build_matrix(findings)
    if args.lang == "fr":
        for row in matrix:
            row["name"] = CATEGORIES_FR.get(row["name"], row["name"])
            row["suffix"] = CATEGORIES_FR.get(row["suffix"], row["suffix"])
    totals = compute_totals(findings)
    score  = compute_score(totals)
    verdict = verdict_for(score, totals)

    summary_line = (f"Audit result &mdash; {totals['blocker']} blocker"
                    f"{'s' if totals['blocker']!=1 else ''}, "
                    f"{totals['major']} major"
                    f"{'s' if totals['major']!=1 else ''}, "
                    f"{totals['minor']} minor"
                    f"{'s' if totals['minor']!=1 else ''}, "
                    f"{totals['info']} informational finding"
                    f"{'s' if totals['info']!=1 else ''}.")

    if args.lang == "fr":
        summary_line = (f"Résultat de l'audit &mdash; {totals['blocker']} bloquant(s), "
                        f"{totals['major']} majeur(s), {totals['minor']} mineur(s), "
                        f"{totals['info']} information(s).")

    report = {
        "title":         data.get("title", "RAML Audit Report"),
        "subtitle":      data.get("subtitle", ""),
        "spec_path":     data.get("spec_path", "(unspecified)"),
        "date":          data.get("date", datetime.date.today().isoformat()),
        "skill_version": data.get("skill_version", SKILL_VERSION),
        "score":         score,
        "verdict":       verdict,
        "summary_line":  summary_line,
        "api":           data.get("api"),   # v1.4.2; absent in older findings
    }
    if report["api"] and args.api_description:
        report["api"] = dict(report["api"], description=args.api_description.strip(), description_given=True)

    env = Environment(
        loader=FileSystemLoader(args.template_dir),
        autoescape=select_autoescape(["html"]),
    )
    if args.lang == "fr":
        report["title"] = report["title"].replace(UI_FR["report_prefix_en"], UI_FR["report_prefix_fr"])
        report["subtitle"] = UI_FR["subtitle"]
    template = env.get_template("report.html.j2" if args.lang == "en" else "report.fr.html.j2")
    html_out = template.render(report=report, matrix=matrix, totals=totals,
                               findings=findings)
    Path(args.out).write_text(html_out, encoding="utf-8")
    print(f"Wrote {args.out} ({len(findings)} findings, score {score}, {verdict})")

if __name__ == "__main__":
    main()
