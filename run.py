import subprocess
import sys
import os
import time
from threading import Thread

def run_backend():
    """Ejecuta el servidor backend en puerto 5000"""
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    subprocess.run([sys.executable, 'main.py'])

def run_frontend():
    """Ejecuta el servidor frontend en puerto 3000"""
    # Esperar un momento para que el backend inicie primero
    time.sleep(2)
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    os.chdir(frontend_dir)
    subprocess.run([sys.executable, 'server.py'])

if __name__ == '__main__':
    print("Iniciando ambos servidores...")
    print("Backend: http://localhost:5000")
    print("Frontend: http://localhost:3000")
    
    # Crear hilos para ejecutar ambos servidores
    backend_thread = Thread(target=run_backend)
    frontend_thread = Thread(target=run_frontend)
    
    backend_thread.start()
    frontend_thread.start()
    
    backend_thread.join()
    frontend_thread.join()