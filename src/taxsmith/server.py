"""Local development server for the Taxsmith workflow UI and agent API."""

from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from taxsmith.agent import analyze_question
from taxsmith.schemas import TaxQuery


ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "site"


class TaxsmithHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE_DIR), **kwargs)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/analyze":
            self.send_error(404, "Unknown endpoint")
            return

        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, status=400)
            return

        text = str(payload.get("text", "")).strip()
        if not text:
            self._send_json({"error": "Question text is required"}, status=400)
            return

        query = TaxQuery(
            text=text,
            tax_year=payload.get("tax_year"),
            province=payload.get("province"),
            taxpayer_type=payload.get("taxpayer_type"),
        )
        result = analyze_question(
            query,
            use_ollama=bool(payload.get("use_ollama")),
            ollama_base_url=str(payload.get("ollama_base_url") or "http://127.0.0.1:11434"),
            ollama_model=str(payload.get("ollama_model") or "qwen3"),
        )
        self._send_json(result)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(host: str = "127.0.0.1", port: int = 8766) -> None:
    server = ThreadingHTTPServer((host, port), TaxsmithHandler)
    print(f"Taxsmith running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
