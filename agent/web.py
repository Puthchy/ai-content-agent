"""Local web interface: edit the channel config, start runs, watch progress, browse clips."""

import json
import threading
import traceback
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import yaml

from .config import OUTPUT_DIR, ROOT, load_settings
from .pipeline import build_pipeline

STATIC_DIR = Path(__file__).resolve().parent / "static"
CONFIG_PATH = ROOT / "config.yaml"
MIME = {".mp4": "video/mp4", ".mp3": "audio/mpeg", ".png": "image/png", ".json": "application/json",
        ".srt": "text/plain; charset=utf-8", ".txt": "text/plain; charset=utf-8",
        ".html": "text/html; charset=utf-8"}


class Job:
    """At most one generation run at a time; the UI polls its log."""

    def __init__(self):
        self.lock = threading.Lock()
        self.running = False
        self.logs: list[str] = []
        self.error: str | None = None

    def log(self, line: str) -> None:
        self.logs.append(f"{datetime.now():%H:%M:%S}  {line}")

    def start(self, count: int, dry_run: bool) -> bool:
        with self.lock:
            if self.running:
                return False
            self.running, self.logs, self.error = True, [], None
        threading.Thread(target=self._run, args=(count, dry_run), daemon=True).start()
        return True

    def _run(self, count: int, dry_run: bool) -> None:
        try:
            pipeline = build_pipeline(load_settings(), dry_run, self.log)
            for i in range(count):
                self.log(f"— คลิป {i + 1}/{count} —")
                pipeline.make_clip()
            self.log("เสร็จทั้งหมด")
        except Exception as e:  # surface every failure in the UI instead of killing the thread silently
            self.error = str(e)
            self.log(f"ผิดพลาด: {e}")
            traceback.print_exc()
        finally:
            self.running = False

    def state(self) -> dict:
        return {"running": self.running, "logs": self.logs, "error": self.error}


JOB = Job()


def list_clips() -> list[dict]:
    clips = []
    for d in sorted(OUTPUT_DIR.glob("*/"), reverse=True):
        # post.txt is written last, so its presence means the clip is finished.
        if not (d / "post.txt").exists():
            continue
        script = json.loads((d / "script.json").read_text(encoding="utf-8")) if (d / "script.json").exists() else {}
        post = (d / "post.txt").read_text(encoding="utf-8")
        clips.append({"id": d.name, "title": script.get("title", d.name), "post": post,
                      "scenes": script.get("scenes", [])})
    return clips


def key_status() -> dict:
    s = load_settings()
    return {"anthropic": bool(s.anthropic_key),
            "elevenlabs": bool(s.elevenlabs_key and s.elevenlabs_voice),
            "affiliate_links": len(s.affiliate_links)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json(self, data, status=HTTPStatus.OK):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def _file(self, path: Path):
        size = path.stat().st_size
        start, end = 0, size - 1
        # <video> seeking needs byte ranges.
        rng = self.headers.get("Range")
        if rng and rng.startswith("bytes="):
            a, _, b = rng[6:].partition("-")
            start = int(a) if a else max(size - int(b), 0)
            end = int(b) if a and b else size - 1
        length = end - start + 1
        self.send_response(HTTPStatus.PARTIAL_CONTENT if rng else HTTPStatus.OK)
        self.send_header("Content-Type", MIME.get(path.suffix, "application/octet-stream"))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if rng:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        with path.open("rb") as f:
            f.seek(start)
            self.wfile.write(f.read(length))

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path == "/":
            return self._file(STATIC_DIR / "index.html")
        if path == "/api/config":
            return self._json(yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")))
        if path == "/api/status":
            return self._json({**key_status(), "job": JOB.state()})
        if path == "/api/clips":
            return self._json(list_clips())
        if path.startswith("/files/"):
            target = (OUTPUT_DIR / path[len("/files/"):]).resolve()
            if target.is_file() and OUTPUT_DIR.resolve() in target.parents:
                return self._file(target)
        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/config":
            CONFIG_PATH.write_text(yaml.safe_dump(self._body(), allow_unicode=True, sort_keys=False),
                                   encoding="utf-8")
            return self._json({"ok": True})
        if path == "/api/run":
            body = self._body()
            count = max(1, min(int(body.get("count", 1)), 20))
            if not JOB.start(count, bool(body.get("dry_run"))):
                return self._json({"error": "กำลังทำคลิปอยู่ รอให้เสร็จก่อน"}, HTTPStatus.CONFLICT)
            return self._json({"ok": True})
        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)


def serve(host: str, port: int) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"เปิดหน้าเว็บที่ http://{host}:{port}  (กด Ctrl+C เพื่อปิด)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
