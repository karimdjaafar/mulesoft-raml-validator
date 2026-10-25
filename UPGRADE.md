# Upgrading mulesoft-raml-validator

| Document | Version | Date | Author | Status |
|---|---|---|---|---|
| UPGRADE — mulesoft-raml-validator | 1.5.0 | 2026-10-25 | Karim DJAAFAR — Jasmine Conseil | Released |

## From 1.4.x to 1.5.0

A **minor** release: the new `raml-validator` command (coloured output, zsh /
bash completion), English or French reports, same 23 rules and score formula.
The findings JSON gains an optional `api` block; files without it still render.
Replace the whole skill folder with the 1.5.0 folder, now
`skills/mulesoft-raml-validator/` in the repository, which is also a Claude plugin (see
[INSTALL.md](INSTALL.md)), then run `raml-validator verify`.

The scripts in `skills/mulesoft-raml-validator/scripts/` still work with their old arguments, but use the
command from now on: `raml-validator run my-api.raml` replaces the four calls.

What can change in your results:

| Change | Effect on an existing audit |
|---|---|
| One finding per rule | A rule hit in several places is now **one** finding listing every location. Scores can go **up** (e.g. two `NAMING-003` → one, +2 points). |
| `NAMING-004` checks the whole title | A prefixed title that is not kebab-case (`s-leave management-api`) is now a MAJOR finding (−5 points). |
| Singleton sub-resources | The generator no longer renames `/users/{userId}/password` to `/passwords`. |

Re-run the audit on specs you track if you compare scores over time.

## From 1.2.0 or 1.3.x

Replace the whole folder as above. 1.3.0 added the analyzer and the HTML
report, 1.4.0 the best-practices generator and the remediation guide: see
[CHANGELOG.md](CHANGELOG.md). Findings JSON produced since 1.2.0 still renders.

## Roll back

Install the previous release folder the same way. Reports already produced
stay readable: the findings JSON schema has not changed since 1.2.0.

---

## Historique du document

| Version | Date | Commentaire |
|---|---|---|
| 1.5.0 | 2026-10-25 | Rewritten for 1.5.0: patch upgrade path, effects on existing scores, older versions. |
| 1.3.0 | 2026-05 | First version (1.2.0 → 1.3.0). |

<p align="right"><span style="color:#E97132">© 2026 Jasmine Conseil</span></p>
