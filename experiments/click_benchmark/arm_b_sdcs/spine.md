# Constitutional Invariants (The Spine)
<!-- SPEC-001 Pillar 1 | Mutability: IMMUTABLE -->

This document declares the non-negotiable architectural axioms governing `pallets/click`.

## Axiom 1: Zero External Dependencies
`click` is a foundational CLI framework. It must never depend on non-standard-library packages at runtime. All terminal formatting, option parsing, and ANSI manipulations are implemented internally.

## Axiom 2: Strict Context Lifecycle & Resource Cleanup
- A command invocation executes within a hierarchical `Context` tree.
- Context resources registered via `call_on_close` and `with_resource` must always be closed/cleaned up deterministically on exit or abort.
- Standalone mode handles exceptions and converts them into user-facing output with deterministic exit codes; non-standalone mode allows exceptions to propagate to callers.

## Axiom 3: Cross-Platform File & Terminal Safety
- Windows console and POSIX terminal abstractions in `click._termui_impl` must isolate OS differences.
- Any temporary file opened for paging or editor operations must ensure handles are properly closed before filesystem mutations or unlinking, avoiding platform-specific handle locks.
- Stream operations must handle binary and text encodings gracefully without unintended byte-string type collisions.

## Axiom 4: Singleton Immutability & Identity
- Internal sentinel representations used to indicate unset arguments, missing options, or default overrides must preserve identity under standard copy, deepcopy, and serialization operations.

## Axiom 5: Public API Stability
- Public classes (`Command`, `Group`, `Context`, `Parameter`, `Option`, `Argument`, `ParamType`) must preserve signature backwards compatibility.
- Help formatting must produce deterministic, readable output across all supported terminal dimensions.\n