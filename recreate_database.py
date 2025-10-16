import os
import sys
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def recreate_database():
    logger.info("=== RECREANDO BASE DE DATOS COMPLETAMENTE ===")
    
    db_path = 'instance/app.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info(f"Base de datos eliminada: {db_path}")
    
    instance_dir = 'instance'
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        logger.info(f"Directorio creado: {instance_dir}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("Creando tabla users...")
        cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(64) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_admin BOOLEAN DEFAULT FALSE,
            student_id INTEGER UNIQUE,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
        ''')
        
        logger.info("Creando tabla students...")
        cursor.execute('''
        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dni VARCHAR(20) UNIQUE NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            apellido VARCHAR(100) NOT NULL,
            username VARCHAR(64) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            grado VARCHAR(20) NOT NULL,
            seccion VARCHAR(10) NOT NULL,
            turno VARCHAR(20) NOT NULL,
            especialidad VARCHAR(100),
            matricula VARCHAR(50) UNIQUE NOT NULL,
            estado VARCHAR(50) DEFAULT 'Activo',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        logger.info("Creando índices...")
        cursor.execute('CREATE INDEX idx_users_username ON users (username)')
        cursor.execute('CREATE INDEX idx_users_email ON users (email)')
        cursor.execute('CREATE INDEX idx_users_student_id ON users (student_id)')
        cursor.execute('CREATE INDEX idx_students_username ON students (username)')
        cursor.execute('CREATE INDEX idx_students_email ON students (email)')
        cursor.execute('CREATE INDEX idx_students_dni ON students (dni)')
        cursor.execute('CREATE INDEX idx_students_matricula ON students (matricula)')
        
        logger.info("Creando usuario admin...")
        password_hash = generate_password_hash('Profesores2025')
        cursor.execute(
            'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
            ('admin', 'admin@sanisidro.edu', password_hash, True)
        )
        
        logger.info("Creando usuarios de prueba...")
        test_users = [
            ('juanperez', 'juan@sanisidro.edu', generate_password_hash('password123'), False),
            ('mariagomez', 'maria@sanisidro.edu', generate_password_hash('password123'), False),
            ('profesor1', 'profesor@sanisidro.edu', generate_password_hash('password123'), False)
        ]
        
        for username, email, pwd_hash, is_admin in test_users:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                (username, email, pwd_hash, is_admin)
            )
        
        conn.commit()
        conn.close()
        
        logger.info("Base de datos recreada exitosamente.")
        logger.info("Tabla users creada con columna is_admin y student_id.")
        logger.info("Usuario admin creado: admin / Profesores2025.")
        logger.info("Usuarios de prueba creados.")
        
    except Exception as e:
        logger.critical(f"Error al recrear la base de datos: {e}", exc_info=True)
        return False
    
    logger.info("Verificando que la base de datos se creó correctamente...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        logger.info("\n=== ESTRUCTURA DE LA TABLA users ===")
        for col in columns:
            logger.info(f"  {col[1]} ({col[2]})")
        
        cursor.execute("SELECT username, email, is_admin, student_id FROM users")
        users = cursor.fetchall()
        logger.info("\n=== USUARIOS EN LA BASE DE DATOS ===")
        for user in users:
            logger.info(f"  {user[0]} ({user[1]}) - Admin: {bool(user[2])} - Student ID: {user[3]}")
        
        conn.close()
        
    except Exception as e:
        logger.critical(f"Error al verificar la base de datos: {e}", exc_info=True)
        return False
    
    logger.info("\n¡Base de datos recreada exitosamente!")
    logger.info("Ahora puedes ejecutar: python main.py")
    return True

if __name__ == '__main__':
    confirm = input("¿Estás seguro de que quieres RECREAR COMPLETAMENTE la base de datos? (s/n): ")
    if confirm.lower() == 's':
        recreate_database()
    else:
        logger.info("Operación cancelada.")
