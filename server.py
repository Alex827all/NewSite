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
    print("write_storage ", data)
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
        print("Post request")
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._json_response({"error": "invalid JSON"}, 400)
            return

        # Проверка на логин через nick и password
        if isinstance(data, dict) and "nick" in data and "password" in data:
            store = read_storage()
            for user_id, user_data in store.items():
                if isinstance(user_data, dict):
                    if user_data.get("password") == data["password"]:
                        player_stat = user_data.get("playerStat", {})
                        if player_stat.get("nick") == data["nick"]:
                            print("user_id search ", user_id)
                            self._json_response({
                                "id": user_id,
                                "data": user_data
                            })
                            return
            self._json_response({"error": "совпадений не найдено"}, 403)
            return

        store = read_storage()

        # Обычное поведение
        if isinstance(data, dict):
            print("store.update(data)")
            store.update(data)
        else:
            key = uuid.uuid4().hex[:8]
            store[key] = data

        write_storage(store)
        self._json_response({"status": "ok", "size": len(store)})

    def do_GET(self):
        self._json_response(read_storage())

    def do_DELETE(self):
        path_parts = urlparse(self.path).path.strip("/").split("/")

        if not path_parts or not path_parts[0]:
            self._json_response({"error": "missing key"}, 400)
            return

        store = read_storage()
        current = store

        # Навигация до предпоследнего уровня
        for key in path_parts[:-1]:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                self._json_response(
                    {"error": f"key path not found: {'/'.join(path_parts)}"},
                    404)
                return

        last_key = path_parts[-1]
        if isinstance(current, dict) and last_key in current:
            del current[last_key]
            write_storage(store)
            self._json_response({
                "status": "deleted",
                "path": "/".join(path_parts)
            })
        else:
            self._json_response({"error": "final key not found"}, 404)

    def do_PUT(self):
        path_parts = urlparse(self.path).path.strip("/").split("/")
        if not path_parts or not path_parts[0]:
            self._json_response({"error": "missing key"}, 400)
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        try:
            value = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._json_response({"error": "invalid JSON"}, 400)
            return

        store = read_storage()
        current = store

        # Переход по ключам
        for key in path_parts[:-1]:
            current = current.setdefault(key, {})

        last_key = path_parts[-1]
        target = current.setdefault(last_key, {})

        if isinstance(target, dict) and isinstance(value, dict):
            target.update(value)
            write_storage(store)
            self._json_response({
                "status": "partial update",
                "path": "/".join(path_parts)
            })
        else:
            self._json_response(
                {"error": "invalid structure for partial update"}, 400)


# --- Запуск сервера ---

if __name__ == "__main__":
    ensure_storage_file()
    print(f"\U0001F680 Server running at http://localhost:{PORT}")
    HTTPServer((HOST, PORT), KVHandler).serve_forever()
