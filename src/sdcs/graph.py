"""
sdcs.graph - Declarative Topology Graph Visualizer (SPEC-001 v1.4.0 Pillar 2)
"""

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def locate_wiring_file(repo_root: Path, custom_path: str | Path | None = None) -> Path | None:
    """Locates wiring.yaml in root, .agent/, or custom path."""
    if custom_path:
        p = Path(custom_path)
        if not p.is_absolute():
            p = repo_root / p
        return p if p.is_file() else None

    candidates = [
        repo_root / "wiring.yaml",
        repo_root / ".agent" / "wiring.yaml",
        repo_root / "wiring.yml",
        repo_root / ".agent" / "wiring.yml",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def parse_wiring(wiring_file: Path) -> dict[str, Any]:
    """Parses wiring.yaml using pyyaml or fallback parser."""
    content = wiring_file.read_text(encoding="utf-8", errors="ignore")
    if yaml is not None:
        data = yaml.safe_load(content) or {}
    else:
        # Minimalist fallback parser if pyyaml is missing
        data = {"subsystems": {}}
        current_sub = None
        for line in content.splitlines():
            trimmed = line.strip()
            if trimmed.startswith("subsystems:"):
                continue
            if line.startswith("  ") and not line.startswith("    ") and trimmed.endswith(":"):
                current_sub = trimmed[:-1].strip()
                data["subsystems"][current_sub] = {"allowed_dependencies": []}
            elif current_sub and "allowed_dependencies:" in trimmed:
                pass
            elif current_sub and trimmed.startswith("- "):
                dep = trimmed[2:].strip().strip("\"'")
                data["subsystems"][current_sub].setdefault("allowed_dependencies", []).append(dep)
    return data


def generate_mermaid_graph(subsystems: dict[str, Any]) -> str:
    """Generates a Mermaid flowchart TD diagram string representing subsystem contracts."""
    lines = [
        "```mermaid",
        "flowchart TD",
        "  %% SDCS Declarative Subsystem Topology (SPEC-001 v1.4.0 Pillar 2)",
    ]

    # Declare nodes
    for name, spec in sorted(subsystems.items()):
        path = spec.get("path", "")
        if path:
            lines.append(f'  {name}["{name}<br/><code>{path}</code>"]')
        else:
            lines.append(f'  {name}["{name}"]')

    lines.append("")

    # Declare edges
    edge_count = 0
    for name, spec in sorted(subsystems.items()):
        allowed = spec.get("allowed_dependencies") or []
        for dep in allowed:
            lines.append(f"  {name} --> {dep}")
            edge_count += 1

    if edge_count == 0:
        lines.append("  %% No cross-subsystem edges declared (isolated subsystems)")

    lines.append("```")
    return "\n".join(lines)


def generate_ascii_graph(subsystems: dict[str, Any]) -> str:
    """
    Generates a formatted ASCII directed acyclic graph (DAG) representation
    in topological consumer-to-primitive order.
    """
    lines = [
        "SDCS Declarative Topology DAG (Pillar 2: wiring.yaml)",
        "====================================================",
    ]

    # Calculate in-degree to sort consumers first
    in_degree = defaultdict(int)
    for name in subsystems:
        in_degree[name] = 0
    for name, spec in subsystems.items():
        allowed = spec.get("allowed_dependencies") or []
        for dep in allowed:
            in_degree[dep] += 1

    # Sort: subsystems with in-degree 0 (top consumers) down to leaf nodes
    sorted_nodes = sorted(
        subsystems.keys(),
        key=lambda n: (in_degree[n], -len(subsystems[n].get("allowed_dependencies") or []), n),
    )

    for name in sorted_nodes:
        spec = subsystems[name]
        path = spec.get("path", "")
        path_str = f" ({path})" if path else ""
        allowed = spec.get("allowed_dependencies") or []

        lines.append(f"[{name}]{path_str}")
        if not allowed:
            lines.append("  └──> (leaf: zero outbound subsystem dependencies)")
        else:
            for idx, dep in enumerate(allowed):
                is_last = idx == len(allowed) - 1
                branch = "└──>" if is_last else "├──>"
                lines.append(f"  {branch} [{dep}]")
        lines.append("")

    return "\n".join(lines).rstrip()


def run_graph_command(
    repo_root: Path,
    wiring_path: str | Path | None = None,
    graph_format: str = "ascii",
    output_path: str | Path | None = None,
) -> int:
    """CLI runner for sdcs graph."""
    w_file = locate_wiring_file(repo_root, wiring_path)
    if w_file is None:
        print(f"[ERROR] wiring.yaml not found in {repo_root} or .agent/", file=sys.stderr)
        return 1

    data = parse_wiring(w_file)
    subsystems = data.get("subsystems") or {}

    if not subsystems:
        print(f"[WARN] No subsystems declared in {w_file}")
        return 0

    fmt = graph_format.lower().strip()
    if fmt == "mermaid":
        rendered = generate_mermaid_graph(subsystems)
    else:
        rendered = generate_ascii_graph(subsystems)

    if output_path:
        out_p = Path(output_path)
        if not out_p.is_absolute():
            out_p = repo_root / out_p
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(rendered + "\n", encoding="utf-8")
        print(f"✓ [SAVED] Topology diagram saved to: {out_p}")
    else:
        print(rendered)

    return 0
