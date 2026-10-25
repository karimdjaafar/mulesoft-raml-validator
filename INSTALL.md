# Installing mulesoft-raml-validator

| Document | Version | Date | Author | Status |
|---|---|---|---|---|
| INSTALL — mulesoft-raml-validator | 1.5.0 | 2026-10-25 | Karim DJAAFAR — Jasmine Conseil | Released |

The skill is one folder. Install it wherever your Claude client loads skills,
then run the verifier. Nothing in the skill depends on where the folder sits.

---

## 0. Prerequisites

| Need | Detail |
|---|---|
| Operating system | **macOS, Linux or Windows** — zsh, bash or PowerShell. |
| Python | **3.9 or later**, reachable as `python3` (macOS, Linux) or `python` / `py` (Windows). Homebrew and recent Linux Pythons are fine, even though they refuse `pip install` outside a private environment. |
| PyYAML, Jinja2 | **Installed for you.** The first command that needs them creates a private environment `.venv` in the repository (ignored by git) and installs them there; `raml-validator setup` does it on demand. If the usual Python cannot install them (too recent, no `venv` module), the command tries `python3.13` … `python3.9` in turn. |
| Debian / Ubuntu | The `python3-venv` package: `sudo apt install python3-venv` (the distribution's Python ships without the `venv` module). |
| Network | Needed once, for that first install (Python Package Index). |
| Claude | For use inside Claude: code execution enabled (claude.ai, desktop app, Cowork, Claude Code). |

### Qualified platforms (v1.5.0)

A platform is **qualified** when the [acceptance tests](docs/ACCEPTANCE-TESTS.md)
pass on it; other versions are expected to work but are not guaranteed.

| Platform | Shell | Python | Status |
|---|---|---|---|
| macOS 26 Tahoe | zsh | Homebrew `python3` (3.15) | ✅ qualified — manual run, steps 1–5 (6–8 covered by the runners) |
| macOS 15 (GitHub runner) | bash, zsh | 3.9, 3.12, 3.13 | ✅ qualified — `acceptance` run #1 (commit e705b0e) |
| Ubuntu 24.04 LTS | bash 5.2 | 3.12 (distribution) | ✅ qualified — 8/8 (manual run) |
| Ubuntu 24.04 (GitHub runner) | bash | 3.9, 3.12, 3.13 | ✅ qualified — `acceptance` run #1 (commit e705b0e) |
| Windows Server 2022 (GitHub runner) | PowerShell 7 | 3.9, 3.12, 3.13 | ✅ qualified — `acceptance` run #1 (commit e705b0e); no manual run yet |

The `acceptance` workflow (`.github/workflows/acceptance.yml`) runs the
automated part of the acceptance tests on every push. Its result is the
reference for the GitHub-runner rows.

---

## 1. Install

### From the Claude plugin directory

Once listed, search **RAML Validator by Jasmine Conseil** (`jasmine-raml-validator`)
in the directory and add it. It works in Claude chat, Cowork and Claude Code.

### Claude (claude.ai, desktop app, Cowork), skill only

1. Zip the `skills/mulesoft-raml-validator` folder (the folder itself, with
   `SKILL.md` at its top level).
2. In Claude, open **Customize → Skills** and upload the zip.
3. Turn the skill on and open a **new** conversation.

On Team and Enterprise plans, an Owner can also make the skill available to the
whole organization.

### Windows (PowerShell)

```powershell
git clone https://github.com/karimdjaafar/mulesoft-raml-validator.git $HOME\tools\mulesoft-raml-validator
& $HOME\tools\mulesoft-raml-validator\skills\mulesoft-raml-validator\bin\raml-validator.cmd setup
[Environment]::SetEnvironmentVariable("Path", "$HOME\tools\mulesoft-raml-validator\skills\mulesoft-raml-validator\bin;" + [Environment]::GetEnvironmentVariable("Path", "User"), "User")
Add-Content $PROFILE 'raml-validator completion powershell | Out-String | Invoke-Expression'
```

Open a new PowerShell window, then `raml-validator --version` must print
`mulesoft-raml-validator v1.5.0`; Tab completes commands, options and `.raml`
files. `bin\raml-validator.cmd` also works from `cmd.exe` (without completion).

### Claude Code

Load the whole plugin from a clone of the repository:

```bash
git clone https://github.com/karimdjaafar/mulesoft-raml-validator.git ~/tools/mulesoft-raml-validator
claude --plugin-dir ~/tools/mulesoft-raml-validator
```

Or copy only the skill into your personal skills folder:
`cp -R ~/tools/mulesoft-raml-validator/skills/mulesoft-raml-validator ~/.claude/skills/`.

Use `.claude/skills/` inside a project instead to share it with that project.
Start a new Claude Code session so the skill is loaded.

### Command line (macOS, Linux), without Claude

Clone the repository, prepare its Python environment, put the skill's `bin/` folder on your
`PATH` and turn on tab completion. For **zsh** (default shell on macOS):

```bash
git clone https://github.com/karimdjaafar/mulesoft-raml-validator.git ~/tools/mulesoft-raml-validator
~/tools/mulesoft-raml-validator/skills/mulesoft-raml-validator/bin/raml-validator setup
echo 'export PATH="$HOME/tools/mulesoft-raml-validator/skills/mulesoft-raml-validator/bin:$PATH"' >> ~/.zshrc
echo 'autoload -Uz compinit && compinit' >> ~/.zshrc
echo 'eval "$(raml-validator completion zsh)"' >> ~/.zshrc
source ~/.zshrc
raml-validator --version
```

For **bash** (most Linux distributions), use `~/.bashrc` and
`eval "$(raml-validator completion bash)"`; skip the `compinit` line.

The last command must print `mulesoft-raml-validator v1.5.0`.
`setup` prints `✔ Python environment ready` (skipping it is fine: the first
`audit`, `fix`, `run` or `verify` does it). `bin/raml-validator` then uses the
repository's `.venv` automatically; set `RAML_VALIDATOR_PYTHON` to choose
another Python. If no Python can install the packages, the command says why and
exits with code 2. Then type
`raml-validator ` and press Tab: the commands are listed. Colours are on in a
terminal and off with `--no-color` or `NO_COLOR=1`.

## 2. Verify

```bash
raml-validator verify
```

Or for another copy: `raml-validator verify --root /path/to/mulesoft-raml-validator`.
In Claude, ask: *"Run the install check of the mulesoft-raml-validator skill."*

The verifier runs 7 steps and ends with one verdict:

| Step | Check | Expected |
|---|---|---|
| 1 | Skill folder present | — |
| 2 | `SKILL.md` version banner (and `.claude-plugin/plugin.json` in the repository) | same as `scripts/version.py` |
| 3 | File inventory | all expected files present |
| 4 | Broken fixture `customerOrderAPI.raml` | 17 findings, 21/100, NO-GO |
| 5 | Clean fixture `s-customer-orders-api.raml` | 0 findings, 100/100, GO |
| 6 | Refactor of the broken fixture, re-audited | 100/100, GO |
| 7 | Reference demo `examples/demo/leave-management-api.raml` through `raml-validator run` | 16 findings, 26/100 NO-GO → 100/100 GO |

A healthy install prints `VERDICT — v1.5.0 FULLY DEPLOYED` and exits with 0.

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

Open an issue with: the full output of `raml-validator verify`, the first ten lines
of `SKILL.md` (version banner), and the Python version (`python3 --version`).
Security issues: see [SECURITY.md](SECURITY.md).

---

## Historique du document

| Version | Date | Commentaire |
|---|---|---|
| 1.5.0 | 2026-10-25 | Rewritten: install paths for Claude, Claude Code and scripts only; path-agnostic verifier with 7 steps; exit codes. |
| 1.3.0 | 2026-05 | First version (deployment to `/mnt/skills/user/`). |

<p align="right"><span style="color:#E97132">© 2026 Jasmine Conseil</span></p>
