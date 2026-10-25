![RAML Validator logo](../assets/logo.png)

# Developer guide — mulesoft-raml-validator

| Document | Version | Date | Author | Status |
|---|---|---|---|---|
| Developer guide — mulesoft-raml-validator | 1.5.0 | 2026-10-25 | Karim DJAAFAR — Jasmine Conseil | Released |

For people who change the skill: add or fix a rule, extend the generator, change
a report, or cut a release. To *use* the skill, read the [README](../README.md).

---

## 1. Architecture

**Layout.** The repository is a Claude plugin: `.claude-plugin/plugin.json` at
the root and the skill in `skills/mulesoft-raml-validator/`, which carries the
command launchers in its own `bin/`. There is deliberately **no `bin/` at the
repository root**: the directory refuses to list a plugin with a top-level
`bin/` in Cowork and the Claude apps. **Paths in this guide are
relative to the skill folder** unless they start with the repository root
(`docs/`, `.claude-plugin/`, `.github/`).

Everything goes through **one command, `raml-validator`** (`bin/raml-validator`
→ `scripts/raml_validator.py`). It chains four scripts joined by two JSON
files; Claude runs it and adds a semantic review. The scripts stay callable on
their own for debugging, but nobody has to chain them by hand.

```
raml-validator run spec.raml --out-dir DIR [--lang fr] [--api-description "…"]

spec.raml ──audit_raml.py──▶ findings.json ──render_report.py──▶ report.html
    │                             │
    └──── generate_best_practices.py ──▶ spec-best-practices.raml + transformations.json
                                                       │
                       render_remediation_guide.py ◀───┘──▶ guide.md + guide.html
```

| File | Role |
|---|---|
| `SKILL.md` | What Claude reads: the 23 rules (§2), output contract (§3), workflow (§5), anti-patterns (§6). The rule catalog's source of truth. |
| `bin/raml-validator` | Shell launcher (macOS, Linux). Python used, in order: `$RAML_VALIDATOR_PYTHON`, the repository's `.venv/bin/python`, `python3`. Put `bin/` on the `PATH`. |
| `.venv/` | Private Python environment with PyYAML and Jinja2, created by `raml-validator setup` or on first use; ignored by git. |
| `scripts/raml_validator.py` | The command: `audit`, `fix`, `run`, `verify`, `setup`, `completion zsh\|bash\|powershell`, `--version`; options `--out-dir`, `--lang`, `--api-description`, `--no-color`. Names outputs after the spec, prints a coloured summary. Calls the scripts below with `subprocess`; it never reimplements them. |
| `bin/raml-validator.cmd` | Windows launcher (cmd, PowerShell): `%RAML_VALIDATOR_PYTHON%`, `.venv\Scripts\python.exe`, then `python` or `py`. |
| `completions/_raml-validator`, `completions/raml-validator.bash`, `completions/raml-validator.ps1` | Tab completion for zsh, bash and PowerShell, printed by `raml-validator completion …`. |
| `.github/workflows/acceptance.yml` | Acceptance tests on Ubuntu, macOS and Windows, Python 3.9 / 3.12 / 3.13, on every push. |
| `scripts/version.py` | The only place the version is written. Every script imports it. |
| `scripts/audit_raml.py` | Parses RAML with PyYAML, runs the checks, scores, writes `findings.json`. |
| `scripts/render_report.py` | `findings.json` → HTML report (`templates/report.html.j2`): API under audit, findings matrix, detailed findings, links to the project, this guide and feedback. `--lang fr` for French. |
| `scripts/generate_best_practices.py` | Applies one fix per finding, writes the refactored RAML and `transformations.json`. |
| `scripts/render_remediation_guide.py` | `transformations.json` (+ findings) → guide in Markdown and HTML, with the description of the audited API. `--lang fr` for French. |
| `scripts/i18n_fr.py` | French texts for `--lang fr`. |
| `scripts/verify_install.py` | Install check and regression suite (7 steps). |
| `templates/` | Jinja2 templates for the HTML outputs, Markdown report skeleton. |
| `references/raml-best-practices.md` | One-page rule cheat sheet. |
| `examples/` | Regression fixtures and the reference demo (`examples/demo/`). |

Dependencies: Python 3.9+, `PyYAML`, `Jinja2`. No network access, no other
package.

## 2. Data contracts

### `findings.json` (written by `audit_raml.py`)

```json
{
  "title": "RAML Audit Report — Leave Management API",
  "subtitle": "MuleSoft RAML 1.0 production-readiness audit",
  "spec_path": "leave-management-api.raml",
  "date": "2026-10-25",
  "skill_version": "mulesoft-raml-validator v1.5.0",
  "score": 21,
  "verdict": "NO-GO",
  "findings": [
    {
      "rule": "NAMING-003",
      "severity": "MINOR",
      "location": "GET /leaveRequests?page_size; GET /employee/{employeeId}/balance?page_size",
      "summary": "2 occurrences — Query parameter 'page_size' is not camelCase.",
      "impact": "…",
      "remediation_code": "queryParameters:\n  pageSize:\n    type: string"
    }
  ],
  "api": {
    "title": "Leave Management API", "version": "v1.0.3",
    "base_uri": "https://api.demo.jasmineconseil.com/leaves",
    "media_type": "application/json", "layer": "unknown",
    "description": "Employee leave management. Employees submit leave requests …",
    "resources": 6, "operations": 6, "methods": {"GET": 3, "POST": 2, "PUT": 1},
    "operation_list": [{"method": "GET", "path": "/leaveRequests", "description": "List leave requests."}],
    "security_schemes": [], "types": ["LeaveRequest"], "traits": []
  }
}
```

- **One entry per rule** (`aggregate_by_rule`): locations are joined with `; `,
  and the summary is prefixed with `N occurrences —`.
- `severity` is one of `BLOCKER`, `MAJOR`, `MINOR`, `INFO`.
- A finding carries `remediation_code` or `remediation_text`.
- **Score**: `100 − 15·BLOCKER − 5·MAJOR − 2·MINOR`, floor 0 (`PENALTY` in
  `audit_raml.py`). **Verdict** `GO` only if score ≥ 80 and no BLOCKER.
- `api` (added in 1.5.0, built by `api_profile`) describes the API under audit
  exactly as declared in the spec; the report shows it in the *API under audit*
  section. Only the layer is derived (from the title prefix, `unknown` without
  one). Findings files without `api` still render, without that section.
- Adding an optional field is backward compatible; removing or renaming a field
  is a **major** version.

### `transformations.json` (written by `generate_best_practices.py`)

Top level: `title`, `source_raml`, `refactored_raml`, `date`, `skill_version`,
`inferred_layer`, `layer_reasoning`, `transformations`, `transformation_count`,
`transformation_kinds`. Each transformation:

```json
{ "rule": "NAMING-001", "kind": "mechanical", "before": "/leaveRequests",
  "after": "/leave-requests", "reasoning": "…", "confidence": "high" }
```

| `kind` | Meaning | Flagged for review in the guide |
|---|---|---|
| `mechanical` | Deterministic, safe (rename, format) | no |
| `heuristic` | Sensible default to check (placeholder example, generated description, inferred layer) | yes |
| `architectural` | A design choice with several valid answers | yes |

## 3. Add or change a rule

1. **Define it in `SKILL.md` §2**: ID in its category (`NAMING-005`…),
   severity, one-sentence rule. Add the row to `references/raml-best-practices.md`.
2. **Detect it** in the matching `check_*` function of `audit_raml.py`
   (`check_naming`, `check_apic`, `check_reuse`, `check_spec`,
   `check_security`, `check_versioning`, `check_documentation`, listed in
   `CHECKS`). Append a dict with the fields of § 2. Emit one finding per place:
   aggregation is done for you.
3. **Fix it** (if it can be fixed) with a `fix_<rule>_<what>(spec, findings,
   transformations)` function in `generate_best_practices.py`. Start with
   `if not has_finding(findings, "<RULE>"): return`, change `spec` in place,
   and record each change with `make_transformation(...)`. Call it from the
   ordered list in `main()`: renames come first, examples and endpoint security last.
4. **The round-trip must close**: the refactored RAML must re-audit with **no
   finding of that rule**. If it cannot be fixed automatically, say so in the
   remediation guide (kind `architectural`) rather than leaving it silent.
5. **Prove it**: add or extend a fixture that triggers the rule, and check the
   test turns red without your change and green with it (§ 5).
6. **French**: add the rule to `RULES_FR` (and `REMEDIATION_FR` /
   `REASONING_FR` if it has a remediation text or a generator fix) in
   `scripts/i18n_fr.py`.
7. **Version**: new rule = minor; fix of a false positive = patch; changed
   severity or removed rule = major (see *Versioning policy* in the CHANGELOG).

Traps already met:

- A rule hit in several places used to be penalised several times → keep
  aggregation in `main()`.
- A RAML key can hold several segments (`/users/{userId}/password`): judge the
  **last** segment, and treat a segment under a URI parameter as a singleton.
- `LAYER_PREFIX_RE` only tests the prefix; use `TITLE_RE` when the whole title
  must be valid.
- `!include` targets are not read: a trait included from a file is trusted.

## 4. Change a report

- HTML report: `templates/report.html.j2`; guide: `templates/remediation-guide.html.j2`
  and `remediation-guide.md.j2`. The renderers load them from `templates/`
  next to the scripts unless `--template-dir` is given.
- **Jasmine Conseil charter**: header band with the project name and logo,
  orange `#E97132` and dark blue `#0E2841` (CSS variables `--header-blue` and
  `--footer-navy` at the top of each template), Calibri, footer
  © 2026 Jasmine Conseil. Severity colours (`--sev-*`) stay semantic.
- The logo is embedded as a PNG data URI so the page stays one self-contained
  file; the source image is the logo shown at the top of the README.
- Deliverables stay in **English** (§3bis of `SKILL.md`).

## 5. Languages — bilingual generation (EN / FR)

The reports are generated in **one target language per run: English by default,
French on request**. The option is given on the command line, at generation
time:

```bash
raml-validator run my-api.raml --out-dir reports/              # English (default)
raml-validator run my-api.raml --out-dir reports/ --lang fr    # French: audit report and guide
raml-validator run my-api.raml --lang fr --api-description "Description traduite…"
```

The command passes `--lang` (and `--api-description`) to both renderers,
`render_report.py` and `render_remediation_guide.py`, which accept the same
options when called directly.

| Rule | Detail |
|---|---|
| Values | `--lang en` (default) or `--lang fr`; any other value is refused by the command line. |
| One language per run | The audit report and the remediation (generation) report of a run are always produced in the **same** language (§3bis of `SKILL.md`). In Claude, asking for "rapport en français" sets `fr` for both. |
| What is translated | Titles, labels, category and severity names, finding summaries and impacts, remediation texts, transformation reasonings, layer explanation, next steps. |
| API description | Taken from the spec and kept as written by default. Translating it is optional, at the user's choice: pass the translation with `--api-description "…"` to both renderers; the report marks it "(description traduite)". The RAML is not changed. The reference demo uses the translated variant. |
| What is not | Rule IDs, RAML paths, YAML snippets, the refactored RAML, and the JSON files (`findings.json`, `transformations.json` stay in English: the language is chosen when rendering only). |
| Default unchanged | English output is byte-identical whether or not French support is present. |

Where the French lives:

- Templates: `templates/report.fr.html.j2`, `templates/remediation-guide.fr.html.j2`,
  `templates/remediation-guide.fr.md.j2`. **A change to an English template must
  be made in its French twin too.**
- Texts: `scripts/i18n_fr.py` — `CATEGORIES_FR`, `RULES_FR` (summary and impact
  per rule), `REMEDIATION_FR`, `REASONING_FR` (keyed by the English reasoning of
  the generator), `KIND_LABEL_FR`, `CONFIDENCE_LABEL_FR`, layer explanations, and
  `BEFORE_AFTER_FR` (patterns for the generator's before / after summaries such
  as "6 resources without description"; code-like values stay as they are).
  **A new rule or a new generator reasoning needs its French entry**; a missing
  one falls back to English rather than being guessed.

Check after any change: render the demo in both languages (commands in
`examples/README.md`), read the visible French text, and confirm the English
outputs are byte-identical to the committed ones.

## 6. Command line: colours and completion

- **Colours** (`c()` in `raml_validator.py`): ANSI codes, only when the output
  is a terminal, `NO_COLOR` is unset and `--no-color` is not given. Keep every
  message readable without colour; never colour a file the command writes.
- **Completion**: `completions/_raml-validator` (zsh, `#compdef`, `_arguments`),
  `completions/raml-validator.bash` (`complete -F`) and
  `completions/raml-validator.ps1` (`Register-ArgumentCompleter -Native`).
  **A new subcommand or option must be added to the three files and to the
  command's help.** Check them with `zsh -n` / `bash -n`, by pressing Tab in
  each shell, and in PowerShell with `TabExpansion2`.
- **Windows**: `.venv\Scripts\python.exe` instead of `.venv/bin/python`; the
  command restarts in `.venv` with `subprocess` (no `os.execv`); colours are
  turned on with `os.system("")`; the scripts run in Python UTF-8 mode
  (`PYTHONUTF8=1`) so French templates and RAML files read the same on every
  OS. Keep paths built with `pathlib`, never with `/` in strings.
- **Exit codes**: 0 done, 1 a step failed, 2 PyYAML or Jinja2 missing (with
  the install command in the message), 3 file not found; `verify` returns the
  verifier's codes 0-4.
- **Python environment**: `setup()` creates `.venv` and installs PyYAML and
  Jinja2, trying `$RAML_VALIDATOR_PYTHON`, `python3`, then `python3.13` …
  `python3.9` until one works. `audit`, `fix`, `run` and `verify` call it on
  first use, then restart themselves in `.venv` with `os.execv` (output is
  line-buffered so no message is lost). `raml-validator setup` runs it on demand.

## 7. Test

```bash
raml-validator verify
```

Must end with `FULLY DEPLOYED` and exit code `0`. The 7 steps: folder,
version banner, file inventory, broken fixture (17 findings, 21/100, NO-GO),
clean fixture (0, 100/100, GO), round-trip on the broken fixture (100/100),
reference demo through `raml-validator run` (16 findings, 26/100 → 100/100).

Compare a full snapshot after a change:

```bash
raml-validator audit examples/customerOrderAPI.raml --out-dir /tmp --no-color
diff <(jq -S 'del(.date,.skill_version,.spec_path)' examples/customerOrderAPI-findings.json) \
     <(jq -S 'del(.date,.skill_version,.spec_path)' /tmp/customerOrderAPI-findings.json)
```

No diff means no regression. A diff you intended means: regenerate the
snapshot (commands in `examples/README.md`), read the diff line by line, and
explain it in the CHANGELOG.

Before release, also run the whole chain on the demo (commands in
`examples/README.md`) and open both HTML files.

## 8. Release

1. Set the new version in `scripts/version.py`, in the `SKILL.md` banner
   (`Version:` / `Released:`) and in `.claude-plugin/plugin.json`;
   `verify_install.py` checks that the three match.
2. Add the CHANGELOG entry and write `RELEASE-NOTES-x.y.z.md`; update the
   version badge and the *Historique du document* tables you touched.
3. Regenerate `examples/demo/` in both languages (commands in
   `examples/README.md`) and run `raml-validator verify`.
4. Check that the `acceptance` workflow is green on the three OSes, run the
   **[acceptance tests](ACCEPTANCE-TESTS.md)** on a real machine from a clean
   state, and record the run in its table.
5. Commit, tag `vx.y.z`, push; create the GitHub release from the release notes.
6. Re-upload the skill folder to Claude (see [INSTALL.md](../INSTALL.md)).

## 9. Known limitations

- `REUSE-002` (duplicated error schemas) and `SPEC-004` (inline schemas over 20
  lines) are left to Claude's review.
- Two report languages only: English and French.
- Layer inference looks at top-level resources only.
- RAML 0.8 and OpenAPI are not supported; `!include` files are not followed.
- Pluralisation is a simple suffix rule (`person` → `persons`).

---

## Historique du document

| Version | Date | Commentaire |
|---|---|---|
| 1.5.0 | 2026-10-25 | First developer guide: architecture, data contracts (incl. the `api` block), adding a rule, reports and charter, bilingual generation (`--lang en` / `fr`), the `raml-validator` command with colours and completion, tests, release, limitations. |

Contact: Karim DJAAFAR — [kdjaafar@jasmineconseil.com](mailto:kdjaafar@jasmineconseil.com)

<p align="right"><span style="color:#E97132">© 2026 Jasmine Conseil</span></p>
