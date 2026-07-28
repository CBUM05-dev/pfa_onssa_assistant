"""Serve the isolated ONSSA chat demo and proxy requests to the local FastAPI app."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, request


class DemoHandler(SimpleHTTPRequestHandler):
    backend_url = "http://127.0.0.1:8000"
    images_dir: Path | None = None

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._proxy("GET", "/health")
            return
        if self.path.startswith("/images/"):
            self._serve_image()
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

    def _serve_image(self) -> None:
        if self.images_dir is None:
            self.send_error(404, "Images directory is not configured")
            return

        image_name = Path(self.path.removeprefix("/images/")).name
        image_path = (self.images_dir / image_name).resolve()
        images_root = self.images_dir.resolve()
        if images_root not in image_path.parents or not image_path.is_file():
            self.send_error(404, "Image not found")
            return

        content_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
        payload = image_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the isolated ONSSA chat demo.")
    parser.add_argument("--port", type=int, default=5500)
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    demo_dir = Path(__file__).resolve().parent
    project_root = demo_dir.parents[1]
    DemoHandler.backend_url = args.backend_url.rstrip("/")
    DemoHandler.images_dir = project_root / "IMAGES_ONSSA"
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
