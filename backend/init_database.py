# FileName: /pagina-web-main/backend/init_database.py
#!/usr/bin/env python3
import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def init_database():
    logger.info("=== INICIALIZACIÓN COMPLETA DE LA BASE DE DATOS ===")

    instance_dir = 'instance'
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        logger.info(f"Directorio creado: {instance_dir}")

    db_path = os.path.join(instance_dir, 'app.db')

    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info(f"Base de datos anterior eliminada: {db_path}")

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
        admin_password_hash = generate_password_hash('admin123') # Contraseña por defecto para el admin
        cursor.execute(
            'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
            ('admin', 'admin@sanisidro.edu', admin_password_hash, 1)
        )

        logger.info("Creando usuarios de prueba...")
        test_users = [
            ('juanperez', 'juan@sanisidro.edu', generate_password_hash('password123'), 0),
            ('mariagomez', 'maria@sanisidro.edu', generate_password_hash('password123'), 0),
            ('profesor1', 'profesor@sanisidro.edu', generate_password_hash('password123'), 0)
        ]

        for username, email, pwd_hash, is_admin in test_users:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                (username, email, pwd_hash, is_admin)
            )

        conn.commit()

        logger.info("Verificando la estructura...")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        logger.info("\n=== ESTRUCTURA DE LA TABLA users ===")
        for col in columns:
            logger.info(f"  {col[1]} ({col[2]})")

        cursor.execute("SELECT username, email, is_admin, student_id FROM users")
        users = cursor.fetchall()
        logger.info("\n=== USUARIOS EN LA BASE DE DATOS ===")
        for user in users:
            logger.info(f"  {user[0]} ({user[1]}) - Admin: {'Sí' if user[2] else 'No'} - Student ID: {user[3]}")

        conn.close()

        logger.info(f"\n¡Base de datos inicializada exitosamente en {db_path}!")
        logger.info("Usuario admin: admin / admin123")
        logger.info("Nota: Los usuarios de prueba no están vinculados a estudiantes por defecto.")

        return True

    except Exception as e:
        logger.critical(f"Error al inicializar la base de datos: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    logger.info("Este script creará una NUEVA base de datos con la estructura correcta.")
    confirm = input("¿Continuar? (s/n): ")
    if confirm.lower() == 's':
        success = init_database()
        if success:
            logger.info("\n¡Base de datos lista! Ahora ejecuta: python main.py")
        else:
            logger.error("\nError al crear la base de datos.")
    else:
        logger.info("Operación cancelada.")
