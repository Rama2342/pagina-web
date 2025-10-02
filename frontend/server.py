#!/usr/bin/env python3
"""
Servidor HTTP simple para servir archivos estáticos del frontend.
Maneja errores de conexión abortada por el cliente.
"""

import http.server
import socketserver
import logging
import os
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('frontend_server.log'),  # Log en archivo
        logging.StreamHandler()  # También en consola
    ]
)
logger = logging.getLogger(__name__)

# Directorio base para servir archivos (ajusta según tu estructura)
BASE_DIR = Path(__file__).parent
PORT = 8000  # Puerto para el frontend (diferente al backend en 5000)

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Handler personalizado que maneja errores de conexión abortada.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, format_str, *args):
        """Redirige los logs del servidor a nuestro logger."""
        logger.info(f"{self.address_string()} - - [{self.log_date_time_string()}] {format_str % args}")

    def do_GET(self):
        """
        Maneja solicitudes GET con try-except para capturar ConnectionAbortedError.
        """
        try:
            # Llama al método padre (servir archivo estático)
            return super().do_GET()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
            # Cliente cerró la conexión prematuramente (normal en web)
            logger.warning(f"Conexión abortada por el cliente: {e} (IP: {self.client_address[0]})")
        except Exception as e:
            # Otros errores inesperados
            logger.error(f"Error inesperado en do_GET: {e}", exc_info=True)
            # Envía una respuesta de error 500 si es posible
            try:
                self.send_error(500, f"Error interno del servidor: {str(e)}")
            except:
                pass  # Si la conexión ya está rota, ignora

    def do_POST(self):
        """
        Si necesitas manejar POST (por ejemplo, para uploads), agrega aquí.
        Por ahora, redirige a 405 (Method Not Allowed) para simplicidad.
        """
        try:
            self.send_error(405, "Method Not Allowed")
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            logger.warning(f"Conexión abortada en do_POST: {self.client_address[0]}")

class CustomTCPServer(socketserver.TCPServer):
    """
    Servidor TCP personalizado que permite reutilizar el puerto.
    """
    allow_reuse_address = True

def run_frontend_server():
    """
    Inicia el servidor del frontend.
    """
    try:
        # Crea el servidor con el handler personalizado
        with CustomTCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            logger.info(f"Servidor del frontend iniciado en http://localhost:{PORT}")
            logger.info(f"Sirviendo archivos desde: {BASE_DIR}")
            logger.info("Presiona Ctrl+C para detener.")
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Servidor del frontend detenido por el usuario.")
    except Exception as e:
        logger.error(f"Error al iniciar el servidor del frontend: {e}", exc_info=True)

if __name__ == "__main__":
    run_frontend_server()