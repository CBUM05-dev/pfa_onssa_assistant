"""Serve the isolated ONSSA chat demo and proxy requests to the local FastAPI app."""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, request


class DemoHandler(SimpleHTTPRequestHandler):
    backend_url = "http://127.0.0.1:8000"

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._proxy("GET", "/health")
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/rag/answer":
            self._proxy("POST", "/api/v1/rag/answer")
            return
        self.send_error(404, "Unknown demo endpoint")

    def _proxy(self, method: str, backend_path: str) -> None:
        body = None
        if method == "POST":
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)

        headers = {"Content-Type": self.headers.get("Content-Type", "application/json")}
        proxied = request.Request(
            f"{self.backend_url}{backend_path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with request.urlopen(proxied, timeout=180) as response:
                payload = response.read()
                self.send_response(response.status)
                self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                self.end_headers()
                self.wfile.write(payload)
        except error.HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            self.send_header("Content-Type", exc.headers.get("Content-Type", "application/json"))
            self.end_headers()
            self.wfile.write(payload)
        except error.URLError as exc:
            payload = json.dumps({"detail": f"Backend unavailable: {exc.reason}"}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the isolated ONSSA chat demo.")
    parser.add_argument("--port", type=int, default=5500)
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    demo_dir = Path(__file__).resolve().parent
    DemoHandler.backend_url = args.backend_url.rstrip("/")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), DemoHandler)
    print(f"Demo: http://127.0.0.1:{args.port}")
    print(f"Backend: {DemoHandler.backend_url}")
    try:
        import os

        os.chdir(demo_dir)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping demo server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
