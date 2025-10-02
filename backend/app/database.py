from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
import sqlite3
import os
import logging
from werkzeug.security import generate_password_hash # Importar para crear contraseñas

# Configurar logging
logger = logging.getLogger(__name__)

# Inicializar SQLAlchemy
db = SQLAlchemy()

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Asegura que las claves foráneas estén habilitadas para SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        logger.debug("PRAGMA foreign_keys=ON ejecutado para la conexión SQLite.")

def init_app(app):
    """
    Inicializa la base de datos con la aplicación Flask.
    Crea las tablas si no existen y un usuario admin por defecto.
    """
    db.init_app(app)
    
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_path)
            
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Directorio de base de datos creado: {db_dir}")
        
        try:
            # Importar modelos aquí para asegurar que se registren
            from .models import User, Student
            logger.info("Modelos importados correctamente para la creación de tablas.")
            
            db.create_all()
            logger.info("Tablas de la base de datos creadas exitosamente (si no existían).")
            
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Tablas existentes en la base de datos: {tables}")
            
            # Crear usuario admin por defecto si no existe
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(username='admin', email='admin@sanisidro.edu', is_admin=True)
                admin_user.set_password('admin123') # Contraseña por defecto para el admin
                db.session.add(admin_user)
                db.session.commit()
                logger.info("Usuario administrador creado: admin / admin123")
            else:
                logger.info("Usuario administrador 'admin' ya existe.")
            
        except Exception as e:
            logger.error(f"Error al crear tablas o usuario admin usando SQLAlchemy: {e}", exc_info=True)
            # Fallback para crear tablas manualmente si SQLAlchemy falla (útil en algunos entornos)
            try:
                if db_uri.startswith('sqlite:///'):
                    db_path = db_uri.replace('sqlite:///', '')
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
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
                    
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS students (
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
                    
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_student_id ON users (student_id)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_username ON students (username)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_email ON students (email)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_dni ON students (dni)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_matricula ON students (matricula)')
                    
                    try:
                        password_hash = generate_password_hash('admin123')
                        cursor.execute(
                            'INSERT OR IGNORE INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                            ('admin', 'admin@sanisidro.edu', password_hash, True)
                        )
                    except Exception as insert_e:
                        logger.warning(f"Error al insertar admin en fallback manual: {insert_e}")
                    
                    conn.commit()
                    conn.close()
                    logger.info("Tablas 'users' y 'students' creadas manualmente (fallback).")
                    
            except Exception as manual_error:
                logger.critical(f"Error CRÍTICO al crear tablas manualmente: {manual_error}", exc_info=True)
