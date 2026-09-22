# Spec-Driven Cognitive Scaffolding (SDCS) Wiki

Welcome to the official developer and architecture wiki for **Spec-Driven Cognitive Scaffolding (SDCS / SPEC-001 v1.8.0)**.

SDCS is an open-source, file-based cognitive harness and closed-loop cybernetic control system designed to eliminate context drift, cartographic hallucinations, and episodic amnesia in autonomous coding agents (Claude Code, Cursor, Codex, Gemini CLI).

```bash
pip install sdcs
```

---

## 🏢 The Furnished Office Metaphor
> **The Bot** is the *Brain* without arms.  
> **The Harness** is the Brain's *arms & hands*.  
> **Skills** are the *tools held in the hands*.  
> **SDCS** is the **Furnished Office** (the constitutional rules, floor plan, central whiteboard, rejection graveyard, kinetic bouncer, and central warehouse).

---

## Quick Navigation

* 🎮 **[Living Office HUD (`sdcs watch`)](CLI-Command-Reference#1-living-office-hud-sdcs-watch)**: 16-bit isometric pixel-art HUD streaming repository telemetry in real time.
* 🏛️ **[Architecture & Cybernetic Ontology](Architecture-&-Cybernetic-Ontology)**: The 4-layer control theory foundation and the 4-phase execution engine.
* 📜 **[The 7 Cognitive Pillars](The-7-Cognitive-Pillars)**: Detailed file reference for `spine.md`, `wiring.yaml`, `roadmap.md`, `state.md`, `app_map.md`, `decisions.md`, `evals.md`, and the `sessions/` flight recorder.
* 🛡️ **[Kinetic Enforcement Gates](Kinetic-Enforcement-Gates)**: The 8 automated kinetic gates (Gates C, T, P, M, S, W, Q, E) and the Circuit Breaker physically blocking architectural erosion and file thrashing.
* 🔄 **[Lossless Compaction Protocol](Lossless-Compaction-Protocol)**: The 5-step checklist eliminating Compaction Amnesia during long pair-programming shifts.
* 📋 **[Agent Runbooks & SOPs](Agent-Runbooks-&-SOPs)**: Standard operating procedures for boot sequence, in-stride wiring, and baseline fixture recalibration.
* 💻 **[CLI Command Reference](CLI-Command-Reference)**: Complete options and workflows for `sdcs init`, `sdcs watch`, `sdcs doctor`, `sdcs hydrate`, `sdcs verify`, `sdcs map`, `sdcs eval`, `sdcs state`, `sdcs warehouse`, `sdcs decay`, `sdcs session`, `sdcs graph`, and `sdcs grill`.
* 📖 **[Ontology Lexicon & Glossary](Ontology-Lexicon-&-Glossary)**: Formal terminology dictionary (Phantom Corpus, Inverted ADR, Teleological Anchor, etc.).

---

## 🎙️ Multimedia Overviews & Presentations

Prefer listening or watching? Explore the architectural foundations and field lessons:
* 🎬 **Executive Video Presentation:** [▶️ Watch on YouTube](https://youtu.be/Ap0bXGM0MbU) — *Spec-Driven Cognitive Scaffolding: The Architecture of Deterministic AI*
* 🎧 **Audio Deep-Dive Podcast:** [🎧 Listen to the Podcast (M4A)](https://github.com/adamm285-dev/Spec-Driven-Cognitive-Scaffolding-SDCS/releases/download/v1.4.1/Breaking_the_Turn_15_Wall_with_SDCS.m4a) — *Breaking the Turn 15 Wall with SDCS*
* 📊 **Slide Deck (PDF):** [📄 Download 12-Slide High-Resolution Deck (v1.4.1)](https://github.com/adamm285-dev/Spec-Driven-Cognitive-Scaffolding-SDCS/blob/main/media/v141slides/Deterministic_AI_Engineering.pdf)

---

## Why SDCS Exists: The Crisis of Monolithic Prompting

Autonomous coding agents typically fail not because of raw model capability, but because of **context conflation**. When system rules, scratchpad notes, file paths, and execution history are dumped into a single prompt window, three fatal pathologies emerge:

1. **Context Drift:** Core constraints get pushed out of effective attention as conversational history expands.
2. **Cartographic Hallucination:** Agents waste hundreds of tokens running recursive `find` and `grep` loops, inventing non-existent files or duplicating utilities.
3. **Episodic Amnesia:** Lacking negative memory, agents repeatedly retry architectures and hypotheses that were already measured and rejected in prior sessions.

SDCS externalizes cognition into **seven repository-controlled files** enforced by **eight physical kinetic gates** and a **circuit breaker** on disk, guaranteeing deterministic autonomous engineering.
