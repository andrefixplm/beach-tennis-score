#!/usr/bin/env python3
"""Tennis Scorer Proxy — serves React frontend + routes API to FastAPI backend"""

import http.server, json, socketserver, urllib.request, urllib.error, mimetypes
from pathlib import Path

FRONTEND_DIR = Path(__file__).parent / "dist"
API_PORT = 5176
API_HOST = "127.0.0.1"

# Fix MIME types for modern web
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("font/woff2", ".woff2")

class TennisProxy(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.proxy_request("GET")
        else:
            self.serve_static()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self.proxy_request("POST")
        else:
            self.serve_static()

    def do_DELETE(self):
        if self.path.startswith("/api/"):
            self.proxy_request("DELETE")
        else:
            self.serve_static()

    def serve_static(self):
        """Serve static files from dist/ with correct MIME types"""
        # Remove leading slash and resolve path
        path = self.path.split("?")[0]
        if path == "/":
            path = "/index.html"
        
        file_path = FRONTEND_DIR / path.lstrip("/")
        
        if file_path.is_dir():
            file_path = file_path / "index.html"
        
        if not file_path.exists():
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"detail": "Not found"}).encode())
            return
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "application/octet-stream"
        
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", file_path.stat().st_size)
        self.send_header("Cache-Control", "public, max-age=0, must-revalidate")
        self.end_headers()
        
        with open(file_path, "rb") as f:
            self.wfile.write(f.read())

    def proxy_request(self, method: str):
        body = None
        if method in ("POST", "PUT", "PATCH"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

        headers = dict(self.headers)
        headers["Host"] = f"{API_HOST}:{API_PORT}"
        headers.pop("Origin", None)
        headers.pop("Referer", None)

        url = f"http://{API_HOST}:{API_PORT}{self.path}"
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=10) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding", "connection", "content-length"):
                        self.send_header(k, v)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"detail": str(e)}).encode())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"detail": str(e)}).encode())

    def log_message(self, format, *args):
        pass  # silent

PORT = 5175

print(f"Tennis Scorer starting...")
print(f"  Frontend: http://0.0.0.0:{PORT}/  (dist: {FRONTEND_DIR})")
print(f"  API:      http://0.0.0.0:{PORT}/api/* → http://{API_HOST}:{API_PORT}/api/*")

with socketserver.ThreadingTCPServer(("", PORT), TennisProxy) as httpd:
    print(f"  Proxy:    http://0.0.0.0:{PORT}")
    httpd.serve_forever()