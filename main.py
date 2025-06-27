from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from backend import Backend
from pool import ServerPool

class LoadBalancer(BaseHTTPRequestHandler):
    """
    A simple HTTP load balancer that distributes incoming requests
    among a pool of backend servers using a round-robin algorithm.
    """
    def do_GET(self):
        """
        Handles GET requests by forwarding them to an available backend server.
        Also handles the /health endpoint for health checks.
        """
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
        """
        Handles POST requests by calling do_GET.
        """
        self.do_GET()

    def health_check(self):
        """
        Performs health checks on all registered backend servers.
        """
        for backend in pool.backends:
            backend.health_check()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Health checks performed.")

backends = [Backend(url="http://localhost:8081"), Backend(url="http://localhost:8082")]
pool = ServerPool(backends=backends)

def main():
    """
    Starts the load balancer server.
    """
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, LoadBalancer)
    print(f"Load balancer running on port {server_address[1]}...")
    httpd.serve_forever()

if __name__ == '__main__':
    main()
