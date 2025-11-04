# app_stdlib.py
import os, json, time
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen
from urllib.error import URLError

# --- Config via env vars ---
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/ai-chatbot")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))

# --- Zorg dat / het 'public' pad is ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
os.makedirs(PUBLIC_DIR, exist_ok=True)
os.chdir(PUBLIC_DIR)  # <- belangrijk: root van de webserver is nu ./public

ALIASES = {
    "/logo.png": "/emglogo.png",   # alles dat logo.png vraagt, krijgt emglogo.png
    "/favicon.ico": "/emglogo.png" # voorkomt favicon-404
}

class Handler(SimpleHTTPRequestHandler):
    # Kleinere en nettere logregels
    def log_message(self, fmt, *args):
        # Standaard schrijft SimpleHTTPRequestHandler naar stderr; wij doen print()
        print(f"{self.address_string()} - {self.command} {self.path} - " + (fmt % args))

    def do_OPTIONS(self):
        # CORS preflight: maak het makkelijk als je UI elders staat
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", os.environ.get("ALLOWED_ORIGINS", "*"))
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        self.end_headers()

    def do_POST(self):
        if self.path != "/ask":
            self.send_error(404, "Not Found")
            return

        start = time.time()
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"

        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self.send_response(400); self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        try:
            req = Request(
                N8N_WEBHOOK_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=60) as resp:
                body = resp.read()
                ctype = resp.headers.get("Content-Type", "application/json")
                self.send_response(resp.status)
                self.send_header("Content-Type", ctype)
                self.send_header("Access-Control-Allow-Origin", os.environ.get("ALLOWED_ORIGINS", "*"))
                self.end_headers()
                self.wfile.write(body)
        except URLError as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"Upstream error: {e}".encode("utf-8"))
        finally:
            dur = (time.time() - start) * 1000
            print(f"{self.client_address[0]} - POST /ask -> {N8N_WEBHOOK_URL} ({dur:.0f} ms)")

    def translate_path(self, path):
        # Alias voor bekende paden
        path = ALIASES.get(path, path)

        # vanaf hier je bestaande translate_path logic:
        from urllib.parse import unquote
        path = unquote(path.split('?',1)[0].split('#',1)[0])
        if path == "/": path = "/index.html"
        if path.startswith("/"): path = path[1:]
        import os
        fs_path = os.path.join(PUBLIC_DIR, os.path.normpath(path))
        print(f"[STATIC] URL '{self.path}' -> FS '{fs_path}' (exists={os.path.exists(fs_path)})")
        return fs_path

    def do_GET(self):
        # extra: als iemand /logo.png of /favicon.ico vraagt, log duidelijk de alias
        if self.path in ALIASES:
            print(f"[ALIAS] {self.path} -> {ALIASES[self.path]}")
        return super().do_GET()
    
# Start server
if __name__ == "__main__":
    print(f"Serving static files from: {PUBLIC_DIR}")
    print(f"n8n webhook: {N8N_WEBHOOK_URL}")
    print(f"→ http://{HOST}:{PORT}/  (CTRL+C to stop)")
    HTTPServer((HOST, PORT), Handler).serve_forever()
