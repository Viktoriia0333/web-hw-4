import json
import mimetypes
import os
import threading
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import pathlib
import socket
from time import sleep

STORAGE_DIR = 'storage'
FILE_PATH = os.path.join(STORAGE_DIR, 'data.json')


class httpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url_path = urllib.parse.urlparse(self.path)
        if url_path.path == '/':
            self.send_html_file('index.html')
        elif url_path.path == '/message.html':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(url_path.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        print(data_dict)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(json.dumps(data_dict).encode(), ("127.0.0.1", 5000))
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, file, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(file, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run():
    server_address = ('', 3000)
    http = HTTPServer(server_address, httpHandler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def start_server(host='127.0.0.1', port=5000):
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind((host, port))
        while True:
            data, addr = server.recvfrom(1024)
            try:
                data_dict = json.loads(data.decode())
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

                entry = {
                    "username": data_dict.get("username", ""),
                    "message": data_dict.get("message", "")
                }

                existing = {}
                if os.path.exists(FILE_PATH):
                    with open(FILE_PATH, 'r') as f:
                        try:
                            existing = json.load(f)
                        except json.JSONDecodeError:
                            existing = {}

                existing[timestamp] = entry

                with open(FILE_PATH, 'w') as f:
                    json.dump(existing, f, indent=2, ensure_ascii=False)

            except Exception as e:
                print(f"Error: {e}")


if __name__ == '__main__':
    socket_thread = threading.Thread(target=start_server, daemon=True)
    socket_thread.start()
    run()
