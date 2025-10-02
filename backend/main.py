import os
import sys
from flask import Flask
from flask_jwt_extended import JWTManager, get_jwt, get_jwt_identity, unset_jwt_cookies
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta, timezone
import logging

# Configurar logging para el módulo principal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    storage_uri="memory://",  # En producción, usar Redis o similar
    default_limits=["200 per day", "50 per hour"],
    application_limits=["1000 per day"]  # Límite general de la app
)

# --- Lista negra de tokens JWT ---
blacklist = set()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    is_revoked = jti in blacklist
    if is_revoked:
        logger.info(f"Token JTI {jti} revocado detectado.")
    return is_revoked

@jwt.token_verification_loader
def verify_token_callback(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    if jti in blacklist:
        exp_timestamp = jwt_payload["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now)
        if target_timestamp > exp_timestamp:
            blacklist.discard(jti)
            logger.info(f"Token JTI {jti} expirado y eliminado de la lista negra.")
    return True

# --- Fin Lista negra de tokens JWT ---

def create_app():
    app = Flask(__name__)

    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instance')

    if not os.path.exists(instance_path):
        os.makedirs(instance_path, exist_ok=True)
        logger.info(f"Directorio 'instance' creado en: {instance_path}")

    db_path = os.path.join(instance_path, "app.db")
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu-clave-super-secreta-aqui-cambia-en-produccion')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-clave-super-secreta-cambia-en-produccion')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

    logger.info(f"Base de datos configurada en: {db_path}")

    try:
        init_db(app)
        logger.info("Base de datos inicializada correctamente.")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}", exc_info=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        logger.warning("Usando base de datos en memoria como fallback.")
        init_db(app)

    cors.init_app(app, resources={
        r"/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"],  # Agregué puerto del frontend
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 600
        }
    })

    jwt.init_app(app)
    limiter.init_app(app)

    # Importar blueprints y funciones necesarias ANTES de registrar
    from app.routes import main_bp
    from app.auth import auth_bp, auth_login  # Importar auth_login para decorarlo
    from app.admin import admin_bp

    # Aplicar rate limit DIRECTAMENTE a la función auth_login (antes de registrar el blueprint)
    limiter.limit("5 per minute")(auth_login)
    logger.info("Rate limit de 5 por minuto aplicado al endpoint /api/login.")

    # Registrar blueprints DESPUÉS de aplicar decoradores
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    return app

app = create_app()
app.config['PROPAGATE_EXCEPTIONS'] = False
app.config['DEBUG'] = False  # En producción, siempre False

# Handler personalizado para manejar errores de conexión (ya lo tenías, lo refino)
from werkzeug.serving import WSGIRequestHandler

class CustomWSGIRequestHandler(WSGIRequestHandler):
    def handle(self):
        try:
            super().handle()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
            # Cliente cerró la conexión prematuramente
            logger.warning(f"Conexión interrumpida por el cliente: {e} (IP: {self.client_address[0] if hasattr(self, 'client_address') else 'desconocida'})")
        except Exception as e:
            logger.error(f"Error inesperado en el manejador de solicitudes: {e}", exc_info=True)

if __name__ == '__main__':
    # Desactivar logging de werkzeug para reducir ruido
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    logger.info("=" * 50)
    logger.info("API Backend iniciada correctamente!")
    logger.info("API disponible en: http://0.0.0.0:5000")
    logger.info("Accesible desde otras máquinas en la red")
    logger.info("Endpoints:")
    logger.info("  - POST /api/login (Rate limited: 5/min)")
    logger.info("  - POST /api/register")
    logger.info("  - GET  /api/dashboard (protegido)")
    logger.info("  - GET  /api/protected (protegido)")
    logger.info("  - GET  /api/user (protegido)")
    logger.info("  - GET  /health")
    logger.info("  - GET  /network-info (info de red del servidor)")
    logger.info("  - POST /api/admin/upload-students (protegido, admin)")
    logger.info("  - GET  /api/admin/students (protegido, admin)")
    logger.info("=" * 50)

    try:
        # Opción 1: Servidor de desarrollo de Flask (para desarrollo)
        # app.run(
        #     debug=False,  # Siempre False en producción
        #     port=5000,
        #     host='0.0.0.0',
        #     request_handler=CustomWSGIRequestHandler,
        #     threaded=True
        # )

        # Opción 2: Usar Waitress para producción (recomendado, más robusto)
        from waitress import serve
        serve(app, host='0.0.0.0', port=5000, _quiet=True)  # _quiet=True reduce logs de Waitress

    except KeyboardInterrupt:
        logger.info("\nServidor detenido por el usuario.")
    except Exception as e:
        logger.critical(f"Error CRÍTICO al iniciar servidor: {e}", exc_info=True)