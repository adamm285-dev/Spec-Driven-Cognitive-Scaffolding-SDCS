## Description
<!-- Provide a concise summary of the changes and the problem solved. -->

---

## SDCS Cognitive Harness Checklist

Before merging, confirm compliance across the SDCS pillars:

- [ ] **`spine.md` (Constitutional Invariants):** No axioms violated or weakened.
- [ ] **`roadmap.md` (Acceptance Contract):** Changes align with `[INTENT]` without inventing proxy metrics; no ephemeral task queues added.
- [ ] **`app_map.md` (Cartography):** Updated if new files/modules were introduced, renamed, or deleted.
- [ ] **`decisions.md` (Negative Memory):** Recorded any measured rejections or intentional trade-offs (`Claim → Metric → Reopen`).
- [ ] **`evals.md` (Standing & Ground Truth):** 
  - [ ] New fixtures registered with SHA-256 hash.
  - [ ] Ran `python audit_evals_corpus.py` (0 collisions / 0 phantom fixtures).
- [ ] **`state.md` (Working Memory):** Reset or cleaned of local developer scratch tasks.
- [ ] **Verification Gates:**
  - [ ] `pytest -v` (all tests pass).
  - [ ] Linter & formatter clean.
