# Release notes — mulesoft-raml-validator 1.5.0

| Document | Version | Date | Author | Status |
|---|---|---|---|---|
| Release notes — mulesoft-raml-validator | 1.5.0 | 2026-10-25 | Karim DJAAFAR — Jasmine Conseil | Released |

**Minor release** — a real command line, reports in English or French, a
reference demo; same 23 rules and score formula; the findings JSON gains one
optional `api` block (backward compatible). Recommended for every user of
1.4.x. Detailed list of changes: [CHANGELOG.md](CHANGELOG.md#150--2026-10-25).

---

## Highlights

- **A Claude plugin.** The repository is now the plugin `jasmine-raml-validator`
  ("RAML Validator by Jasmine Conseil"), ready for Anthropic's plugin directory;
  the skill lives in `skills/mulesoft-raml-validator/`.
- **One command: `raml-validator`.** `run`, `audit`, `fix`, `verify`,
  `completion`, `--version` — no more chaining Python scripts by hand. Coloured
  output (verdict in green or red), tab completion for zsh and bash, standard
  setup on macOS and Linux:

  ```bash
  raml-validator run my-api.raml --out-dir reports/ --lang fr
  ```

  Nothing to install by hand: PyYAML and Jinja2 go into a private `.venv`
  on first use. Works on **macOS, Linux and Windows** (zsh, bash, PowerShell
  completion); every push is tested on the three OSes (GitHub Actions).
- **The repository is back in step with the released skill.** It had stayed at
  1.2.0 while 1.3.0 → 1.4.1 shipped to Claude users. The analyzer, the HTML
  report, the best-practices generator, the remediation guide and their
  examples are now all on GitHub.
- **A reference demo you can read before running anything.**
  [`examples/demo/`](skills/mulesoft-raml-validator/examples/demo/) audits a realistic *Leave Management API*
  and keeps every deliverable, in English and French: **26/100 NO-GO** before,
  **100/100 GO** after the generated refactor, with 15 traced transformations
  (6 flagged for human review).
- **More accurate scores.** One finding per rule, listing every location: a
  rule hit in two places no longer costs twice.

## Fixes

| Area | Before | Now |
|---|---|---|
| Score | A rule hit in N places was penalised N times | One finding per rule, every location listed |
| `NAMING-004` | `s-leave management-api` passed | The whole title must be kebab-case; the generator fixes it |
| Generator | `/users/{userId}/password` became `/passwords` | Singleton sub-resources stay singular |
| Install check | `verify_install.py` looked in one fixed folder and reported "NOT INSTALLED" on correct installs | Checks the folder it ships in, or `--root PATH`; 7 steps including the demo |
| Rule count | Docs said 22 or 23 | 23 rules: 21 checked by the analyzer, `REUSE-002` and `SPEC-004` by Claude's review |

## New

- **Reports in English or French.** English by default; ask for French and
  both the audit report and the remediation guide are produced in French
  (`--lang fr`), including the description of the API (`--api-description`).
  Rule IDs, RAML and JSON are unchanged.
- **The audit report and the remediation guide describe the API under audit** first: title,
  version, layer, description, base URI, operations with their descriptions,
  security, types and traits — as declared in the spec.
- **Developer guide**: [`docs/DEVELOPER-GUIDE.md`](docs/DEVELOPER-GUIDE.md).
- Report footer links to the project, the developer guide, feedback and contact.
- `scripts/version.py` — one place for the version, read by every script.
- **HTML report and remediation guide in the Jasmine Conseil charter**: header
  band with the project name and logo, orange `#E97132` / dark blue `#0E2841` palette, Calibri, © 2026 Jasmine
  Conseil footer. Severity colours are unchanged.
- README, INSTALL, UPGRADE and CONTRIBUTING rewritten for this release.
- **Follow the project and give feedback**: Watch → Releases on GitHub, issue
  templates (bug, false positive, rule proposal), maintainer contact
  kdjaafar@jasmineconseil.com.

## Impact on existing audits

Scores can change when you re-audit a spec:

- **Up** — repeated hits of the same rule now count once (e.g. two `NAMING-003` → one, +2).
- **Down** — a prefixed title that is not kebab-case is now a MAJOR finding (−5).

Re-run the audit on the specs you track over time. See [UPGRADE.md](UPGRADE.md).

## Removed

- `examples/bad-customer-orders.raml` and `examples/sample-report.md` (1.2.0
  samples, superseded by `examples/customerOrderAPI.raml` and `examples/demo/`).

## Known limitation

Layer inference only looks at top-level resources: the demo's nested `/approve`
action does not make the generator choose the Process layer (`p-`). The
remediation guide flags the title choice for review.

## Upgrade

Replace the skill folder with this release ([INSTALL.md](INSTALL.md)), then run:

```bash
raml-validator verify
```

Expected: `VERDICT — v1.5.0 FULLY DEPLOYED`, exit code 0.

---

## Historique du document

| Version | Date | Commentaire |
|---|---|---|
| 1.5.0 | 2026-10-25 | First release notes for 1.5.0. |

<p align="right"><span style="color:#E97132">© 2026 Jasmine Conseil</span></p>
