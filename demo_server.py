"""Serve a one-page demo dashboard for the Day 14 evaluation pipeline.

Uses only the Python standard library. Reads artifacts from disk on each request
so re-running evaluate_answers.py refreshes the demo without restarting.

Usage:
    python demo_server.py
    python demo_server.py --port 8765 --host 127.0.0.1
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DEMO_DIR = ROOT / "demo"
ARTIFACTS = ROOT / "artifacts"


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {"error": f"Missing file: {path.name}", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


class DemoHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        print(f"[demo] {args[0]}")

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        if path in {"/", "/index.html"}:
            html = (DEMO_DIR / "index.html").read_bytes()
            self._send(200, html, "text/html; charset=utf-8")
            return

        if path == "/api/overview":
            golden = _read_json(ROOT / "golden_dataset.json")
            benchmark = _read_json(ARTIFACTS / "benchmark_results.json")
            actual = _read_json(ARTIFACTS / "actual_answers.json")
            payload = {
                "golden": {
                    "corpus_id": golden.get("corpus_id"),
                    "qa_count": len(golden.get("qa_pairs", [])),
                    "difficulties": _count_difficulty(golden.get("qa_pairs", [])),
                },
                "actual": {
                    "answer_count": len(actual.get("answers", [])),
                    "agent": actual.get("agent"),
                    "generated_at": actual.get("generated_at"),
                },
                "benchmark": benchmark,
            }
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return

        if path == "/api/case":
            qs = parse_qs(urlparse(self.path).query)
            case_id = (qs.get("id") or [""])[0]
            body = json.dumps(_case_detail(case_id), ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return

        # static assets under demo/
        rel = path.lstrip("/")
        candidate = (DEMO_DIR / rel).resolve()
        if candidate.is_file() and DEMO_DIR.resolve() in candidate.parents:
            data = candidate.read_bytes()
            ctype = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
            self._send(200, data, ctype)
            return

        self._send(404, b'{"error":"not found"}', "application/json")


def _count_difficulty(pairs: list) -> dict[str, int]:
    counts: dict[str, int] = {}
    for pair in pairs:
        if isinstance(pair, dict):
            key = str(pair.get("difficulty") or "unknown")
            counts[key] = counts.get(key, 0) + 1
    return counts


def _case_detail(case_id: str) -> dict:
    golden = _read_json(ROOT / "golden_dataset.json")
    actual = _read_json(ARTIFACTS / "actual_answers.json")
    benchmark = _read_json(ARTIFACTS / "benchmark_results.json")

    g = next((p for p in golden.get("qa_pairs", []) if p.get("id") == case_id), None)
    a = next((p for p in actual.get("answers", []) if p.get("id") == case_id), None)
    r = next((p for p in benchmark.get("results", []) if p.get("id") == case_id), None)
    if not g:
        return {"error": f"Unknown case id: {case_id}"}
    return {"golden": g, "actual": a, "result": r}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not (DEMO_DIR / "index.html").is_file():
        print(f"ERROR: missing {DEMO_DIR / 'index.html'}")
        return 2

    server = ThreadingHTTPServer((args.host, args.port), DemoHandler)
    url = f"http://{args.host}:{args.port}/"
    print("=" * 56)
    print("  Northstar Eval Demo")
    print(f"  Open: {url}")
    print("  Stop: Ctrl+C")
    print("=" * 56)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[demo] stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
