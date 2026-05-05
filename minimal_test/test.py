from http.server import BaseHTTPRequestHandler, HTTPServer
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>✅ Minimal test works!</h1><p>PythonAnywhere WSGI is functional.</p>')
def run(): httpd = HTTPServer(('0.0.0.0', 8000), Handler); httpd.serve_forever()
if __name__ == '__main__': run()
