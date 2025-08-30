from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
import sqlite3
import os

# Inicializar SQLAlchemy
db = SQLAlchemy()

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

def init_app(app):
    """
    Inicializa la base de datos con la aplicación Flask
    """
    db.init_app(app)
    
    # Crear tablas si no existen
    with app.app_context():
        # Asegurar que el directorio de la base de datos existe
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_path)
            
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                print(f"Directorio de base de datos creado: {db_dir}")
        
        try:
            # Importar modelos aquí para asegurar que se registren
            from .models import User
            print("Modelos importados correctamente")
            
            # Crear todas las tablas
            db.create_all()
            print("Tablas de la base de datos creadas exitosamente")
            
            # Verificar que las tablas se crearon
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tablas existentes en la base de datos: {tables}")
            
        except Exception as e:
            print(f"Error al crear tablas: {e}")
            # Intentar con una conexión directa a SQLite
            try:
                if db_uri.startswith('sqlite:///'):
                    db_path = db_uri.replace('sqlite:///', '')
                    conn = sqlite3.connect(db_path)
                    
                    # Crear la tabla users manualmente
                    conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username VARCHAR(64) UNIQUE NOT NULL,
                        email VARCHAR(120) UNIQUE NOT NULL,
                        password_hash VARCHAR(128) NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')
                    
                    # Crear índices
                    conn.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)')
                    conn.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)')
                    
                    conn.commit()
                    conn.close()
                    print("Tabla 'users' creada manualmente")
                    
            except Exception as manual_error:
                print(f"Error al crear tabla manualmente: {manual_error}")