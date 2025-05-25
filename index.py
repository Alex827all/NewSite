from http.server import BaseHTTPRequestHandler, HTTPServer
import json

# Настройки сервера
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', 8080))  # порт задаётся окружением
DATA_FILE = 'data.json'

class SimpleRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Получаем длину данных
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            # Пытаемся прочитать как JSON
            data = json.loads(post_data.decode('utf-8'))

            # Сохраняем в файл
            with open(DATA_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Data saved\n')

        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid JSON\n')

    def do_GET(self):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'File not found\n')

# Запуск сервера
if __name__ == '__main__':
    server = HTTPServer((HOST, PORT), SimpleRequestHandler)
    print(f'Server running on http://{HOST}:{PORT}')
    server.serve_forever()

