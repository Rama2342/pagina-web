import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Configuración base de la aplicación con seguridad mejorada"""
    
    # === CLAVES SECRETAS ===
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # Validar que las claves secretas estén configuradas
    if not SECRET_KEY or SECRET_KEY.startswith('TU_CLAVE'):
        raise ValueError("⚠️  SEGURIDAD: Debes configurar SECRET_KEY en el archivo .env")
    if not JWT_SECRET_KEY or JWT_SECRET_KEY.startswith('TU_JWT'):
        raise ValueError("⚠️  SEGURIDAD: Debes configurar JWT_SECRET_KEY en el archivo .env")
    
    # === BASE DE DATOS ===
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(basedir, "instance", "app.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # === CONFIGURACIÓN JWT ===
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30)))
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # === CORS Y SEGURIDAD ===
    ALLOWED_ORIGINS = [origin for origin in os.environ.get('ALLOWED_ORIGINS', '').split(',') if origin]
    
    # === RATE LIMITING ===
    RATE_LIMIT_PER_DAY = int(os.environ.get('RATE_LIMIT_PER_DAY', 1000))
    RATE_LIMIT_PER_HOUR = int(os.environ.get('RATE_LIMIT_PER_HOUR', 100))
    RATE_LIMIT_LOGIN_PER_MINUTE = int(os.environ.get('RATE_LIMIT_LOGIN_PER_MINUTE', 5))
    
    # === CONFIGURACIÓN DE LOGGING ===
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    
    # === CONFIGURACIÓN DE SESIÓN ===
    SESSION_COOKIE_SECURE = True  # Solo HTTPS en producción
    SESSION_COOKIE_HTTPONLY = True  # No accesible desde JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'  # Protección CSRF
    
    # === CONFIGURACIÓN DE FLASK ===
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    TESTING = False
    
    @staticmethod
    def init_app(app):
        """Inicialización adicional de la aplicación"""
        pass

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # HTTP permitido en desarrollo

class ProductionConfig(Config):
    """Configuración para producción con seguridad máxima"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Logging para producción
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/app.log', maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Sistema Escolar iniciado')

class TestingConfig(Config):
    """Configuración para tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SESSION_COOKIE_SECURE = False

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}