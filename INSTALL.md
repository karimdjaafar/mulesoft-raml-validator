# Installing mulesoft-raml-validator

| Document | Version | Date | Author | Status |
|---|---|---|---|---|
| INSTALL — mulesoft-raml-validator | 1.4.2 | 2026-10-25 | Karim DJAAFAR — Jasmine Conseil | Released |

The skill is one folder. Install it wherever your Claude client loads skills,
then run the verifier. Nothing in the skill depends on where the folder sits.

---

## 1. Install

### Claude (claude.ai, desktop app, Cowork)

1. Zip the `mulesoft-raml-validator` folder (the folder itself, with `SKILL.md`
   at its top level).
2. In Claude, open **Customize → Skills** and upload the zip.
3. Turn the skill on and open a **new** conversation.

On Team and Enterprise plans, an Owner can also make the skill available to the
whole organization.

### Claude Code

Copy or clone the folder into your personal skills folder:

```bash
git clone https://github.com/karimdjaafar/mulesoft-raml-validator.git \
  ~/.claude/skills/mulesoft-raml-validator
```

Use `.claude/skills/` inside a project instead to share it with that project.
Start a new Claude Code session so the skill is loaded.

### Scripts only, without Claude

Clone the repository anywhere and install the two dependencies:

```bash
pip install pyyaml jinja2
```

## 2. Verify

From the skill folder:

```bash
python3 scripts/verify_install.py
```

Or from anywhere: `python3 scripts/verify_install.py --root /path/to/mulesoft-raml-validator`.
In Claude, ask: *"Run the install check of the mulesoft-raml-validator skill."*

The verifier runs 7 steps and ends with one verdict:

| Step | Check | Expected |
|---|---|---|
| 1 | Skill folder present | — |
| 2 | `SKILL.md` version banner | same as `scripts/version.py` |
| 3 | File inventory | all expected files present |
| 4 | Broken fixture `customerOrderAPI.raml` | 17 findings, 21/100, NO-GO |
| 5 | Clean fixture `s-customer-orders-api.raml` | 0 findings, 100/100, GO |
| 6 | Refactor of the broken fixture, re-audited | 100/100, GO |
| 7 | Reference demo `examples/demo/leave-management-api.raml`, audit then refactor | 16 findings, 26/100 NO-GO → 100/100 GO |

A healthy install prints `VERDICT — v1.4.2 FULLY DEPLOYED` and exits with 0.

| Exit code | Meaning | What to do |
|---|---|---|
| 0 | Fully deployed | Use the skill. |
| 1 | A script failed or a result drifted from its baseline | Do not use it on real RAMLs; report it (section 4). |
| 2 | Another version is installed | Install this version again. |
| 3 | Files are missing | Install the complete folder again. |
| 4 | Folder not found | Check the path, or pass `--root`. |

## 3. Upgrade or roll back

See [UPGRADE.md](UPGRADE.md). Rolling back means installing the previous
release folder the same way.

## 4. Report a problem

Open an issue with: the full output of `verify_install.py`, the first ten lines
of `SKILL.md` (version banner), and the Python version (`python3 --version`).
Security issues: see [SECURITY.md](SECURITY.md).

---

## Historique du document

| Version | Date | Commentaire |
|---|---|---|
| 1.4.2 | 2026-10-25 | Rewritten: install paths for Claude, Claude Code and scripts only; path-agnostic verifier with 7 steps; exit codes. |
| 1.3.0 | 2026-05 | First version (deployment to `/mnt/skills/user/`). |

<p align="right"><span style="color:#E97132">© 2026 Jasmine Conseil</span></p>
