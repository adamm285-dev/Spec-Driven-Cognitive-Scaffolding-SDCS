import os
import subprocess
import sys
from pathlib import Path

from sdcs.hydrate import compile_hydration_payload
from sdcs.verifier.state import count_tokens
from sdcs.warehouse import (
    compile_tier1_index,
    filter_records,
    format_warehouse_record,
    load_cached_records,
    parse_warehouse_record,
    publish_record,
    run_gate_w_audit,
    sanitize_warehouse_record,
    scan_for_sensitive_data,
    sync_warehouse,
)

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")


# -----------------------------------------------------------------------------
# 1. Gate W: Secret & PII Screening Tests
# -----------------------------------------------------------------------------

def test_gate_w_screening():
    dirty_text = """
    We attempted to authenticate using API key AIzaSyA1234567890123456789012345678901 and secret sk-abcdef123456789012345678.
    Contact the on-call engineer at test.engineer@company.com or phone +1-555-867-5309.
    The database node at 198.51.100.42 was unresponsive, but localhost 127.0.0.1 was fine.
    """
    findings = scan_for_sensitive_data(dirty_text)
    types_found = {f["type"] for f in findings}

    assert "api_key" in types_found
    assert "email" in types_found
    assert "phone" in types_found
    assert "ip" in types_found
    # 127.0.0.1 should not be flagged as a routable IP
    assert not any("127.0.0.1" in f["match"] for f in findings)

    # Test audit function
    is_clean, violations = run_gate_w_audit(dirty_text)
    assert not is_clean
    assert len(violations) >= 4

    # Test sanitization
    sanitized, redactions = sanitize_warehouse_record(dirty_text)
    assert "<REDACTED_API_KEY>" in sanitized
    assert "<REDACTED_EMAIL>" in sanitized
    assert "<REDACTED_PHONE_NUMBER>" in sanitized
    assert "<REDACTED_IP>" in sanitized
    assert "test.engineer@company.com" not in sanitized
    assert "198.51.100.42" not in sanitized
    assert len(redactions) >= 4

    # Verify sanitized text passes Gate W
    clean_status, clean_violations = run_gate_w_audit(sanitized)
    assert clean_status
    assert len(clean_violations) == 0


# -----------------------------------------------------------------------------
# 2. Record Parsing & Formatting Tests
# -----------------------------------------------------------------------------

def test_parse_and_format_record():
    raw_record = """---
id: "W-TEL-001"
title: "Telnyx Outbound Voice Handshake Latency Spike"
tags: ["telecom", "telnyx", "sip"]
severity: "critical"
context_envelope:
  language: ["python", "node"]
  domain: ["telecom", "voice"]
affects_version: "< 2.5.0"
date_recorded: "2026-09-20"
ttl_days: 180
---

### THE TRAP
Attempting to establish SIP outbound call legs synchronously inside active request thread.

### THE EMPIRICAL PROOF
Measured p99 latency spiked to 920ms under 50 concurrent calls.

### THE MITIGATION (THE INVARIANT)
Always dispatch call leg initiation to an isolated Celery/Redis worker.

### WHAT WOULD REOPEN IT
If Telnyx introduces sub-50ms webhooks in US-East.
"""
    rec = parse_warehouse_record(raw_record)
    assert rec["id"] == "W-TEL-001"
    assert rec["title"] == "Telnyx Outbound Voice Handshake Latency Spike"
    assert rec["tags"] == ["telecom", "telnyx", "sip"]
    assert rec["severity"] == "critical"
    assert rec["context_envelope"]["language"] == ["python", "node"]
    assert "SIP outbound call legs synchronously" in rec["trap"]
    assert "p99 latency spiked to 920ms" in rec["empirical_proof"]
    assert "dispatch call leg initiation" in rec["mitigation"]
    assert "sub-50ms webhooks" in rec["what_would_reopen_it"]

    reformatted = format_warehouse_record(rec)
    assert "id: \"W-TEL-001\"" in reformatted
    assert "### THE MITIGATION (THE INVARIANT)" in reformatted


# -----------------------------------------------------------------------------
# 3. Context Envelope & Blindspot 1 Mitigation Tests
# -----------------------------------------------------------------------------

def test_context_envelope_filtering():
    records = [
        {
            "id": "W-RUST-01",
            "title": "Rust Async Trait Deadlock",
            "tags": ["concurrency", "performance"],
            "severity": "critical",
            "context_envelope": {"language": ["rust"]},
            "trap": "Async trait heap allocation stalls.",
            "mitigation": "Use enum dispatch.",
        },
        {
            "id": "W-PY-01",
            "title": "Python Asyncio Subprocess Zombie",
            "tags": ["concurrency", "python"],
            "severity": "high",
            "context_envelope": {"language": ["python"]},
            "trap": "Subprocesses without wait() become zombies.",
            "mitigation": "Always await process.wait().",
        },
        {
            "id": "W-GEN-01",
            "title": "Database Connection Leak",
            "tags": ["database"],
            "severity": "advisory",
            "context_envelope": {},
            "trap": "Unclosed connections exhaust pool.",
            "mitigation": "Use context managers.",
        },
    ]

    # In a Python project, Rust-specific traps MUST be excluded
    filtered_py = filter_records(
        records,
        subscriptions={"tags": ["concurrency", "performance", "database"], "severity_floor": "advisory"},
        project_context={"language": "python"},
    )
    ids_py = [r["id"] for r in filtered_py]
    assert "W-PY-01" in ids_py
    assert "W-GEN-01" in ids_py
    assert "W-RUST-01" not in ids_py  # Context envelope mismatch successfully filtered!

    # Severity floor check
    filtered_high = filter_records(
        records,
        subscriptions={"tags": ["database", "concurrency"], "severity_floor": "high"},
        project_context={"language": "python"},
    )
    ids_high = [r["id"] for r in filtered_high]
    assert "W-PY-01" in ids_high
    assert "W-GEN-01" not in ids_high  # Advisory is below 'high' floor


# -----------------------------------------------------------------------------
# 4. Two-Tier Hierarchical Paging & Token Budget Tests (Blindspot 2)
# -----------------------------------------------------------------------------

def test_tier1_index_token_budget():
    records = []
    for i in range(25):
        records.append({
            "id": f"W-VEND-{i:03d}",
            "title": f"Vendor API Rate Limit Trap {i}",
            "tags": ["telecom", "api"],
            "mitigation": f"Rate limit outbound requests to <= {10 + i} RPS.",
        })

    table, tokens = compile_tier1_index(records, max_tokens=250)
    assert "| ID | Tag | Trap Summary | What to Avoid |" in table
    assert tokens <= 250
    assert tokens > 0
    # Confirm table contains rows
    assert "`W-VEND-000`" in table


# -----------------------------------------------------------------------------
# 5. Version-Bounded TTL & Expiration Tests (Blindspot 4)
# -----------------------------------------------------------------------------

def test_ttl_expiration():
    expired_record = """---
id: "W-LEGACY-01"
title: "Ancient SQLite Concurrency Lock"
tags: ["sqlite"]
severity: "high"
date_recorded: "2020-01-01"
ttl_days: 90
---

### THE TRAP
SQLite locked under concurrent reads.

### THE MITIGATION (THE INVARIANT)
Enable WAL mode.
"""
    rec = parse_warehouse_record(expired_record)
    assert rec["expired"] is True

    table, _ = compile_tier1_index([rec], max_tokens=200)
    assert "[EXPIRED] Ancient SQLite Concurrency Lock" in table


# -----------------------------------------------------------------------------
# 6. Publishing Flow & Gate W Pre-Publish Scrubber (Blindspot 3)
# -----------------------------------------------------------------------------

def test_publish_with_gate_w_sanitization(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    decisions_file = repo_root / "decisions.md"
    decisions_file.write_text("""# Decisions
## REJ-042: Direct Twilio Rest Auth
- **The Claim:** Use direct Twilio client with staging key AIzaSyC9999999999999999999999999999999.
- **The Measurement:** Staging API key logged in production telemetry. Contact secops@corp.com.
- **What Would Reopen It:** Never.
""", encoding="utf-8")

    warehouse_repo = tmp_path / "central_warehouse"
    warehouse_repo.mkdir()

    # 1. Without scrub and not forced -> Should reject publish
    success, msg, scrubbed = publish_record(
        identifier="REJ-042",
        repo_root=repo_root,
        warehouse_target=warehouse_repo,
        scrub=False,
        force=False,
    )
    assert not success
    assert "Gate W rejected publish" in msg

    # 2. With scrub=True -> Should auto-sanitize and succeed
    success, msg, scrubbed = publish_record(
        identifier="REJ-042",
        repo_root=repo_root,
        warehouse_target=warehouse_repo,
        scrub=True,
    )
    assert success
    assert len(scrubbed) >= 2
    published_file = warehouse_repo / "records" / "W-REJ-042.md" if (warehouse_repo / "records").is_dir() else warehouse_repo / "W-REJ-042.md"
    assert published_file.is_file()

    content = published_file.read_text(encoding="utf-8")
    assert "<REDACTED_API_KEY>" in content
    assert "<REDACTED_EMAIL>" in content
    assert "secops@corp.com" not in content


# -----------------------------------------------------------------------------
# 7. Offline Resilience & Sync Tests (Blindspot 5)
# -----------------------------------------------------------------------------

def test_warehouse_sync_and_offline_resilience(tmp_path):
    # Setup local warehouse source directory
    source_dir = tmp_path / "source_wh"
    source_dir.mkdir()
    (source_dir / "W-001.md").write_text("""---
id: "W-001"
title: "Test Invariant 1"
tags: ["core"]
severity: "high"
---
### THE TRAP
Trap 1
### THE MITIGATION
Mitigation 1
""", encoding="utf-8")

    cache_dir = tmp_path / "cache"
    success, msg, count = sync_warehouse(str(source_dir), cache_dir)
    assert success
    assert count == 1
    assert (cache_dir / "W-001.md").is_file()

    # Test loading cached records
    cached = load_cached_records(cache_dir)
    assert len(cached) == 1
    assert cached[0]["id"] == "W-001"

    # Test unreachable remote URL -> should gracefully fallback without unhandled exceptions
    fake_remote = "https://invalid-host-sdcs-warehouse.local/repo.git"
    success_remote, msg_remote, cached_count = sync_warehouse(fake_remote, cache_dir)
    assert not success_remote
    assert "Offline fallback" in msg_remote
    assert cached_count == 1


# -----------------------------------------------------------------------------
# 8. Deterministic Context Compiler Integration
# -----------------------------------------------------------------------------

def test_hydrate_with_warehouse_subscription(tmp_path):
    # Setup wiring.yaml with warehouse configuration
    cache_dir = tmp_path / "wh_cache"
    cache_dir.mkdir()
    (cache_dir / "W-TEL-001.md").write_text("""---
id: "W-TEL-001"
title: "Telnyx Rate Limit Spike"
tags: ["telecom"]
severity: "high"
---
### THE TRAP
Too many parallel calls.
### THE MITIGATION (THE INVARIANT)
Batch calls with leaky bucket.
""", encoding="utf-8")

    (tmp_path / "spine.md").write_text("# Constitutional Invariants\nLaw\n", encoding="utf-8")
    (tmp_path / "state.md").write_text("## Current Objective\nTask\n", encoding="utf-8")
    (tmp_path / "wiring.yaml").write_text(f"""
version: "1.6"
subsystems:
  core:
    path: "src/"
    allowed_dependencies: []
warehouse:
  cache_dir: "{cache_dir.as_posix()}"
  subscriptions:
    tags: ["telecom"]
    severity_floor: "high"
""", encoding="utf-8")

    payload, tokens = compile_hydration_payload(tmp_path, profile="standard")
    assert "[CENTRAL WAREHOUSE: FLEET FEDERATION]" in payload
    assert "`W-TEL-001`" in payload
    assert "#telecom" in payload
    assert tokens > 0


# -----------------------------------------------------------------------------
# 9. CLI End-to-End Execution Tests
# -----------------------------------------------------------------------------

def test_cli_warehouse_commands(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    (cache_dir / "W-001.md").write_text("""---
id: "W-CLI-01"
title: "CLI Record"
tags: ["cli"]
severity: "critical"
---
### THE TRAP
Trap
### THE MITIGATION
Mitigation
""", encoding="utf-8")

    # 1. test 'sdcs warehouse list'
    cmd_list = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "warehouse",
        "list",
        "--cache-dir",
        str(cache_dir),
        "--repo-root",
        str(repo_root),
    ]
    res_list = subprocess.run(cmd_list, cwd=str(repo_root), capture_output=True, text=True, check=True, env=ENV)
    assert "W-CLI-01" in res_list.stdout

    # 2. test 'sdcs verify --warehouse'
    (repo_root / "decisions.md").write_text("""# Decisions
## REJ-001: Good Decision
THE CLAIM: Safe
THE MEASUREMENT: Pass
WHAT WOULD REOPEN IT: Never
""", encoding="utf-8")

    cmd_verify = [
        sys.executable,
        "-m",
        "sdcs.cli",
        "verify",
        "--warehouse",
        "--repo-root",
        str(repo_root),
    ]
    res_verify = subprocess.run(cmd_verify, cwd=str(repo_root), capture_output=True, text=True, check=True, env=ENV)
    assert "Gate W Secret & PII Sanitization Audit" in res_verify.stdout
    assert "[STATUS: CLEAN]" in res_verify.stdout
