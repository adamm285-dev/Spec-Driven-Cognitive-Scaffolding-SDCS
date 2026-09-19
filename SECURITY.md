# Security Policy

This policy outlines how to report vulnerabilities in SDCS reference tooling, clarifies the security boundaries of the framework, and provides practical guidelines for running autonomous coding agents safely.

---

## 1. Supported Versions

| Version | Supported |
| --- | --- |
| `1.3.x` | Yes |
| `1.2.x` | Yes |
| `< 1.2.0` | No (Upgrade to v1.2.0+ for invariant git hook protections) |

---

## 2. Reporting a Vulnerability

If you discover a security flaw, bypass, or bug in the reference CLI scripts (`sdcs_init.py`, `audit_evals_corpus.py`) or the pre-commit hook harness:

* **Do not open a public issue.**
* Open a **Private Security Advisory** via GitHub (under repository **Security** > **Advisories** > **Report a vulnerability**), or email `security@adammurphy.dev`.
* Include reproduction steps, your environment details (OS, Python version), and a minimal test case demonstrating the failure.
* We aim to acknowledge reports within 48 hours and provide patches within 7 business days.

---

## 3. The SDCS Security Model

SDCS is an architectural harness that organizes context and establishes structured checkpoints for AI coding agents. It is important to understand where prompt-level guidance ends and operating-system security begins:

* **Prompt vs. Process:** Markdown files like `spine.md` and `wiring.yaml` instruct the agent on operational rules. However, an LLM agent with unrestricted filesystem access can technically edit any file it has permission to touch.
* **Defense in Depth:** SDCS pairs prompt instructions with physical checkpoints—specifically Git pre-commit hooks (`Gate C`) and file-level permissions—to prevent an agent from silently relaxing validation rules or modifying constitutional invariants to force a task to pass.
* **Auditability:** Shift handoffs (`sessions/*.md`) and SHA-256 fixture audits (`evals.md`) create a clear, traceable record of what changes were made, why they were made, and which tests were executed.

---

## 4. Best Practices for Running Autonomous Agents

When giving an agent shell access, code execution privileges, or automated git commit capabilities, follow standard engineering safeguards:

### Enforce Physical File Permissions

Do not rely purely on the agent choosing to follow instructions. Lock foundational configuration files so the agent cannot overwrite them during an automated run:

```bash
# Set constitutional invariants to read-only
chmod 444 spine.md wiring.yaml
```

### Enable Repository Pre-Commit Hooks

Activate the built-in SDCS pre-commit hooks to block commits that tamper with invariants or introduce large code diffs without updating working memory:

```bash
# Direct git to use SDCS hooks
git config core.hooksPath .githooks

# Set enforcement mode (advisory or strict)
git config sdcs.mode strict
```

### Run in Ephemeral, Sandboxed Environments

* Run autonomous agent shifts inside isolated containers (e.g., Docker, Dev Containers, or temporary virtual machines) rather than directly on your primary host system.
* Restrict the agent process to non-root privileges with limited access to sensitive host directories.

### Practice Strict Secret Hygiene

* Never store API keys, tokens, or credentials in markdown memory files (`state.md`, `sessions/`, etc.).
* Exclude `.env` files from version control using `.gitignore`.
* Inject secrets dynamically into the runtime environment via environment variables rather than persisting them to disk.
