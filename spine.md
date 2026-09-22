# Constitutional Invariants & Axioms (The Law)
<!-- SPEC-001 Pillar 1 | Mutability: READ-ONLY (Requires SDCS_ALLOW_CONSTITUTIONAL_MUTATION=1) -->

## Core Invariants

1. **Deterministic Grounding Over Speculative Assumptions:**
   - Every claim, verification status, and architectural decision must be grounded in physical filesystem state, AST verification, or executed test telemetry.
   - Verification gates must execute locally and deterministically. Never use LLM inference as a substitute for deterministic verification.

2. **Zero Heavy External Dependencies:**
   - The SDCS core package must remain ultra-lightweight. Standard library and PyYAML are the only permitted runtime dependencies.
   - External tools (compilers, linters, formatters) are invoked as optional child subprocesses, never bundled dependencies.

3. **Kinetic Rejection Before Contamination:**
   - Illegal imports, cartography drift, hollow tests, and cyclic thrashing must be physically rejected before disk staging.
   - Failure states must halt with non-zero exit codes (`exit 1`) to trigger agent self-correction.

4. **Backward Compatibility of CLI and Specifications:**
   - CLI subcommands (`sdcs verify`, `sdcs hydrate`, `sdcs doctor`, `sdcs audit`, `sdcs slice`, `sdcs repair`, `sdcs route`) must maintain stable interface contracts.
   - SPEC-001 specifications are versioned semantically; breaking changes require major version increments.
