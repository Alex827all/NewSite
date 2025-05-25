#!/usr/bin/env python3
"""
Простейшее key-value JSON-хранилище.

 • POST   /        → добавляет/обновляет записи (JSON)
 • GET    /        → отдаёт весь словарь
 • DELETE /<key>   → удаляет запись по ключу

Подходит для Replit/Railway: порт берётся из env «PORT».
"""

import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8080))
DATA_FILE = "data.json"


# ---------- вспомогательные функции ----------

def ensure_storage_file() -> None:
    """Создать файл-хранилище, если его нет (пустой словарь)."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False)


def read_storage() -> dict:
    """Прочитать словарь из файла; вернуть {} при ошибке."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            return json.loads(raw) if raw else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_storage(data: dict) -> None:
    """Перезаписать файл новым содержимым."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- HTTP-обработчик ----------

class KVHandler(BaseHTTPRequestHandler):
    def _json_response(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ======== POST / ========
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        try:
            incoming = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._json_response({"error": "invalid JSON"}, 400)
            return

        store = read_storage()

        if isinstance(incoming, dict):
            # Сливаем пришедший объект со словарём-хранилищем
            store.update(incoming)
        else:
            # Кладём под случайным коротким ключом
            store[uuid.uuid4().hex[:8]] = incoming

        write_storage(store)
        self._json_response({"status": "ok", "size": len(store)})

    # ======== GET / ========
    def do_GET(self):
        self._json_response(read_storage())

    # ======== DELETE /<key> ========
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


# ---------- точка входа ----------

if __name__ == "__main__":
    ensure_storage_file()
    print(f"🚀 Server running at http://localhost:{PORT}")
    HTTPServer((HOST, PORT), KVHandler).serve_forever()
