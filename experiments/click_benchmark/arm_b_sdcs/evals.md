# Positive Ground Truth (The Evals)
<!-- SPEC-001 Pillar 7 | Mutability: READ-ONLY -->

## Test Execution Invariant
All test runs must set `pythonpath=src` (or environment variable `PYTHONPATH=src`) to ensure tests execute against the repository source rather than system-installed packages.

## Test Baseline
- Command: `pytest -o pythonpath=src -q`
- Expected: ~2,022 passed in ~3.8 seconds.
- Regression Gate: Zero regression tolerance on existing passing tests.\n