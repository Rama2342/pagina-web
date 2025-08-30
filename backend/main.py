import os
import sys
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Añadir el directorio actual al path para que Python encuentre el módulo app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar la instancia de db y las funciones de database.py
from app.database import db, init_app as init_db

# Inicializar otras extensiones
jwt = JWTManager()
cors = CORS()

# Configurar limiter con storage explícito
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["200 per day", "50 per hour"]
)

def create_app():
    app = Flask(__name__)
    
    # Configuración - RUTA ABSOLUTA para la base de datos
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instance')
    
    # Asegurarse de que el directorio instance existe
    if not os.path.exists(instance_path):
        os.makedirs(instance_path, exist_ok=True)
        print(f"Directorio 'instance' creado en: {instance_path}")
    
    db_path = os.path.join(instance_path, "app.db")
    app.config['SECRET_KEY'] = 'tu-clave-super-secreta-aqui-cambia-en-produccion'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'jwt-clave-super-secreta-cambia-en-produccion'
    
    print(f"Base de datos configurada en: {db_path}")
    
    # Inicializar extensiones con la app
    try:
        init_db(app)
        print("Base de datos inicializada correctamente")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        # Intentar con base de datos en memoria como fallback
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        print("Usando base de datos en memoria como fallback")
        init_db(app)
    
    # Configurar CORS para permitir frontend
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": "http://localhost:3000",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    jwt.init_app(app)
    limiter.init_app(app)
    
    # Importar y registrar blueprints
    from app.routes import main_bp
    from app.auth import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("=" * 50)
    print("API Backend iniciada correctamente!")
    print("API disponible en: http://localhost:5000")
    print("Endpoints:")
    print("  - POST /api/login")
    print("  - POST /api/register") 
    print("  - GET  /api/dashboard (protegido)")
    print("  - GET  /api/protected (protegido)")
    print("  - GET  /api/user (protegido)")
    print("  - GET  /health")
    print("=" * 50)
    app.run(debug=True, port=5000, host='0.0.0.0')