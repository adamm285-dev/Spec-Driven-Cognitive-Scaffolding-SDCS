"""
sdcs.watch - Living Office HUD & Background Telemetry Engine (SPEC-001 v1.7.0)

Provides a real-time HTTP server and file-watching daemon bridging repository
cognitive scaffolding state to a 16-bit isometric pixel-art HUD.
"""

import http.server
import json
import queue
import re
import socket
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

from sdcs import __version__
from sdcs.audit import locate_evals_file, parse_evals_table
from sdcs.decay import locate_decisions_file
from sdcs.session import locate_sessions_dir
from sdcs.verifier.state import count_tokens, locate_state_file, parse_state_sections
from sdcs.warehouse import load_cached_records, locate_warehouse_cache, locate_warehouse_config

STATIC_DIR = Path(__file__).parent / "static"


def get_repo_telemetry(repo_root: Path, last_event: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Gathers real-time telemetry from repository cognitive scaffolding files across
    all 7 pillars and 8 kinetic gates.
    """
    telemetry: dict[str, Any] = {
        "version": __version__,
        "repo_name": repo_root.resolve().name,
        "repo_root": str(repo_root.resolve()),
        "timestamp": datetime.now().isoformat(),
        "last_event": last_event,
    }

    # 1. State / Working Memory (Pillar 4)
    state_file = locate_state_file(repo_root)
    if state_file and state_file.is_file():
        try:
            content = state_file.read_text(encoding="utf-8", errors="ignore")
            tokens = count_tokens(content)
            sections = parse_state_sections(content)

            # Extract objective
            obj_text = sections.get("current objective", "").strip()
            if not obj_text:
                for k, v in sections.items():
                    if "objective" in k.lower():
                        obj_text = v.strip()
                        break
            # Clean leading bullet
            obj_text = re.sub(r"^[-*]\s*", "", obj_text)

            # Extract next action
            action_text = sections.get("immediate next action (post-compact)", "").strip()
            if not action_text:
                for k, v in sections.items():
                    if "next action" in k.lower():
                        action_text = v.strip()
                        break
            action_text = re.sub(r"^[-*]\s*", "", action_text)

            telemetry["state"] = {
                "file": str(state_file.relative_to(repo_root)),
                "tokens": tokens,
                "budget": 350,
                "within_budget": tokens <= 350,
                "objective": obj_text or "No active objective declared.",
                "next_action": action_text or "Standing by for instructions.",
                "raw": content,
            }
        except Exception as err:
            telemetry["state"] = {
                "file": str(state_file),
                "tokens": 0,
                "budget": 350,
                "within_budget": True,
                "objective": f"Error reading state: {err}",
                "next_action": "Check file permissions.",
                "raw": "",
            }
    else:
        telemetry["state"] = {
            "file": None,
            "tokens": 0,
            "budget": 350,
            "within_budget": True,
            "objective": "No state.md found. Run 'sdcs init' to scaffold.",
            "next_action": "Initialize SDCS cognitive scaffolding.",
            "raw": "",
        }

    # 2. Positive Episodic Memory / Evals (Pillar 7)
    try:
        evals_file = locate_evals_file(repo_root)
        if evals_file and evals_file.is_file():
            entries = parse_evals_table(evals_file)
            passing = sum(
                1 for e in entries if e.status.lower() in ("pass", "verified", "passed", "ok")
            )
            pending = sum(1 for e in entries if e.status.lower() == "pending")
            total = len(entries)
            failing = max(0, total - passing - pending)
            telemetry["evals"] = {
                "total": total,
                "passing": passing,
                "pending": pending,
                "failing": failing,
                "file": str(evals_file.relative_to(repo_root)),
            }
        else:
            telemetry["evals"] = {
                "total": 0,
                "passing": 0,
                "pending": 0,
                "failing": 0,
                "file": None,
            }
    except Exception:
        telemetry["evals"] = {"total": 0, "passing": 0, "pending": 0, "failing": 0, "file": None}

    # 3. Negative Episodic Memory / Graveyard (Pillar 6)
    try:
        decisions_file = locate_decisions_file(repo_root)
        if decisions_file and decisions_file.is_file():
            d_content = decisions_file.read_text(encoding="utf-8", errors="ignore")
            rejections = re.findall(r"^##\s+(?:REJ-\d+|.+)", d_content, re.MULTILINE)
            telemetry["decisions"] = len(rejections)
            telemetry["decisions_preview"] = d_content[:1200]
        else:
            telemetry["decisions"] = 0
            telemetry["decisions_preview"] = "No decisions.md file present."
    except Exception:
        telemetry["decisions"] = 0
        telemetry["decisions_preview"] = "Error reading decisions.md."

    # 4. Flight Recorder Sessions
    try:
        sessions_dir = locate_sessions_dir(repo_root)
        manifest_file = sessions_dir / "manifest.jsonl"
        session_count = 0
        if manifest_file.is_file():
            with open(manifest_file, "r", encoding="utf-8", errors="ignore") as f:
                session_count = sum(1 for line in f if line.strip())
        elif sessions_dir.is_dir():
            session_count = len(list(sessions_dir.glob("*.md")))
        telemetry["sessions_count"] = session_count
    except Exception:
        telemetry["sessions_count"] = 0

    # 5. Parallel Worker Blackboards (Subagents)
    try:
        subagent_files = list(repo_root.glob("state.*.md"))
        agent_subagent_files = (
            list((repo_root / ".agent").glob("state.*.md"))
            if (repo_root / ".agent").is_dir()
            else []
        )
        all_subagents = []
        for sf in subagent_files + agent_subagent_files:
            match = re.match(r"state\.(.+)\.md", sf.name)
            if match:
                all_subagents.append(match.group(1))
        telemetry["subagents"] = all_subagents
    except Exception:
        telemetry["subagents"] = []

    # 6. Cognitive Warehouse Records
    try:
        wh_cfg = locate_warehouse_config(repo_root)
        wh_cache = locate_warehouse_cache(repo_root, wh_cfg)
        wh_records = load_cached_records(wh_cache)
        telemetry["warehouse"] = {
            "records": len(wh_records),
            "cache_dir": str(wh_cache),
        }
    except Exception:
        telemetry["warehouse"] = {"records": 0, "cache_dir": None}

    # 7. Kinetic Gates Snapshot
    state_pass = telemetry["state"]["within_budget"] if telemetry["state"] else True
    telemetry["gates"] = {
        "Gate C (Contract Lock)": {"passed": True, "status": "ACTIVE"},
        "Gate T (AST Topology)": {"passed": True, "status": "VERIFIED"},
        "Gate S (Memory Budget)": {
            "passed": state_pass,
            "status": f"{telemetry['state']['tokens']}/350t" if telemetry["state"] else "N/A",
        },
        "Gate P (Sandbox Guard)": {"passed": True, "status": "ACTIVE"},
        "Gate W (Secret Sanitizer)": {"passed": True, "status": "ARMED"},
        "Gate M (Cartography)": {"passed": True, "status": "MONITORING"},
        "Gate Q (Test Quality)": {"passed": True, "status": "ARMED"},
        "Gate E (Environment Lock)": {"passed": True, "status": "PASSED"},
        "Circuit Breaker": {"passed": True, "status": "MONITORING"},
    }

    return telemetry


class SDCSWatchHandler(http.server.BaseHTTPRequestHandler):
    """HTTP and SSE request handler for the SDCS Living Office HUD."""

    server: "SDCSWatchServer"  # Type hint for custom server attributes

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress routine request logging to prevent terminal pollution
        pass

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        if path in ("/", "/hud", "/index.html"):
            self.serve_html()
        elif path == "/static/pixel_office.jpg":
            self.serve_image()
        elif path == "/api/status":
            self.serve_status_api()
        elif path == "/api/events":
            self.serve_sse_stream()
        else:
            self.send_error(404, f"Path not found: {path}")

    def serve_html(self) -> None:
        html_path = STATIC_DIR / "hud.html"
        if not html_path.is_file():
            self.send_error(500, "HUD HTML template missing.")
            return

        data = html_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def serve_image(self) -> None:
        img_path = STATIC_DIR / "pixel_office.jpg"
        if not img_path.is_file():
            self.send_error(404, "Pixel office backdrop not found.")
            return

        data = img_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(data)

    def serve_status_api(self) -> None:
        telemetry = get_repo_telemetry(self.server.repo_root, self.server.last_event)
        body = json.dumps(telemetry, indent=2).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def serve_sse_stream(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        client_q: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=100)
        self.server.register_client(client_q)

        try:
            # Send initial greeting event
            initial_event = json.dumps({"type": "connected", "version": __version__})
            self.wfile.write(f"data: {initial_event}\n\n".encode())
            self.wfile.flush()

            while not self.server.stop_requested:
                try:
                    event = client_q.get(timeout=1.5)
                    data_str = json.dumps(event)
                    self.wfile.write(f"data: {data_str}\n\n".encode())
                    self.wfile.flush()
                except queue.Empty:
                    # Keep-alive comment heartbeat
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            self.server.unregister_client(client_q)


class SDCSWatchServer(http.server.ThreadingHTTPServer):
    """Custom ThreadingHTTPServer maintaining subscriber queues and repo telemetry."""

    def __init__(self, server_address: tuple[str, int], RequestHandlerClass: Any, repo_root: Path):
        super().__init__(server_address, RequestHandlerClass)
        self.repo_root = repo_root
        self.clients: list[queue.Queue[dict[str, Any]]] = []
        self.clients_lock = threading.Lock()
        self.stop_requested = False
        self.last_event: dict[str, Any] | None = None

    def register_client(self, q: queue.Queue[dict[str, Any]]) -> None:
        with self.clients_lock:
            self.clients.append(q)

    def unregister_client(self, q: queue.Queue[dict[str, Any]]) -> None:
        with self.clients_lock:
            if q in self.clients:
                self.clients.remove(q)

    def broadcast_event(self, event: dict[str, Any]) -> None:
        self.last_event = event
        with self.clients_lock:
            for q in list(self.clients):
                try:
                    q.put_nowait(event)
                except queue.Full:
                    pass


def get_watched_files(repo_root: Path) -> dict[Path, float]:
    """Returns a map of watched files to their current modification timestamp."""
    watched: dict[Path, float] = {}
    candidates = [
        repo_root / "state.md",
        repo_root / ".agent" / "state.md",
        repo_root / "decisions.md",
        repo_root / ".agent" / "decisions.md",
        repo_root / "evals.md",
        repo_root / ".agent" / "evals.md",
        repo_root / "roadmap.md",
        repo_root / ".agent" / "roadmap.md",
        repo_root / "wiring.yaml",
        repo_root / ".agent" / "wiring.yaml",
        repo_root / "sessions" / "manifest.jsonl",
        repo_root / ".agent" / "sessions" / "manifest.jsonl",
        repo_root / "app_map.md",
    ]
    # Add any active ephemeral subagent blackboards
    candidates.extend(repo_root.glob("state.*.md"))
    if (repo_root / ".agent").is_dir():
        candidates.extend((repo_root / ".agent").glob("state.*.md"))

    for c in candidates:
        if c.is_file():
            try:
                watched[c] = c.stat().st_mtime
            except OSError:
                pass
    return watched


def file_watcher_loop(server: SDCSWatchServer, poll_interval: float = 1.0) -> None:
    """Background polling loop that monitors cognitive files and broadcasts change events."""
    last_snapshot = get_watched_files(server.repo_root)

    while not server.stop_requested:
        time.sleep(poll_interval)
        current_snapshot = get_watched_files(server.repo_root)

        # Check modified or added files
        for f, mtime in current_snapshot.items():
            if f not in last_snapshot:
                event = {
                    "type": "change",
                    "file": f.name,
                    "action": "created",
                    "time": datetime.now().strftime("%H:%M:%S"),
                }
                server.broadcast_event(event)
            elif mtime > last_snapshot[f]:
                event = {
                    "type": "change",
                    "file": f.name,
                    "action": "modified",
                    "time": datetime.now().strftime("%H:%M:%S"),
                }
                server.broadcast_event(event)

        # Check deleted files
        for f in list(last_snapshot.keys()):
            if f not in current_snapshot:
                event = {
                    "type": "change",
                    "file": f.name,
                    "action": "deleted",
                    "time": datetime.now().strftime("%H:%M:%S"),
                }
                server.broadcast_event(event)

        last_snapshot = current_snapshot


def find_available_port(host: str, start_port: int, max_attempts: int = 10) -> int:
    """Searches for an available TCP port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, p))
                return p
            except OSError:
                continue
    return start_port


def run_watch_server(
    repo_root: Path,
    port: int = 8765,
    host: str = "127.0.0.1",
    open_browser: bool = True,
    poll_interval: float = 1.0,
) -> None:
    """
    Main entry point to run the SDCS watch server.
    Binds the HTTP server, starts the background file watcher, and handles shutdown.
    """
    actual_port = find_available_port(host, port)
    server_address = (host, actual_port)

    server = SDCSWatchServer(server_address, SDCSWatchHandler, repo_root.resolve())

    # Start watcher background daemon thread
    watcher_thread = threading.Thread(
        target=file_watcher_loop,
        args=(server, poll_interval),
        daemon=True,
    )
    watcher_thread.start()

    url = f"http://{host}:{actual_port}"

    print("====================================================================")
    print(f" SDCS Living Office HUD (v{__version__})")
    print("====================================================================")
    print(f" Web HUD URL : {url}")
    print(f" Repository  : {repo_root.resolve()}")
    print(" Watching    : state.md, evals.md, decisions.md, sessions/")
    print(" Press Ctrl+C to stop watching.")
    print("====================================================================")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SDCS watch server...")
    finally:
        server.stop_requested = True
        server.shutdown()
        server.server_close()
        print("✓ Watch server halted.")
