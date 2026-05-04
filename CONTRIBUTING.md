# Contributing to mulesoft-raml-validator

Thank you for your interest in contributing! This skill is maintained as an
open-core project by [Jasmine Conseil](https://www.jasmineconseil.com), and
community contributions are welcome.

---

## How to contribute

### Reporting bugs or false positives

Open a GitHub issue with the `bug` label. Please include:

- The **RAML snippet** that triggers the bug (minimal reproducer, ≤ 30 lines).
- The **expected behavior** (which rule should or should not fire, and why).
- The **actual behavior** (what the audit produced).
- Your environment: Python version, OS, Claude product (claude.ai / Claude Code / API).

False positives (a rule fires when it shouldn't) are particularly valuable —
the credibility of the audit depends on its accuracy.

### Proposing new audit rules

Open a GitHub issue with the `rule-proposal` label. A good proposal includes:

1. **Rule ID** following the existing namespacing (`NAMING-005`, `SEC-004`, etc.).
2. **Severity** (BLOCKER / MAJOR / MINOR / INFO) with justification.
3. **Category** (one of the 7 existing categories, or a proposal for a new one).
4. **Bad example** — a RAML snippet that violates the rule.
5. **Good example** — the same snippet remediated.
6. **Business impact** — why does this matter in production?

Rules are reviewed against the same bar as the existing 23: every rule must be
**unambiguous**, **automatable**, and **actionable** (i.e., have a clear fix).

### Submitting pull requests

1. Fork the repo and create a feature branch (`git checkout -b feature/my-rule`).
2. Make your changes. For new rules, update **all** of:
   - `SKILL.md` §2 (the rule definition)
   - `references/raml-best-practices.md` (the cheat sheet)
   - `scripts/audit_raml.py` (the detection logic, if automatable)
   - `examples/` (a fixture demonstrating the rule)
   - `CHANGELOG.md` (under `[Unreleased]`)
3. Run the existing audit on `examples/bad-customer-orders.raml` and verify
   the score and findings haven't regressed unexpectedly.
4. Open a pull request with a clear description and a link to the issue.

---

## Development setup

```bash
git clone https://github.com/karim-djaafar/mulesoft-raml-validator.git
cd mulesoft-raml-validator
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install pyyaml
```

Run the audit on the sample RAML to verify your setup:

```bash
python scripts/audit_raml.py --raml examples/bad-customer-orders.raml --out findings.json
python scripts/render_report.py --findings findings.json --out report.md --format markdown
```

You should get a score around 19/100 with 18 findings.

---

## Code style

- **Python**: PEP 8, 4-space indentation, type hints where reasonable, docstrings
  on public functions.
- **YAML / RAML in examples**: 2-space indentation, kebab-case resources,
  camelCase query parameters (i.e., the rules the skill itself enforces).
- **Markdown**: prefer prose over deep bullet hierarchies. ATX headings (`##`),
  fenced code blocks with language hints.
- Keep PRs focused — one rule or one bug fix per PR.

---

## Contributor License Agreement

By submitting a contribution, you agree that your contribution is licensed
under the same Apache License 2.0 as the project, and you certify that you
have the right to submit it (per the [Developer Certificate of Origin](https://developercertificate.org/)).

There is no separate CLA to sign. The DCO is implicit in the act of opening
a PR — by doing so, you assert authorship and right-to-license of your code.

---

## Code of conduct

Be respectful. Assume good faith. Disagree with ideas, not with people.
Off-topic, derogatory, or harassing comments will be removed and the author
may be blocked from the repo.

---

## Out of scope

The following are intentionally **not** in scope for community contributions:

- **Sector-specific rules** (banking, telecom, healthcare). These belong to
  the Enterprise Edition and are maintained separately.
- **Branded report templates**. The Community Edition uses neutral styling
  by design.
- **Anypoint Exchange / API Manager integrations**. Enterprise feature.
- **CI/CD plugins** (Maven, Gradle, GitHub Actions). Enterprise feature.

If you have a use case that touches these, please reach out at
[contact@jasmineconseil.com](mailto:contact@jasmineconseil.com) — there may
be a path via the Enterprise Edition or a partnership.

---

## Questions?

- General questions: open a GitHub Discussion.
- Sensitive or commercial questions: [contact@jasmineconseil.com](mailto:contact@jasmineconseil.com).
- Security issues: see [SECURITY.md](SECURITY.md) (or email
  [security@jasmineconseil.com](mailto:security@jasmineconseil.com)).

Thank you for helping make MuleSoft RAML specs better, one audit at a time.
