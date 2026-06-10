import http.server
import socketserver
import os

PORT = int(os.environ.get("PORT", 7860))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>CMMS Electrique Test</h1><p>Python HTTP server OK!</p>")
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Test server on 0.0.0.0:{PORT}", flush=True)
    httpd.serve_forever()
