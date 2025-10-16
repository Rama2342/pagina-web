import os
import sys
from flask import Flask
from flask_jwt_extended import JWTManager, get_jwt, get_jwt_identity, unset_jwt_cookies
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta, timezone
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar módulos de seguridad
from app.segurity import add_security_headers, ThreatDetection, check_blocked_ip
from config import config

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

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Determinar configuración basada en entorno
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        if config_name not in config:
            config_name = 'default'
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instance')

    if not os.path.exists(instance_path):
        os.makedirs(instance_path, exist_ok=True)
        logger.info(f"Directorio 'instance' creado en: {instance_path}")

    # Mantener db_path para el logging
    db_path = os.path.join(instance_path, "app.db")
    
    # Si no hay DATABASE_URL en config, usar la ruta local
    if not app.config.get('SQLALCHEMY_DATABASE_URI') or app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    logger.info(f"Base de datos configurada en: {db_path}")

    try:
        init_db(app)
        logger.info("Base de datos inicializada correctamente.")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}", exc_info=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        logger.warning("Usando base de datos en memoria como fallback.")
        init_db(app)

    # Configuración CORS segura
    allowed_origins = app.config.get('ALLOWED_ORIGINS', [])
    if not allowed_origins or (len(allowed_origins) == 1 and not allowed_origins[0]):
        # Si no hay orígenes configurados, usar localhost para desarrollo
        if app.config.get('DEBUG', False):
            allowed_origins = ['http://localhost:3000', 'http://127.0.0.1:5500', 'http://localhost:8000']
            logger.warning("⚠️  Usando orígenes por defecto para desarrollo. Configura ALLOWED_ORIGINS en producción.")
        else:
            logger.error("⚠️  CORS: No se configuraron orígenes permitidos para producción")
            allowed_origins = []  # Bloquear todo en producción si no está configurado
    
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })
    
    logger.info(f"CORS configurado para orígenes: {allowed_origins}")

    jwt.init_app(app)
    
    # Configurar rate limiting mejorado
    rate_limits = [
        f"{app.config.get('RATE_LIMIT_PER_DAY', 1000)} per day",
        f"{app.config.get('RATE_LIMIT_PER_HOUR', 100)} per hour"
    ]
    limiter.init_app(app)
    
    # Agregar headers de seguridad a todas las respuestas
    @app.after_request
    def after_request(response):
        return add_security_headers(response)
    
    # Verificar IPs bloqueadas en todas las rutas
    @app.before_request
    def before_request():
        from flask import request, jsonify
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        if client_ip in ThreatDetection.blocked_ips:
            logger.warning(f"Acceso denegado para IP bloqueada: {client_ip}")
            return jsonify({'error': 'Acceso temporalmente restringido'}), 429
    
    # Importar blueprints y funciones necesarias ANTES de registrar
    from app.routes import main_bp
    from app.auth import auth_bp, auth_login  # Importar auth_login para decorarlo
    from app.admin import admin_bp

    # Aplicar rate limit DIRECTAMENTE a la función auth_login (antes de registrar el blueprint)
    login_rate_limit = f"{app.config.get('RATE_LIMIT_LOGIN_PER_MINUTE', 5)} per minute"
    limiter.limit(login_rate_limit)(auth_login)
    logger.info(f"Rate limit de {login_rate_limit} aplicado al endpoint /api/login.")

    # Registrar blueprints DESPUÉS de aplicar decoradores
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    logger.info("Headers de seguridad configurados")
    logger.info(f"Rate limiting configurado: {rate_limits}")

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
        from waitress import serve
        serve(app, host='0.0.0.0', port=5000, _quiet=True)  # _quiet=True reduce logs de Waitress

    except KeyboardInterrupt:
        logger.info("\nServidor detenido por el usuario.")
    except Exception as e:
        logger.critical(f"Error CRÍTICO al iniciar servidor: {e}", exc_info=True)