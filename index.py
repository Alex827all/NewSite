import os
import json
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# Настройки
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', 8080))
DATA_FILE = 'data.json'

# Убедимся, что файл существует
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f, ensure_ascii=False)

class SimpleRequestHandler(BaseHTTPRequestHandler):
    def load_data(self):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_data(self, data):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            new_entry = json.loads(post_data.decode('utf-8'))

            data = self.load_data()
            new_id = uuid.uuid4().hex[:8]  # генерируем короткий уникальный ID
            data[new_id] = new_entry
            self.save_data(data)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "id": new_id}).encode('utf-8'))

        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid JSON\n')

    def do_GET(self):
        data = self.load_data()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))

    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        key = parsed_path.path.strip('/')

        if not key:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Missing key in URL\n')
            return

        data = self.load_data()

        if key in data:
            del data[key]
            self.save_data(data)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f'Deleted entry with key: {key}\n'.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Key not found\n')

# Запуск сервера
if __name__ == '__main__':
    print(f"Server running at http://localhost:{PORT}")
    server = HTTPServer((HOST, PORT), SimpleRequestHandler)
    server.serve_forever()
