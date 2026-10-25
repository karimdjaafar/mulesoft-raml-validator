#!/usr/bin/env python3
"""raml-validator — one command for the whole mulesoft-raml-validator chain.

Usage:
  raml-validator audit  SPEC.raml [--out-dir DIR] [--lang en|fr] [--api-description TEXT]
  raml-validator fix    SPEC.raml [--out-dir DIR] [--lang en|fr] [--api-description TEXT]
  raml-validator run    SPEC.raml [--out-dir DIR] [--lang en|fr] [--api-description TEXT]
  raml-validator verify [--root DIR]
  raml-validator completion zsh|bash|powershell
  raml-validator setup
  raml-validator --version

  audit   findings JSON + HTML audit report
  fix     best-practices RAML + transformations + remediation guide (MD, HTML),
          and a re-audit of the corrected RAML (audits first if needed)
  run     audit, then fix: every deliverable in one go
  verify  install check and regression suite
  setup   create the private Python environment (.venv) with PyYAML and
          Jinja2 — done automatically the first time a command needs it
  completion  print the shell completion script (zsh, bash or powershell), e.g.
              eval "$(raml-validator completion zsh)"
              raml-validator completion powershell | Out-String | Invoke-Expression

Output is coloured on a terminal; --no-color or the NO_COLOR variable turns
colours off (they are off anyway when the output is piped).

Files are written to --out-dir (default: the current folder), named after the
spec: <name>-findings.json, <name>-report.html, <name>-best-practices.raml,
<name>-transformations.json, <name>-remediation-guide.md/.html,
<name>-best-practices-findings.json. With --lang fr the reports end in .fr.html
/ .fr.md. English is the default language.

Exit codes: 0 done (whatever the verdict) · 1 a step failed · 2 PyYAML or Jinja2
could not be installed · 3 file not found;
`verify` returns the verifier's own codes (0-4, see INSTALL.md).
The individual scripts in scripts/ remain available.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from version import SKILL_VERSION  # single source of the version

PY = sys.executable or "python3"
ROOT = HERE.parent

_COLOR = False
_CODES = {"bold": "1", "dim": "2", "red": "31", "green": "32", "orange": "38;5;208", "blue": "34"}


def c(text: str, *styles: str) -> str:
    """Colour text for a terminal (ANSI); plain when colours are off."""
    if not _COLOR or not styles:
        return text
    return "\033[" + ";".join(_CODES[s] for s in styles) + "m" + text + "\033[0m"


def _has(module: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module) is not None


WINDOWS = os.name == "nt"
VENV = ROOT / ".venv"
VENV_PY = VENV / ("Scripts/python.exe" if WINDOWS else "bin/python")
DEPS = ["pyyaml", "jinja2"]


def _deps_ok(python: str) -> bool:
    return subprocess.run([python, "-c", "import yaml, jinja2"],
                          capture_output=True).returncode == 0


def _candidates() -> list[str]:
    """Pythons to try for .venv, the usual one first, then older ones."""
    names = [os.environ.get("RAML_VALIDATOR_PYTHON", ""), sys.executable or "",
             "python3", "python", "python3.13", "python3.12", "python3.11", "python3.10", "python3.9"]
    seen, out = set(), []
    for n in names:
        path = (n if os.path.isabs(n) and os.path.exists(n) else shutil.which(n)) if n else None
        if path and os.path.realpath(path) not in seen:
            ok = subprocess.run([path, "-c", "import sys; sys.exit(sys.version_info < (3, 9))"],
                                capture_output=True).returncode == 0
            if ok:
                seen.add(os.path.realpath(path))
                out.append(path)
    return out


def setup() -> bool:
    """Create .venv with PyYAML and Jinja2, trying each Python until one works."""
    if VENV_PY.exists() and _deps_ok(str(VENV_PY)):
        print(c("✔ ", "green") + f"Python environment ready: {VENV}")
        return True
    for py in _candidates():
        print(c("▶ ", "orange") + f"Creating {VENV.name} with {py} and installing PyYAML, Jinja2…")
        shutil.rmtree(VENV, ignore_errors=True)
        made = subprocess.run([py, "-m", "venv", str(VENV)], capture_output=True)
        if made.returncode != 0 or not VENV_PY.exists():
            print(c("  ✘ ", "red") + "could not create the environment with this Python, trying another one")
            continue
        inst = subprocess.run([str(VENV_PY), "-m", "pip", "install", "--quiet",
                               "--disable-pip-version-check", *DEPS],
                              capture_output=True, text=True)
        if inst.returncode == 0 and _deps_ok(str(VENV_PY)):
            print(c("✔ ", "green") + f"Python environment ready: {VENV}")
            return True
        last = (inst.stderr or inst.stdout).strip().splitlines()[-1:] or [""]
        print(c("  ✘ ", "red") + "install failed with this Python (" + last[0][:120] + "), trying another one")
    shutil.rmtree(VENV, ignore_errors=True)
    print("ERROR: could not install PyYAML and Jinja2 with any Python 3.9+ found.\n"
          "Check the network access. On Debian / Ubuntu, install the venv module first:\n"
          "  sudo apt install python3-venv\n"
          "then run: raml-validator setup",
          file=sys.stderr)
    return False


def _title(text: str) -> None:
    print(c("▶ " + text, "bold", "orange"))


def _verdict(path: str) -> str:
    d = json.loads(Path(path).read_text())
    ok = d["verdict"] == "GO"
    return (c(f"{d['verdict']}", "bold", "green" if ok else "red")
            + f" — score {d['score']}/100, {len(d['findings'])} findings")


def _step(script: str, *args: str) -> None:
    proc = subprocess.run([PY, str(HERE / script), *args])
    if proc.returncode != 0:
        sys.exit(1)


def _paths(spec: Path, out_dir: Path, lang: str) -> dict:
    n = spec.stem
    sfx = "" if lang == "en" else ".fr"
    o = lambda name: str(out_dir / name)
    return {
        "findings": o(f"{n}-findings.json"),
        "report": o(f"{n}-report{sfx}.html"),
        "bp_raml": o(f"{n}-best-practices.raml"),
        "transformations": o(f"{n}-transformations.json"),
        "guide_md": o(f"{n}-remediation-guide{sfx}.md"),
        "guide_html": o(f"{n}-remediation-guide{sfx}.html"),
        "bp_findings": o(f"{n}-best-practices-findings.json"),
    }


def _opts(args) -> list[str]:
    extra = ["--lang", args.lang]
    if args.api_description:
        extra += ["--api-description", args.api_description]
    return extra


def do_audit(args, p) -> None:
    _title(f"Audit — {args.spec.name}")
    _step("audit_raml.py", "--raml", str(args.spec), "--out", p["findings"])
    _step("render_report.py", "--findings", p["findings"], "--out", p["report"], *_opts(args))


def do_fix(args, p) -> None:
    _title(f"Best-practices refactor — {args.spec.name}")
    if not Path(p["findings"]).exists():
        _step("audit_raml.py", "--raml", str(args.spec), "--out", p["findings"])
    _step("generate_best_practices.py", "--raml", str(args.spec), "--findings", p["findings"],
          "--out-raml", p["bp_raml"], "--out-transformations", p["transformations"])
    _step("render_remediation_guide.py", "--transformations", p["transformations"],
          "--findings", p["findings"], "--out-md", p["guide_md"], "--out-html", p["guide_html"],
          *_opts(args))
    _step("audit_raml.py", "--raml", p["bp_raml"], "--out", p["bp_findings"])


def main() -> int:
    # Line-buffered output keeps our messages in order with the scripts' output,
    # and nothing is lost when os.execv() restarts the command in .venv.
    sys.stdout.reconfigure(line_buffering=True, errors="replace")
    sys.stderr.reconfigure(errors="replace")
    # The scripts read and write UTF-8 files (French templates, RAML); UTF-8
    # mode makes that the default for them on every OS, Windows included.
    os.environ["PYTHONUTF8"] = "1"
    ap = argparse.ArgumentParser(prog="raml-validator", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=SKILL_VERSION)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, helptext in (("audit", "audit a RAML spec"),
                           ("fix", "generate the best-practices RAML and the remediation guide"),
                           ("run", "audit then fix: every deliverable")):
        sp = sub.add_parser(name, help=helptext)
        sp.add_argument("spec", type=Path, help="RAML 1.0 file")
        sp.add_argument("--out-dir", type=Path, default=Path("."), help="output folder (default: .)")
        sp.add_argument("--lang", choices=["en", "fr"], default="en", help="report language (default: en)")
        sp.add_argument("--api-description", default=None,
                        help="description of the API to show in the reports (e.g. a translation)")
        sp.add_argument("--no-color", action="store_true", help="plain output, no colours")
    vp = sub.add_parser("verify", help="install check and regression suite")
    vp.add_argument("--root", default=None, help="skill folder to check")
    sub.add_parser("setup", help="create .venv with PyYAML and Jinja2 (automatic on first use)")
    cp = sub.add_parser("completion", help="print the shell completion script")
    cp.add_argument("shell", choices=["zsh", "bash", "powershell"])
    args = ap.parse_args()

    if args.cmd == "completion":
        name = {"zsh": "_raml-validator", "bash": "raml-validator.bash",
                "powershell": "raml-validator.ps1"}[args.shell]
        sys.stdout.write((ROOT / "completions" / name).read_text(encoding="utf-8"))
        return 0

    global _COLOR
    _COLOR = (sys.stdout.isatty() and "NO_COLOR" not in os.environ
              and not getattr(args, "no_color", False))
    if _COLOR and WINDOWS:
        os.system("")   # turns on ANSI colours in the Windows console

    if args.cmd == "setup":
        return 0 if setup() else 2

    # First run, or a Python without PyYAML / Jinja2: install them into .venv
    # once, then run the same command again with that Python.
    if args.cmd in ("audit", "fix", "run", "verify") and not (_has("yaml") and _has("jinja2")):
        if not (VENV_PY.exists() and _deps_ok(str(VENV_PY))):
            print(c("PyYAML and Jinja2 are missing for " + PY + " — one-time setup.", "bold"))
            if not setup():
                return 2
        sys.stdout.flush(); sys.stderr.flush()
        again = [str(VENV_PY), str(Path(__file__).resolve()), *sys.argv[1:]]
        if WINDOWS:   # os.execv does not replace the process on Windows
            return subprocess.run(again).returncode
        os.execv(again[0], again)

    if args.cmd == "verify":   # keep the verifier's own exit codes (0-4)
        return subprocess.run([PY, str(HERE / "verify_install.py"),
                               *(["--root", args.root] if args.root else [])]).returncode

    if not args.spec.exists():
        print(f"ERROR: file not found: {args.spec}", file=sys.stderr)
        return 3
    if not args.spec.is_file():
        print(f"ERROR: not a file: {args.spec} — give the path of a .raml file, "
              f"e.g. {args.spec.as_posix().rstrip('/')}/<name>.raml", file=sys.stderr)
        return 3
    args.out_dir.mkdir(parents=True, exist_ok=True)
    p = _paths(args.spec, args.out_dir, args.lang)
    if args.cmd in ("audit", "run"):
        do_audit(args, p)
    if args.cmd in ("fix", "run"):
        do_fix(args, p)
    print()
    print(c("Result", "bold"))
    if Path(p["findings"]).exists():
        print("  Audit       " + _verdict(p["findings"]))
    if args.cmd in ("fix", "run"):
        print("  After fix   " + _verdict(p["bp_findings"]))
    print(c("  Files in    ", "dim") + str(args.out_dir.resolve()))
    for key in ("report", "bp_raml", "guide_html", "guide_md"):
        if Path(p[key]).exists():
            print(c("    • ", "orange") + Path(p[key]).name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
