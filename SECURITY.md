# Security Policy & Responsible Engineering Guidelines

This document outlines the security architecture, threat model, vulnerability reporting procedures, and dual-use considerations for the Spec-Driven Cognitive Scaffolding (SDCS) framework and reference tooling (`SPEC-001`).

---

## 1. Vulnerability Reporting & Disclosure

We take the security and integrity of SDCS and its host environments seriously. If you discover a vulnerability or security flaw within the SDCS reference tooling (`sdcs_init.py`, `audit_evals_corpus.py`, or the pre-commit hook harness), report it responsibly.

### 1.1 Reporting Process

* **Email:** Send details to `security@adammurphy.dev` (or open a private GitHub Security Advisory).
* **Information to Include:**
  * Component affected (e.g., pre-commit hook bypass, normalizer hash evasion, path traversal in cartography generation).
  * Proof of Concept (PoC) script or reproduction steps demonstrating the invariant failure.
  * Environmental details (OS, Python version, Git version, execution permissions).
* **Response Timeline:**
  * **Initial Acknowledgment:** Within 48 hours.
  * **Triage & Status Assessment:** Within 7 business days.
  * **Patch Release & Advisory:** Coordinated public release once a fix is verified.

Please do not open public GitHub issues for unpatched arbitrary execution flaws or security bypasses.

---

## 2. Framework Threat Model & Security Boundaries

SDCS is an architectural harness designed to govern the cognitive loop and repository interactions of autonomous Large Language Model (LLM) agents. Understanding the boundary between **prompt-level scaffolding** and **OS-level isolation** is critical.

| Domain | In-Scope (Enforced by SDCS) | Out-of-Scope (Host Responsibility) |
| :--- | :--- | :--- |
| **Invariant Tampering** | Rejection of uncommitted/staged diffs to `spine.md` via pre-commit Gate C. | Malicious kernel-level file overrides or root processes running with `--no-verify`. |
| **Context Integrity** | Prevention of context drift, cartographic hallucination, and phantom test reporting. | Underlying model parametric alignment, jailbreaks, or model weights manipulation. |
| **Auditability** | Append-only execution records (`sessions/*.md`) and SHA-256 fixture diversity. | Network egress monitoring or external packet inspection. |
| **Blast Radius** | Explicit component mapping and tool whitelist declarations (`wiring.yaml`). | Process sandbox escapes or hypervisor security. |

---

## 3. Dual-Use Analysis & Risk Mitigation

SDCS introduces a structured methodology for long-running, multi-turn autonomous software engineering. As with any technology that increases autonomous problem-solving capabilities, SDCS carries potential dual-use implications.

### 3.1 Dual-Use Capability Surface

* **Systematic Negative Exploration (`decisions.md`):** The same mechanism that prevents an agent from repeating a failed database migration could theoretically be leveraged by an adversary to methodically iterate against defensive security controls, recording failed evasion techniques until a bypass is discovered.
* **Autonomous State Persistence (`state.md` + `wiring.yaml`):** Bounding context drift allows models to execute complex, multi-stage engineering workflows across distributed architectures—a capability that could be targeted toward mapping complex attack surfaces or chaining multi-step exploits.

### 3.2 The Defense-Dominant Nature of SDCS

Despite potential dual-use applications, SDCS is fundamentally an **asymmetric defensive technology**:

1. **Defenders Face Combinatorial Asymmetry:** Offensive operations generally succeed by finding a single unpatched flaw; defensive engineering requires verifying and securing every execution path across thousands of files. Monolithic, drift-prone agents fail catastrophically on large codebases. SDCS provides defenders with the determinism required to maintain, refactor, and verify large-scale secure architectures.
2. **Mandatory Auditing vs. Stealth:** SDCS explicitly penalizes opaque operations. By enforcing strict pre-commit hooks, discrete flight recorder handoffs (`sessions/`), and cryptographic integrity audits (`evals.md`), the framework leaves an auditable, immutable paper trail of every mutation and test result.
3. **Formal Invariant Precedence:** The architecture centers around `spine.md` (Constitutional Invariants) and `evals.md` (Deterministic Ground Truth). It is engineered specifically to subject generative output to formal, deterministic verification gates.

---

## 4. Responsible Use Guidelines

By using SDCS, you agree to adhere to ethical engineering practices:

* **No Autonomous Exploitation:** SDCS MUST NOT be used to orchestrate autonomous vulnerability hunting against systems or networks without explicit, written authorization from the system owner.
* **No Signature / Evasion Engineering:** The rejection schema (`decisions.md`) MUST NOT be deployed to automatically fuzz and evade defensive intrusion detection systems (IDS), web application firewalls (WAF), or endpoint detection agents (EDR).
* **No Phantom Metric Inflation:** Teams implementing SPEC-001 MUST NOT modify normalizers to bypass corpus diversity checks or falsify baseline standing.

---

## 5. Deployment Hardening & Operational Recommendations

To run autonomous agents safely using SDCS in production or continuous development loops:

### 5.1 Enforce Physical File Read-Only Attributes

Do not rely exclusively on prompt instructions to protect constitutional files. Enforce OS-level read-only permissions for agent execution users:

```bash
# Render foundational invariants read-only to non-root processes
chmod 444 spine.md wiring.yaml
```

### 5.2 Mandatory Git Hook Activation

Ensure all developer workstations and CI runners actively use the repository git hooks:

```bash
# Direct git to execute SDCS verification hooks
git config core.hooksPath .githooks

# Set enforcement to blocking mode
git config sdcs.mode strict
```

### 5.3 Execution Sandboxing

When granting an agent tool-execution capabilities (`pytest`, `bash`, `python`):

* Execute the agent inside an ephemeral, non-privileged container (e.g., Docker with `--cap-drop=ALL` or a gVisor sandbox).
* Restrict outbound network egress to verified package registries and APIs required by `wiring.yaml`.
* Mount repository secrets into read-only environment variables rather than persisting them on disk.
