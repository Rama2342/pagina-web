import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parsear la URL
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Manejar rutas de la API - redirigir al backend
        if path.startswith('/api/'):
            self.send_response(302)
            self.send_header('Location', f'http://localhost:5000{path}')
            self.end_headers()
            return
        
        # Servir archivos específicos para cada ruta
        if path == '/':
            self.path = '/index.html'
        elif path == '/login':
            self.path = '/login.html'
        elif path == '/register':
            self.path = '/register.html'
        elif path == '/dashboard':
            self.path = '/dashboard.html'
        elif not '.' in path.split('/')[-1]:
            # Si es una ruta sin extensión, servir index.html
            self.path = '/index.html'
        
        # Servir el archivo estático
        return super().do_GET()
    
    def end_headers(self):
        # Agregar headers CORS para desarrollo
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:5000')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Manejar preflight requests para CORS
        self.send_response(200)
        self.end_headers()

def run_server():
    # Cambiar al directorio frontend
    frontend_dir = os.path.join(os.path.dirname(__file__))
    os.chdir(frontend_dir)
    
    PORT = 3000
    Handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("=" * 50)
        print("Frontend iniciado correctamente!")
        print("Frontend disponible en: http://localhost:3000")
        print("Páginas:")
        print("  - http://localhost:3000/ (Inicio)")
        print("  - http://localhost:3000/login (Iniciar sesión)")
        print("  - http://localhost:3000/register (Registrarse)")
        print("  - http://localhost:3000/dashboard (Panel de control)")
        print("=" * 50)
        print("Presiona Ctrl+C para detener el servidor")
        httpd.serve_forever()

if __name__ == '__main__':
    run_server()