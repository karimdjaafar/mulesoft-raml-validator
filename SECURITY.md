# Security Policy

## Reporting a vulnerability

The `mulesoft-raml-validator` team takes security issues seriously. We
appreciate your efforts to responsibly disclose your findings, and we will
make every effort to acknowledge your contribution.

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, report them privately via one of the following channels:

- **Email:** [security@jasmineconseil.com](mailto:security@jasmineconseil.com)
- **GitHub Security Advisories:** use the
  [private reporting feature](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability)
  on this repository.

---

## What to include in your report

To help us triage and fix the issue quickly, please include as much of the
following as possible:

1. **A clear description** of the issue, including the type of vulnerability
   (e.g., arbitrary file read via path traversal in `audit_raml.py`,
   YAML deserialization issue, prompt injection through a crafted RAML, etc.).
2. **Steps to reproduce**, ideally with a minimal RAML or input that triggers
   the issue.
3. **The impact** you believe the vulnerability has — what an attacker could
   achieve, and under what conditions.
4. **The version(s) affected** (check `SKILL.md` frontmatter and
   `CHANGELOG.md`).
5. **Your environment**: Python version, OS, Claude product (claude.ai /
   Claude Code / API), and PyYAML version.
6. **Proposed remediation**, if you have one.

Reports written in either English or French are equally welcome.

---

## What we consider in scope

The following are within the scope of this security policy:

- **Code execution** vulnerabilities in `scripts/audit_raml.py` or
  `scripts/render_report.py` (e.g., arbitrary code execution via crafted YAML,
  command injection via filenames).
- **Path traversal** allowing reads or writes outside the user-specified
  paths.
- **Denial-of-service** through resource exhaustion (e.g., billion-laughs
  attack via YAML anchors, runaway regex).
- **HTML/script injection** in the rendered HTML report when audit findings
  contain attacker-controlled content from the RAML.
- **Information disclosure** (e.g., the renderer leaking environment variables
  or system paths into the report).
- **Prompt injection** in the skill manifest (`SKILL.md`) or templates that
  could cause Claude to deviate from the documented audit posture in a way
  that endangers users.

---

## What we consider out of scope

- The RAML being audited is **untrusted input by design**. The skill is
  meant to point out problems in untrusted RAML — that's its whole job.
  Findings about insecure RAML (e.g., "this RAML has SEC-001!") are *audit
  results*, not security vulnerabilities.
- Issues in **third-party dependencies** (PyYAML, the Python standard
  library, Claude itself). Please report those upstream. We will track and
  bump dependencies when upstream fixes ship.
- **Social engineering** of Jasmine Conseil staff or community contributors.
- **Physical attacks** against contributor hardware.
- **The Enterprise Edition** is governed by a separate security policy and
  support agreement. Enterprise customers should contact their account
  manager directly.

---

## Our commitments

When you report a vulnerability in good faith, we commit to:

- **Acknowledge** receipt of your report within **5 business days**.
- **Provide an initial assessment** of the report within **15 business days**,
  including whether we consider it in scope and a preliminary severity
  rating.
- **Keep you informed** of the progress toward a fix.
- **Credit you** in the release notes and in this `SECURITY.md` (in a future
  "Acknowledgments" section), unless you prefer to remain anonymous.
- **Coordinate disclosure** — we will not publish details of the
  vulnerability until a fix is available, and we will give you reasonable
  notice before doing so.

We do **not** currently offer a paid bug bounty program. We do offer the
gratitude of the maintainers and the community, public acknowledgment, and
swag where logistically possible.

---

## Severity classification

We use the following internal severity ratings, loosely aligned with CVSS:

| Severity | Description | Target fix time |
|---|---|---|
| **Critical** | Remote code execution, unauthenticated data exfiltration | 7 days |
| **High** | Authenticated RCE, sandbox escape, significant DoS | 30 days |
| **Medium** | Information disclosure, limited DoS, prompt injection | 60 days |
| **Low** | Cosmetic issues with security impact, hardening opportunities | 90 days |

Critical and High severity issues will trigger a patch release on a dedicated
branch. Medium and Low severity issues will be bundled into the next
scheduled release.

---

## Supported versions

Only the **latest minor release** of the Community Edition receives security
fixes. As of this writing, that is:

| Version | Supported |
|---|:---:|
| 1.2.x | ✅ |
| 1.1.x | ❌ — please upgrade |
| 1.0.x | ❌ — please upgrade |
| < 1.0 | ❌ — pre-release |

If you are pinned to an older version for a legitimate reason, please reach
out at [security@jasmineconseil.com](mailto:security@jasmineconseil.com) and
we'll discuss extended support options.

---

## Safe-harbor statement

We will not pursue or support legal action against researchers who:

- Make a good-faith effort to comply with this policy;
- Avoid privacy violations, destruction of data, and disruption of service;
- Use only the channels described above to disclose vulnerabilities;
- Give us reasonable time to investigate and fix the issue before any public
  disclosure.

This safe harbor applies only to actions taken in accordance with this
policy. Any activity outside the scope of this policy, such as accessing
production systems of Jasmine Conseil or its clients, is strictly prohibited
and may result in legal action.

---

## Security updates

Security advisories will be published as
[GitHub Security Advisories](https://github.com/karim-djaafar/mulesoft-raml-validator/security/advisories)
on this repository. To stay informed:

- **Watch** the repository on GitHub (Watch → Custom → Security alerts).
- Subscribe to the [`CHANGELOG.md`](./CHANGELOG.md) — security fixes are
  always called out in release notes.
- Follow [@JasmineConseil](https://twitter.com/JasmineConseil) for major
  announcements.

---

## Acknowledgments

We are grateful to the following researchers for their responsible
disclosures (in chronological order):

*No vulnerabilities have been reported and resolved at this time. You could
be the first — see "Reporting a vulnerability" above.*

---

## Contact

- **Security issues:** [security@jasmineconseil.com](mailto:security@jasmineconseil.com)
- **General inquiries:** [contact@jasmineconseil.com](mailto:contact@jasmineconseil.com)
- **Enterprise support:** through your Jasmine Conseil account manager

Last updated: 2026-05-04
