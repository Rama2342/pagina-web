import subprocess
import sys
import os
import time
from threading import Thread
import signal
import socket

def is_port_in_use(port):
    """Verificar si un puerto está en uso"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except socket.error:
            return True

def kill_process_on_port(port):
    """Matar proceso usando un puerto específico"""
    try:
        # Linux/Mac
        result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    subprocess.run(['kill', '-9', pid])
                    print(f"✅ Proceso {pid} en puerto {port} terminado")
    except:
        try:
            # Windows
            subprocess.run(['npx', 'kill-port', str(port)])
        except:
            print(f"⚠️  No se pudo liberar el puerto {port}")

def run_backend():
    """Ejecuta el servidor backend en puerto 5000"""
    print("Iniciando backend...")
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    # Liberar puerto si está ocupado
    if is_port_in_use(5000):
        print("🔄 Liberando puerto 5000...")
        kill_process_on_port(5000)
        time.sleep(2)
    
    try:
        subprocess.run([sys.executable, 'main.py'])
    except KeyboardInterrupt:
        print("\nBackend detenido")

def run_frontend():
    """Ejecuta el servidor frontend"""
    print("Iniciando frontend...")
    time.sleep(3)  # Esperar a que el backend inicie
    
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    os.chdir(frontend_dir)
    
    # Liberar puerto si está ocupado
    if is_port_in_use(3000):
        print("Liberando puerto 3000...")
        kill_process_on_port(3000)
        time.sleep(2)
    
    try:
        subprocess.run([sys.executable, 'server.py'])
    except KeyboardInterrupt:
        print("\nFrontend detenido")

def main():
    print("=" * 60)
    print("COLEGIO SAN ISIDRO - SISTEMA DE GESTIÓN")
    print("=" * 60)
    
    # Verificar que las carpetas existan
    if not os.path.exists('backend'):
        print("Error: No se encuentra la carpeta 'backend'")
        return
    
    if not os.path.exists('frontend'):
        print("Error: No se encuentra la carpeta 'frontend'")
        return
    
    print("Estructura de carpetas verificada")
    print("Iniciando servidores...")
    
    # Crear hilos para ejecutar ambos servidores
    backend_thread = Thread(target=run_backend)
    frontend_thread = Thread(target=run_frontend)
    
    # Configurar manejo de Ctrl+C
    def signal_handler(sig, frame):
        print("\n Deteniendo servidores...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    backend_thread.start()
    frontend_thread.start()
    
    try:
        backend_thread.join()
        frontend_thread.join()
    except KeyboardInterrupt:
        print("\n Aplicación detenida por el usuario")

if __name__ == '__main__':
    main()