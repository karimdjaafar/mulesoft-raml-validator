#!/usr/bin/env python3
"""
Verify whether mulesoft-raml-validator is correctly deployed.

Path-agnostic since v1.5.0: the skill root is the parent of this script's
folder, wherever the skill is installed (claude.ai, Claude Code
~/.claude/skills, a plugin, or a git clone). Override with --root PATH.

Self-contained: no imports beyond the stdlib, no assumptions about prior
state, no external dependencies. Designed to be run in a fresh Claude
session via a single bash invocation.

Exit codes:
    0   fully deployed and smoke-test passes
    1   deployed but smoke-test produced wrong numbers (regression)
    2   wrong version installed
    3   skill folder exists but is incomplete (partial install)
    4   skill folder missing entirely
"""
import argparse
import json
import tempfile
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from version import VERSION  # single source of the version

_ap = argparse.ArgumentParser(description="Verify the mulesoft-raml-validator install.")
_ap.add_argument("--root", help="skill folder to check (default: the folder this script ships in)")
_args = _ap.parse_args()
SKILL_ROOT = Path(_args.root).resolve() if _args.root else Path(__file__).resolve().parent.parent
EXPECTED_VERSION = VERSION
PY = sys.executable or "python3"
TMP = Path(tempfile.mkdtemp(prefix="verify-raml-"))
EXPECTED_FILES = [
    "SKILL.md",
    "scripts/audit_raml.py",
    "scripts/render_report.py",
    "scripts/verify_install.py",
    "scripts/generate_best_practices.py",
    "scripts/render_remediation_guide.py",
    "templates/audit-report-template.md",
    "templates/report.html.j2",
    "templates/remediation-guide.md.j2",
    "templates/remediation-guide.html.j2",
    "references/raml-best-practices.md",
    "examples/README.md",
    "examples/customerOrderAPI.raml",
    "examples/customerOrderAPI-findings.json",
    "examples/s-customer-orders-api.raml",
    "examples/s-customer-orders-api-findings.json",
    "scripts/version.py",
    "scripts/i18n_fr.py",
    "scripts/raml_validator.py",
    "bin/raml-validator",
    "completions/_raml-validator",
    "completions/raml-validator.bash",
    "completions/raml-validator.ps1",
    "bin/raml-validator.cmd",
    "templates/report.fr.html.j2",
    "templates/remediation-guide.fr.html.j2",
    "templates/remediation-guide.fr.md.j2",
    "examples/demo/leave-management-api.raml",
    "examples/demo/leave-management-api-findings.json",
    "examples/demo/leave-management-api-best-practices.raml",
]
EXPECTED_BROKEN = {"score": 21, "verdict": "NO-GO", "findings": 17}
EXPECTED_CLEAN  = {"score": 100, "verdict": "GO", "findings": 0}
# v1.4.0 round-trip baseline: refactoring the broken fixture should yield 100/100
EXPECTED_REFACTORED = {"score": 100, "verdict": "GO", "findings": 0}
# v1.5.0 reference demo (examples/demo): audit, then refactor + re-audit
EXPECTED_DEMO = {"score": 26, "verdict": "NO-GO", "findings": 16}


def banner(s):
    line = "=" * 74
    print(f"\n{line}\n{s}\n{line}")


def report_outcome(level, summary, exit_code):
    banner(f"VERDICT — {level}")
    print(summary)
    print()
    print(f"Exit code: {exit_code}")
    sys.exit(exit_code)


# -------------------------------------------------------------------------
# Step 1 — does the skill folder exist at all?
# -------------------------------------------------------------------------
banner("Step 1 — Skill folder presence")
if not SKILL_ROOT.exists():
    print(f"FAIL: {SKILL_ROOT} does not exist.")
    report_outcome(
        "NOT INSTALLED",
        f"The skill folder is missing entirely. Deploy the v{EXPECTED_VERSION} bundle "
        f"(see INSTALL.md).",
        4,
    )
print(f"OK: {SKILL_ROOT} exists.")

# -------------------------------------------------------------------------
# Step 2 — what version is the SKILL.md banner?
# -------------------------------------------------------------------------
banner("Step 2 — Installed version")
skill_md = SKILL_ROOT / "SKILL.md"
if not skill_md.exists():
    report_outcome(
        "BROKEN INSTALL",
        f"{skill_md} is missing — the skill folder exists but has no SKILL.md.",
        3,
    )

text = skill_md.read_text(encoding="utf-8", errors="replace")
m = re.search(r"Version:\s+(\S+)", text)
if not m:
    report_outcome(
        "BROKEN INSTALL",
        "SKILL.md exists but does not contain a 'Version:' banner. "
        "This file is not a recognized mulesoft-raml-validator SKILL.md.",
        3,
    )

installed_version = m.group(1)
print(f"Installed version: {installed_version}")
print(f"Expected version:  {EXPECTED_VERSION}")

if installed_version != EXPECTED_VERSION:
    report_outcome(
        f"WRONG VERSION (installed v{installed_version}, expected v{EXPECTED_VERSION})",
        f"The SKILL.md banner reads v{installed_version}. The v{EXPECTED_VERSION} bundle "
        f"has not been deployed to this installation. Follow INSTALL.md "
        f"(in the bundle) to upgrade.",
        2,
    )
print(f"OK: version banner matches v{EXPECTED_VERSION}.")
# v1.5.0: inside the plugin repository, the manifest must carry the same version
manifest = SKILL_ROOT.parent.parent / ".claude-plugin" / "plugin.json"
if manifest.exists():
    plugin_version = json.loads(manifest.read_text(encoding="utf-8")).get("version")
    print(f"Plugin manifest version: {plugin_version}")
    if plugin_version != EXPECTED_VERSION:
        report_outcome(
            f"WRONG VERSION (plugin.json v{plugin_version}, expected v{EXPECTED_VERSION})",
            f"{manifest} declares v{plugin_version}; set it to {EXPECTED_VERSION}.", 2)
    print(f"OK: plugin.json matches v{EXPECTED_VERSION}.")

# -------------------------------------------------------------------------
# Step 3 — are all expected files present?
# -------------------------------------------------------------------------
banner("Step 3 — File inventory")
missing = []
present = []
for relpath in EXPECTED_FILES:
    p = SKILL_ROOT / relpath
    if p.exists():
        present.append(f"  OK:      {relpath} ({p.stat().st_size} bytes)")
    else:
        missing.append(f"  MISSING: {relpath}")

for line in present:
    print(line)
for line in missing:
    print(line)

if missing:
    report_outcome(
        f"PARTIAL INSTALL ({len(missing)} of {len(EXPECTED_FILES)} files missing)",
        f"The SKILL.md banner reads v{EXPECTED_VERSION} but {len(missing)} expected files "
        f"are missing. Re-deploy the full v{EXPECTED_VERSION} bundle.",
        3,
    )
print(f"\nOK: all {len(EXPECTED_FILES)} expected files present.")

# -------------------------------------------------------------------------
# Step 4 — does the analyzer actually run on the broken fixture?
# -------------------------------------------------------------------------
banner("Step 4 — Smoke test (broken fixture)")
broken_out = str(TMP / "verify-broken.json")
proc = subprocess.run(
    [PY, str(SKILL_ROOT / "scripts/audit_raml.py"),
     "--raml", str(SKILL_ROOT / "examples/customerOrderAPI.raml"),
     "--out", broken_out],
    capture_output=True, text=True,
)
print(f"  stdout: {proc.stdout.strip()}")
if proc.returncode != 0:
    print(f"  stderr: {proc.stderr.strip()}")
    report_outcome(
        "ANALYZER FAILED",
        f"audit_raml.py exited with code {proc.returncode} on the broken "
        f"fixture. The mechanics of the analyzer are broken; do not use "
        f"this install on real RAMLs.",
        1,
    )

data = json.loads(Path(broken_out).read_text())
got = {"score": data["score"], "verdict": data["verdict"],
       "findings": len(data["findings"])}
print(f"  expected: {EXPECTED_BROKEN}")
print(f"  got:      {got}")
if got != EXPECTED_BROKEN:
    report_outcome(
        "REGRESSION (broken fixture)",
        f"The broken fixture produced {got}, but the regression baseline "
        f"is {EXPECTED_BROKEN}. The analyzer's rule mechanics have drifted "
        f"from the committed snapshot. Inspect the diff before using.",
        1,
    )
print("OK: broken fixture matches baseline.")

# -------------------------------------------------------------------------
# Step 5 — does the analyzer correctly clear the clean fixture?
# -------------------------------------------------------------------------
banner("Step 5 — Smoke test (clean fixture)")
clean_out = str(TMP / "verify-clean.json")
proc = subprocess.run(
    [PY, str(SKILL_ROOT / "scripts/audit_raml.py"),
     "--raml", str(SKILL_ROOT / "examples/s-customer-orders-api.raml"),
     "--out", clean_out],
    capture_output=True, text=True,
)
print(f"  stdout: {proc.stdout.strip()}")
if proc.returncode != 0:
    print(f"  stderr: {proc.stderr.strip()}")
    report_outcome(
        "ANALYZER FAILED",
        f"audit_raml.py exited with code {proc.returncode} on the clean "
        f"fixture.",
        1,
    )

data = json.loads(Path(clean_out).read_text())
got = {"score": data["score"], "verdict": data["verdict"],
       "findings": len(data["findings"])}
print(f"  expected: {EXPECTED_CLEAN}")
print(f"  got:      {got}")
if got != EXPECTED_CLEAN:
    report_outcome(
        "REGRESSION (clean fixture)",
        f"The clean fixture produced {got}, but the regression baseline "
        f"is {EXPECTED_CLEAN}.",
        1,
    )
print("OK: clean fixture matches baseline.")

# -------------------------------------------------------------------------
# Step 6 — round-trip: refactor the broken fixture and re-audit (v1.4.0)
# -------------------------------------------------------------------------
banner("Step 6 — Round-trip test (refactor + re-audit)")
refactored_raml = str(TMP / "verify-refactored.raml")
transformations_json = str(TMP / "verify-transformations.json")
refactored_findings = str(TMP / "verify-refactored-findings.json")

proc = subprocess.run(
    [PY, str(SKILL_ROOT / "scripts/generate_best_practices.py"),
     "--raml", str(SKILL_ROOT / "examples/customerOrderAPI.raml"),
     "--findings", str(SKILL_ROOT / "examples/customerOrderAPI-findings.json"),
     "--out-raml", refactored_raml,
     "--out-transformations", transformations_json],
    capture_output=True, text=True,
)
print(f"  generator stdout: {proc.stdout.strip()}")
if proc.returncode != 0:
    print(f"  stderr: {proc.stderr.strip()}")
    report_outcome("GENERATOR FAILED",
                   f"generate_best_practices.py exited with code {proc.returncode}.", 1)

# Re-audit the refactor
proc = subprocess.run(
    [PY, str(SKILL_ROOT / "scripts/audit_raml.py"),
     "--raml", refactored_raml,
     "--out", refactored_findings],
    capture_output=True, text=True,
)
print(f"  re-audit stdout:  {proc.stdout.strip()}")
if proc.returncode != 0:
    report_outcome("RE-AUDIT FAILED", "audit on refactored RAML failed.", 1)

data = json.loads(Path(refactored_findings).read_text())
got = {"score": data["score"], "verdict": data["verdict"],
       "findings": len(data["findings"])}
print(f"  expected: {EXPECTED_REFACTORED}")
print(f"  got:      {got}")
if got != EXPECTED_REFACTORED:
    report_outcome(
        "ROUND-TRIP REGRESSION",
        f"Refactoring the broken fixture produced {got}, but the round-trip "
        f"contract is that the refactor must score {EXPECTED_REFACTORED}. "
        f"The generator is leaving findings unresolved.",
        1,
    )
print("OK: round-trip closed (refactor scores 100/100).")

# -------------------------------------------------------------------------
# Step 7 — reference demo API (v1.5.0): audit + round-trip
# -------------------------------------------------------------------------
banner("Step 7 — Reference demo (examples/demo/leave-management-api.raml)")
demo = SKILL_ROOT / "examples/demo/leave-management-api.raml"
# v1.5.0: the whole chain goes through the raml-validator command
demo_dir = TMP / "demo"
proc = subprocess.run([PY, str(SKILL_ROOT / "scripts/raml_validator.py"), "run", str(demo),
                       "--out-dir", str(demo_dir), "--no-color"],
                      capture_output=True, text=True)
print("  " + proc.stdout.strip().replace("\n", "\n  "))
if proc.returncode != 0:
    print(f"  stderr: {proc.stderr.strip()}")
    report_outcome("DEMO FAILED", f"raml-validator run exited with code {proc.returncode}.", 1)
demo_out = str(demo_dir / "leave-management-api-findings.json")
demo_bp_out = str(demo_dir / "leave-management-api-best-practices-findings.json")
for path, expected, label in ((demo_out, EXPECTED_DEMO, "demo audit"),
                              (demo_bp_out, EXPECTED_REFACTORED, "demo refactor")):
    data = json.loads(Path(path).read_text())
    got = {"score": data["score"], "verdict": data["verdict"], "findings": len(data["findings"])}
    print(f"  {label}: expected {expected}, got {got}")
    if got != expected:
        report_outcome("REGRESSION (reference demo)",
                       f"The {label} produced {got}, baseline is {expected}.", 1)
print("OK: reference demo matches baseline.")

# -------------------------------------------------------------------------
# All passes green
# -------------------------------------------------------------------------
report_outcome(
    f"v{EXPECTED_VERSION} FULLY DEPLOYED",
    f"All checks passed:\n"
    f"  - skill folder present at {SKILL_ROOT}\n"
    f"  - version banner: v{installed_version}\n"
    f"  - all {len(EXPECTED_FILES)} expected files present\n"
    f"  - broken fixture: {EXPECTED_BROKEN['findings']} findings, "
    f"score {EXPECTED_BROKEN['score']}, verdict {EXPECTED_BROKEN['verdict']}\n"
    f"  - clean fixture:  {EXPECTED_CLEAN['findings']} findings, "
    f"score {EXPECTED_CLEAN['score']}, verdict {EXPECTED_CLEAN['verdict']}\n"
    f"  - round-trip:     refactor of broken fixture scores "
    f"{EXPECTED_REFACTORED['score']}/100, verdict {EXPECTED_REFACTORED['verdict']}\n"
    f"  - reference demo: {EXPECTED_DEMO['findings']} findings, score "
    f"{EXPECTED_DEMO['score']} -> refactor 100/100 GO\n"
    f"\nThe skill is correctly deployed and ready to use on real RAMLs.",
    0,
)
