from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from backend import Backend
from pool import ServerPool

class LoadBalancer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.health_check()
            return

        try:
            backend = pool.get_next_backend()
            response = backend.proxy_request(
                self.command,
                self.path,
                headers=self.headers,
                data=self.rfile.read(int(self.headers.get('Content-Length', 0)))
            )
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)
        except ConnectionError:
            self.send_error(503, "Service Unavailable")
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {e}")

    def do_POST(self):
        self.do_GET()

    def health_check(self):
        for backend in pool.backends:
            backend.health_check()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Health checks performed.")

backends = [Backend(url="http://localhost:8081"), Backend(url="http://localhost:8082")]
pool = ServerPool(backends=backends)

def main():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, LoadBalancer)
    print(f"Load balancer running on port {server_address[1]}...")
    httpd.serve_forever()

if __name__ == '__main__':
    main()
