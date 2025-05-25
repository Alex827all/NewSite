#!/usr/bin/env python3
"""
Простой JSON-хранилище:
  • POST /    → сохраняет присланный JSON в data.json (добавляет в конец списка)
  • GET  /    → отдаёт весь список из data.json
Работает и локально, и на Replit/Railway/Render — порт берётся из env-переменной PORT.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8080))      # ➜ 8080 локально, динамический онлайн
DATA_FILE = "data.json"


def init_storage() -> None:
    """Создаём data.json, если его ещё нет (пустой список [])."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump("file", f, ensure_ascii=False)


def load_all() -> list:
    """Читает весь список записей (или возвращает пустой)."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def append_entry(entry: dict) -> None:
    """Добавляет новую запись в конец списка и перезаписывает файл."""
    data = load_all()
    data.append(entry)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class SimpleAPI(BaseHTTPRequestHandler):
    def _json_response(self, payload, status=200):
        payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(payload_bytes)

    # -------- POST / --------
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        try:
            entry = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._json_response({"error": "Invalid JSON"}, status=400)
            return

        append_entry(entry)
        self._json_response({"status": "saved"})

    # -------- GET / --------
    def do_GET(self):
        self._json_response(load_all())


if __name__ == "__main__":
    init_storage()
    print(f"🚀 Server running at http://localhost:{PORT}")
    HTTPServer((HOST, PORT), SimpleAPI).serve_forever()
