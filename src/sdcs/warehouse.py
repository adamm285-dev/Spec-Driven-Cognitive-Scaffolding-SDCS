"""
sdcs.warehouse - Central Cognitive Warehouse & Fleet Federation Engine (SPEC-001 v1.6.0)

Implements cross-project organizational memory, Gate W secret & PII scrubbing,
version-bounded TTL expiration, and two-tier hierarchical paging.
"""

import datetime
import fnmatch
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from sdcs.verifier.state import count_tokens


# -----------------------------------------------------------------------------
# Gate W: Secret & PII Sanitizer Patterns
# -----------------------------------------------------------------------------

RE_API_KEY_PATTERNS = [
    (r"\bAIza[0-9A-Za-z\-_]{30,40}\b", "Google/Gemini API Key"),
    (r"\bAQ\.[0-9A-Za-z\-_]{20,}\b", "Gemini Fleet API Key"),
    (r"\bsk-[a-zA-Z0-9]{20,}\b", "OpenAI Secret Key"),
    (r"\bghp_[a-zA-Z0-9]{36}\b", "GitHub Personal Token"),
    (r"\bgithub_pat_[a-zA-Z0-9_]{30,}\b", "GitHub Fine-Grained Token"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS Access Key ID"),
    (r"\bBearer\s+[A-Za-z0-9\-\._~\+\/]+=*\b", "Bearer Auth Token"),
]

RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
RE_PHONE = re.compile(r"(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
# IPv4 regex excluding standard loopback 127.0.0.1 and 0.0.0.0
RE_IPV4 = re.compile(
    r"\b(?!(?:127\.0\.0\.1|0\.0\.0\.0)\b)(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)


def scan_for_sensitive_data(content: str) -> list[dict]:
    """
    Gate W static scanner: detects exposed API keys, private credentials,
    email addresses, telephone numbers, and routable IPv4 addresses.
    """
    findings: list[dict] = []

    # 1. API Keys & Auth Tokens
    for pattern, label in RE_API_KEY_PATTERNS:
        for match in re.finditer(pattern, content):
            findings.append({
                "type": "api_key",
                "label": label,
                "match": match.group(0),
                "span": match.span(),
            })

    # 2. Email Addresses
    for match in RE_EMAIL.finditer(content):
        findings.append({
            "type": "email",
            "label": "Email Address",
            "match": match.group(0),
            "span": match.span(),
        })

    # 3. Phone Numbers
    for match in RE_PHONE.finditer(content):
        val = match.group(0)
        # Avoid matching short version numbers like 1.2.3
        if sum(c.isdigit() for c in val) >= 10:
            findings.append({
                "type": "phone",
                "label": "Phone Number",
                "match": val,
                "span": match.span(),
            })

    # 4. Routable IPv4 Addresses
    for match in RE_IPV4.finditer(content):
        findings.append({
            "type": "ip",
            "label": "Routable IPv4 Address",
            "match": match.group(0),
            "span": match.span(),
        })

    return findings


def sanitize_warehouse_record(content: str) -> tuple[str, list[str]]:
    """
    Sanitizes content by replacing detected secrets and PII with canonical placeholders.
    Returns: (sanitized_text, list_of_redaction_notices)
    """
    findings = scan_for_sensitive_data(content)
    if not findings:
        return content, []

    redactions: list[str] = []
    # Sort findings in reverse by start span to safely replace substrings
    sorted_findings = sorted(findings, key=lambda f: f["span"][0], reverse=True)
    sanitized = content

    for f in sorted_findings:
        start, end = f["span"]
        val = f["match"]
        kind = f["type"]
        placeholder = (
            "<REDACTED_API_KEY>" if kind == "api_key"
            else "<REDACTED_EMAIL>" if kind == "email"
            else "<REDACTED_PHONE_NUMBER>" if kind == "phone"
            else "<REDACTED_IP>"
        )
        sanitized = sanitized[:start] + placeholder + sanitized[end:]
        redactions.append(f"Scrubbed {f['label']} ({val[:4]}...{val[-2:] if len(val) > 6 else ''}) -> {placeholder}")

    redactions.reverse()
    return sanitized, redactions


def run_gate_w_audit(content: str) -> tuple[bool, list[str]]:
    """Runs Gate W audit on a string. Returns (is_clean, violations)."""
    findings = scan_for_sensitive_data(content)
    if not findings:
        return True, []
    violations = [f"[{f['type'].upper()}] {f['label']}: {f['match']}" for f in findings]
    return False, violations


# -----------------------------------------------------------------------------
# Warehouse Record Parsing & Formatting
# -----------------------------------------------------------------------------

def parse_warehouse_record(content: str, source_path: Path | None = None) -> dict:
    """
    Parses a warehouse record (YAML frontmatter + Markdown sections).
    """
    record: dict = {
        "id": "W-UNKNOWN",
        "title": "Untitled Record",
        "tags": [],
        "severity": "advisory",
        "context_envelope": {},
        "affects_version": "",
        "date_recorded": "",
        "ttl_days": 365,
        "trap": "",
        "empirical_proof": "",
        "mitigation": "",
        "what_would_reopen_it": "",
        "raw_content": content,
        "source_path": str(source_path) if source_path else None,
        "expired": False,
    }

    # Extract YAML frontmatter
    fm_text = ""
    body_text = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            body_text = parts[2].strip()

    if fm_text:
        if yaml is not None:
            try:
                fm_data = yaml.safe_load(fm_text) or {}
                if isinstance(fm_data, dict):
                    record.update({k: v for k, v in fm_data.items() if v is not None})
            except Exception:
                pass
        else:
            # Fallback simple line parser if PyYAML is missing
            for line in fm_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip().lower()
                    v = v.strip().strip('"\'')
                    if k in record:
                        record[k] = v

    # Ensure tags are a list of lowercase strings
    tags = record.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip().lstrip("#").lower() for t in tags.split(",") if t.strip()]
    elif isinstance(tags, list):
        tags = [str(t).strip().lstrip("#").lower() for t in tags if str(t).strip()]
    record["tags"] = tags

    # Extract ID & Title from markdown heading if present
    h_match = re.search(r"(?m)^##\s+((?:REJ|ADR|W)-[A-Za-z0-9_-]+):?\s*(.*?)$", content)
    if h_match:
        if record["id"] == "W-UNKNOWN":
            raw_hid = h_match.group(1).strip()
            record["id"] = raw_hid if raw_hid.startswith("W-") else f"W-{raw_hid}"
        if record["title"] == "Untitled Record" and h_match.group(2).strip():
            record["title"] = h_match.group(2).strip()

    # Extract body sections from body_text (supporting both ### and - **Header:** formats)
    def extract_section(header_pattern: str, text: str) -> str:
        pattern = rf"(?i)###\s+{header_pattern}\s*\n(.*?)(?=\n###|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        if match and match.group(1).strip():
            return match.group(1).strip()
        pattern_bullet = rf"(?i)(?:^|\n)\s*[-*]?\s*\*\*?\s*{header_pattern}\s*:?\s*\*?\*?:?\s*(.*?)(?=\n\s*[-*]?\s*\*\*|\Z)"
        match_b = re.search(pattern_bullet, text, re.DOTALL)
        if match_b and match_b.group(1).strip():
            return match_b.group(1).strip()
        return ""

    trap = extract_section(r"(?:THE\s+TRAP|THE\s+CLAIM)", body_text)
    proof = extract_section(r"(?:THE\s+EMPIRICAL\s+PROOF|THE\s+MEASUREMENT)", body_text)
    mitigation = extract_section(r"(?:THE\s+MITIGATION(?:\s+\(THE\s+INVARIANT\))?|THE\s+INVARIANT)", body_text)
    reopen = extract_section(r"WHAT\s+WOULD\s+REOPEN\s+IT", body_text)

    # Fallback: if no recognized section matched, preserve body_text in trap so data is never discarded
    if not trap and not proof and body_text.strip():
        trap = body_text.strip()

    record["trap"] = trap
    record["empirical_proof"] = proof
    record["mitigation"] = mitigation
    record["what_would_reopen_it"] = reopen

    # Check TTL expiration
    date_str = str(record.get("date_recorded", "")).strip()
    ttl_days = int(record.get("ttl_days") or 365)
    if date_str:
        try:
            rec_date = datetime.date.fromisoformat(date_str)
            if datetime.date.today() > rec_date + datetime.timedelta(days=ttl_days):
                record["expired"] = True
        except ValueError:
            pass

    return record


def format_warehouse_record(record: dict) -> str:
    """Formats a record dict into canonical Markdown with YAML frontmatter."""
    fm_lines = [
        "---",
        f"id: \"{record.get('id', 'W-GEN-001')}\"",
        f"title: \"{record.get('title', 'Warehouse Record')}\"",
        f"tags: {record.get('tags', [])}",
        f"severity: \"{record.get('severity', 'advisory')}\"",
    ]
    env = record.get("context_envelope", {})
    if env:
        fm_lines.append("context_envelope:")
        for k, v in env.items():
            fm_lines.append(f"  {k}: {v}")
    if record.get("affects_version"):
        fm_lines.append(f"affects_version: \"{record['affects_version']}\"")
    fm_lines.append(f"date_recorded: \"{record.get('date_recorded', datetime.date.today().isoformat())}\"")
    fm_lines.append(f"ttl_days: {record.get('ttl_days', 365)}")
    fm_lines.append("---\n")

    body_lines = [
        "### THE TRAP",
        record.get("trap", "").strip() or "Unspecified trap scenario.",
        "",
        "### THE EMPIRICAL PROOF",
        record.get("empirical_proof", "").strip() or "Empirical measurement recorded.",
        "",
        "### THE MITIGATION (THE INVARIANT)",
        record.get("mitigation", "").strip() or "Enforce boundary contract.",
        "",
        "### WHAT WOULD REOPEN IT",
        record.get("what_would_reopen_it", "").strip() or "Empirical evidence contradicting the invariant.",
        "",
    ]
    return "\n".join(fm_lines) + "\n" + "\n".join(body_lines)


# -----------------------------------------------------------------------------
# Cache & Configuration Management
# -----------------------------------------------------------------------------

def locate_warehouse_config(repo_root: Path, custom_wiring: Path | None = None) -> dict:
    """Reads the 'warehouse' configuration block from wiring.yaml."""
    candidates = [custom_wiring] if custom_wiring else [repo_root / "wiring.yaml", repo_root / ".agent" / "wiring.yaml"]
    for c in candidates:
        if c and c.is_file():
            if yaml is not None:
                try:
                    data = yaml.safe_load(c.read_text(encoding="utf-8")) or {}
                    return data.get("warehouse", {})
                except Exception:
                    pass
    return {}


def locate_warehouse_cache(
    repo_root: Path,
    config: dict | None = None,
    custom_cache: Path | None = None,
) -> Path:
    """Resolves local cache directory with offline resilience."""
    if custom_cache:
        custom_cache.mkdir(parents=True, exist_ok=True)
        return custom_cache

    cfg = config if config is not None else locate_warehouse_config(repo_root)
    configured_dir = cfg.get("cache_dir")
    if configured_dir:
        p = Path(os.path.expanduser(configured_dir))
        if not p.is_absolute():
            p = repo_root / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    # Standard global user cache
    default_cache = Path.home() / ".sdcs" / "warehouse" / "cache"
    default_cache.mkdir(parents=True, exist_ok=True)
    return default_cache


# -----------------------------------------------------------------------------
# Synchronization & Publishing
# -----------------------------------------------------------------------------

def sync_warehouse(source: str, cache_dir: Path) -> tuple[bool, str, int]:
    """
    Synchronizes records from source (local directory or remote git repo) into local cache.
    Offline resilient: if network/git fails, gracefully retains existing cached records.
    Returns: (success, message, record_count)
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    source_path = Path(source).expanduser()

    # 1. Local directory source
    if source_path.is_dir():
        count = 0
        search_dirs = [source_path / "records", source_path]
        for sdir in search_dirs:
            if sdir.is_dir():
                for f in sdir.glob("*.md"):
                    if f.name.lower() != "readme.md":
                        shutil.copy2(f, cache_dir / f.name)
                        count += 1
                for f in sdir.glob("*.yaml"):
                    shutil.copy2(f, cache_dir / f.name)
                    count += 1
                if count > 0:
                    break
        return True, f"Synchronized {count} records from local directory '{source}'.", count

    # 2. Remote git repository source
    if source.startswith(("http://", "https://", "git@", "ssh://")):
        repo_subpath = cache_dir / ".git_remote"
        try:
            if (repo_subpath / ".git").is_dir():
                res = subprocess.run(
                    ["git", "pull", "--ff-only"],
                    cwd=str(repo_subpath),
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            else:
                res = subprocess.run(
                    ["git", "clone", "--depth", "1", source, str(repo_subpath)],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
            if res.returncode == 0:
                count = 0
                search_dirs = [repo_subpath / "records", repo_subpath]
                for sdir in search_dirs:
                    if sdir.is_dir():
                        for f in sdir.glob("*.md"):
                            if f.name.lower() != "readme.md":
                                shutil.copy2(f, cache_dir / f.name)
                                count += 1
                return True, f"Synchronized {count} records from remote '{source}'.", count
            else:
                existing = len(list(cache_dir.glob("*.md")))
                return False, f"Network/Git sync failed. Offline fallback active with {existing} cached records.", existing
        except (subprocess.SubprocessError, OSError) as ex:
            # Offline fallback
            existing = len(list(cache_dir.glob("*.md")))
            return False, f"Network/Git sync failed ({ex}). Offline fallback active with {existing} cached records.", existing

    return False, f"Invalid warehouse source location: '{source}'", 0


def publish_record(
    identifier: str,
    repo_root: Path,
    warehouse_target: Path,
    scrub: bool = True,
    force: bool = False,
) -> tuple[bool, str, list[str]]:
    """
    Promotes a local rejection or record file to a warehouse repository.
    Enforces Gate W static screening before promotion.
    Returns: (success, message, scrubbed_items)
    """
    content = ""
    source_file: Path | None = None

    # Case A: identifier is an existing file path
    direct_file = Path(identifier)
    if direct_file.is_file():
        content = direct_file.read_text(encoding="utf-8")
        source_file = direct_file
    else:
        # Case B: identifier is an ID inside decisions.md (e.g., REJ-001)
        decisions_file = repo_root / "decisions.md"
        if not decisions_file.is_file():
            decisions_file = repo_root / ".agent" / "decisions.md"
        if decisions_file.is_file():
            raw_dec = decisions_file.read_text(encoding="utf-8")
            pattern = rf"(?m)^##\s+{re.escape(identifier)}(?::\s*(.*?))?\n(.*?)(?=\n##\s+(?:REJ|ADR|W)-|\Z)"
            match = re.search(pattern, raw_dec, re.DOTALL)
            if match:
                title_line = (match.group(1) or "").strip()
                body_rest = (match.group(2) or "").strip()
                content = f"## {identifier}: {title_line}\n" + body_rest
                source_file = decisions_file

    if not content:
        return False, f"Could not locate rejection or record '{identifier}'.", []

    # Parse and construct canonical warehouse record
    record = parse_warehouse_record(content, source_path=source_file)
    if record["id"] == "W-UNKNOWN":
        # Formulate canonical W- ID from identifier
        norm_id = re.sub(r"[^A-Za-z0-9_-]", "", identifier).upper()
        if not norm_id.startswith("W-"):
            norm_id = f"W-{norm_id}"
        record["id"] = norm_id

    formatted_text = format_warehouse_record(record)

    # Gate W Screening
    is_clean, violations = run_gate_w_audit(formatted_text)
    scrubbed_items: list[str] = []

    if not is_clean:
        if not scrub and not force:
            violation_summary = "\n".join(f"  - {v}" for v in violations)
            return False, f"Gate W rejected publish due to unscrubbed secrets/PII:\n{violation_summary}", []
        # Auto-scrubbing
        formatted_text, scrubbed_items = sanitize_warehouse_record(formatted_text)

    # Write record to warehouse target
    target_dir = warehouse_target / "records" if (warehouse_target / "records").is_dir() else warehouse_target
    target_dir.mkdir(parents=True, exist_ok=True)
    out_file = target_dir / f"{record['id']}.md"
    out_file.write_text(formatted_text, encoding="utf-8")

    return True, f"Successfully published {record['id']} to {out_file}", scrubbed_items


# -----------------------------------------------------------------------------
# Filtering & Tier-1 Index Compilation
# -----------------------------------------------------------------------------

def load_cached_records(cache_dir: Path) -> list[dict]:
    """Loads all records stored in the warehouse cache directory."""
    records: list[dict] = []
    if not cache_dir.is_dir():
        return records

    for f in cache_dir.glob("*.md"):
        if f.name.lower() in ("readme.md", "template.md"):
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            rec = parse_warehouse_record(content, source_path=f)
            records.append(rec)
        except Exception:
            pass

    for f in cache_dir.glob("*.yaml"):
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            rec = parse_warehouse_record(content, source_path=f)
            records.append(rec)
        except Exception:
            pass

    return records


def filter_records(
    records: list[dict],
    subscriptions: dict,
    project_context: dict | None = None,
) -> list[dict]:
    """
    Filters warehouse records against wiring.yaml subscriptions and project context.
    Solves Blindspot 1 (Conflicting Rejections) via Context Envelope matching.
    """
    ctx = project_context or {}
    proj_lang = str(ctx.get("language", "")).lower().strip()
    proj_domain = str(ctx.get("domain", "")).lower().strip()

    sub_tags = [t.lower().lstrip("#") for t in subscriptions.get("tags", [])]
    sev_floor = str(subscriptions.get("severity_floor", "advisory")).lower()
    sev_ranks = {"critical": 4, "high": 3, "medium": 2, "advisory": 1, "low": 0}
    min_rank = sev_ranks.get(sev_floor, 1)

    matched: list[dict] = []

    for r in records:
        # 1. Severity floor filter
        r_sev = str(r.get("severity", "advisory")).lower()
        if sev_ranks.get(r_sev, 1) < min_rank:
            continue

        # 2. Tag filter (if subscriptions specify tags)
        if sub_tags:
            rec_tags = [t.lower().lstrip("#") for t in r.get("tags", [])]
            if not any(t in sub_tags for t in rec_tags):
                continue

        # 3. Context Envelope Constraints (Language & Domain)
        envelope = r.get("context_envelope", {})
        if envelope:
            # Language/runtime constraint
            env_langs = envelope.get("language") or envelope.get("runtime") or []
            if isinstance(env_langs, str):
                env_langs = [env_langs]
            env_langs = [str(x).lower().strip() for x in env_langs]
            if env_langs and proj_lang:
                if proj_lang not in env_langs:
                    continue  # Mismatch: silently exclude

            # Domain constraint
            env_domains = envelope.get("domain", [])
            if isinstance(env_domains, str):
                env_domains = [env_domains]
            env_domains = [str(x).lower().strip() for x in env_domains]
            if env_domains and proj_domain:
                if proj_domain not in env_domains:
                    continue  # Mismatch: silently exclude

        matched.append(r)

    return matched


def compile_tier1_index(records: list[dict], max_tokens: int = 250) -> tuple[str, int]:
    """
    Two-Tier Hierarchical Paging (Blindspot 2 Solution):
    Compiles records into a hyper-dense Markdown table fitting within max_tokens.
    """
    if not records:
        return "", 0

    header = "| ID | Tag | Trap Summary | What to Avoid |\n| :--- | :--- | :--- | :--- |\n"
    rows: list[str] = []

    for r in records:
        rec_id = r.get("id", "W-???")
        tags = " ".join(f"#{t}" for t in r.get("tags", [])[:2]) or "#general"
        title = r.get("title", "Observed Trap")
        if r.get("expired"):
            title = f"[EXPIRED] {title}"

        # Mitigation summary
        mitigation = r.get("mitigation", "")
        if not mitigation:
            mitigation = r.get("trap", "Consult full record.")
        mitigation_one_liner = mitigation.split("\n")[0].strip()
        if len(mitigation_one_liner) > 75:
            mitigation_one_liner = mitigation_one_liner[:72] + "..."

        row = f"| `{rec_id}` | {tags} | {title} | {mitigation_one_liner} |"
        rows.append(row)

    # Budget truncation check
    selected_rows = list(rows)
    while selected_rows:
        candidate_table = header + "\n".join(selected_rows) + "\n"
        tokens = count_tokens(candidate_table)
        if tokens <= max_tokens or len(selected_rows) == 1:
            return candidate_table, tokens
        selected_rows.pop()  # Drop oldest / least critical

    return "", 0
