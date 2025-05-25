import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8080))
DATA_FILE = "data.json"

# --- Утилиты для работы с файлом ---

def ensure_storage_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False)


def read_storage() -> dict:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except Exception:
        return {}


def write_storage(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- HTTP обработчик ---

class KVHandler(BaseHTTPRequestHandler):
    def _json_response(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._json_response({"error": "invalid JSON"}, 400)
            return

        store = read_storage()

        if isinstance(data, dict):
            store.update(data)
        else:
            key = uuid.uuid4().hex[:8]
            store[key] = data

        write_storage(store)
        self._json_response({"status": "ok", "size": len(store)})

    def do_GET(self):
        self._json_response(read_storage())

    def do_DELETE(self):
        key = urlparse(self.path).path.lstrip("/")
        if not key:
            self._json_response({"error": "missing key"}, 400)
            return

        store = read_storage()
        if key in store:
            del store[key]
            write_storage(store)
            self._json_response({"status": "deleted", "key": key})
        else:
            self._json_response({"error": "key not found"}, 404)


# --- Запуск сервера ---

if __name__ == "__main__":
    ensure_storage_file()
    print(f"🚀 Server running at http://localhost:{PORT}")
    HTTPServer((HOST, PORT), KVHandler).serve_forever()
