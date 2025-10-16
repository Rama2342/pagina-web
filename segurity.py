# ============================================
# MÓDULO DE SEGURIDAD - SISTEMA ESCOLAR
# ============================================
"""
Módulo que contiene todas las funciones y middleware relacionados con la seguridad
de la aplicación, incluyendo headers de seguridad, validación de datos,
sanitización de inputs y protección contra ataques comunes.
"""

import re
import html
import logging
from functools import wraps
from flask import request, jsonify, current_app
from werkzeug.exceptions import BadRequest
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN DE HEADERS DE SEGURIDAD
# ============================================

def add_security_headers(response):
    """
    Agrega headers de seguridad a todas las respuestas HTTP
    """
    # Previene ataques de clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Previene ataques XSS
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Previene sniffing de tipo MIME
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Política de referrer
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Previene carga de recursos desde dominios no autorizados
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self';"
    )
    
    # HSTS para HTTPS
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Previene caching de respuestas sensibles
    if 'api' in request.path:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

# ============================================
# VALIDACIÓN Y SANITIZACIÓN DE DATOS
# ============================================

class InputValidator:
    """Clase para validar y sanitizar datos de entrada"""
    
    # Patrones de validación
    PATTERNS = {
        'username': re.compile(r'^[a-zA-Z0-9_]{3,20}$'),
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'password': re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'),
        'dni': re.compile(r'^\d{7,8}$'),
        'matricula': re.compile(r'^[A-Z0-9-]{5,20}$'),
        'nombre': re.compile(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,50}$'),
        'grado': re.compile(r'^[1-6]$'),
        'seccion': re.compile(r'^[A-Z]$'),
        'turno': re.compile(r'^(Mañana|Tarde|Noche)$'),
    }
    
    # Lista de palabras/patrones maliciosos
    MALICIOUS_PATTERNS = [
        re.compile(r'<script.*?</script>', re.IGNORECASE),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
        re.compile(r'<iframe', re.IGNORECASE),
        re.compile(r'<object', re.IGNORECASE),
        re.compile(r'<embed', re.IGNORECASE),
        re.compile(r'union.*select', re.IGNORECASE),
        re.compile(r'drop.*table', re.IGNORECASE),
        re.compile(r'delete.*from', re.IGNORECASE),
        re.compile(r'insert.*into', re.IGNORECASE),
    ]
    
    @staticmethod
    def sanitize_string(value, max_length=255):
        """Sanitiza una cadena de texto"""
        if not isinstance(value, str):
            return str(value)
        
        # Escapa caracteres HTML
        value = html.escape(value.strip())
        
        # Limita la longitud
        value = value[:max_length]
        
        # Verifica patrones maliciosos
        for pattern in InputValidator.MALICIOUS_PATTERNS:
            if pattern.search(value):
                logger.warning(f"Intento de inyección detectado: {value[:50]}...")
                raise BadRequest("Contenido no válido detectado")
        
        return value
    
    @staticmethod
    def validate_field(field_name, value):
        """Valida un campo específico"""
        if field_name in InputValidator.PATTERNS:
            pattern = InputValidator.PATTERNS[field_name]
            if not pattern.match(str(value)):
                return False, f"El campo {field_name} no tiene un formato válido"
        
        return True, None
    
    @staticmethod
    def validate_password_strength(password):
        """Valida la fortaleza de una contraseña"""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        
        if not re.search(r'[a-z]', password):
            return False, "La contraseña debe contener al menos una letra minúscula"
        
        if not re.search(r'[A-Z]', password):
            return False, "La contraseña debe contener al menos una letra mayúscula"
        
        if not re.search(r'\d', password):
            return False, "La contraseña debe contener al menos un número"
        
        if not re.search(r'[@$!%*?&]', password):
            return False, "La contraseña debe contener al menos un carácter especial (@$!%*?&)"
        
        # Verifica patrones comunes débiles
        weak_patterns = ['123', 'abc', 'password', 'qwerty', '111', '000']
        password_lower = password.lower()
        for pattern in weak_patterns:
            if pattern in password_lower:
                return False, f"La contraseña no puede contener patrones comunes como '{pattern}'"
        
        return True, "Contraseña válida"

# ============================================
# DECORADORES DE SEGURIDAD
# ============================================

def validate_json(required_fields=None, optional_fields=None):
    """Decorador para validar datos JSON de entrada"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type debe ser application/json'}), 400
            
            try:
                data = request.get_json()
            except Exception as e:
                logger.warning(f"JSON inválido recibido: {e}")
                return jsonify({'error': 'JSON inválido'}), 400
            
            if not data:
                return jsonify({'error': 'No se enviaron datos'}), 400
            
            # Validar campos requeridos
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in data or not data[field]:
                        missing_fields.append(field)
                
                if missing_fields:
                    return jsonify({
                        'error': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
                    }), 400
            
            # Sanitizar todos los campos de texto
            sanitized_data = {}
            all_fields = (required_fields or []) + (optional_fields or [])
            
            for field in data:
                if field in all_fields:
                    value = data[field]
                    if isinstance(value, str):
                        try:
                            sanitized_data[field] = InputValidator.sanitize_string(value)
                        except BadRequest as e:
                            return jsonify({'error': str(e)}), 400
                    else:
                        sanitized_data[field] = value
            
            # Validar campos específicos
            for field, value in sanitized_data.items():
                is_valid, error_msg = InputValidator.validate_field(field, value)
                if not is_valid:
                    return jsonify({'error': error_msg}), 400
            
            # Agregar datos sanitizados al request
            request.validated_data = sanitized_data
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

def require_admin(f):
    """Decorador que requiere permisos de administrador"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import get_jwt_identity
        from .models import User
        from .database import db
        
        try:
            current_user_id = get_jwt_identity()
            user = db.session.get(User, current_user_id)
            
            if not user or not user.is_admin:
                logger.warning(f"Intento de acceso no autorizado de usuario ID: {current_user_id}")
                return jsonify({'error': 'Acceso denegado: Se requieren permisos de administrador'}), 403
                
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error en verificación de admin: {e}")
            return jsonify({'error': 'Error de autorización'}), 500
    
    return wrapper

def log_security_event(event_type):
    """Decorador para registrar eventos de seguridad"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            user_agent = request.headers.get('User-Agent', 'Unknown')
            
            logger.info(
                f"SECURITY_EVENT: {event_type} - "
                f"IP: {client_ip} - "
                f"User-Agent: {user_agent} - "
                f"Endpoint: {request.endpoint}"
            )
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ============================================
# CONFIGURACIÓN DE RATE LIMITING AVANZADO
# ============================================

def create_rate_limiter(app):
    """Crear y configurar el limitador de velocidad"""
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["1000 per day", "100 per hour"]
    )
    
    return limiter

def rate_limit_by_user():
    """Rate limiting personalizado por usuario autenticado"""
    def get_user_id():
        try:
            from flask_jwt_extended import get_jwt_identity
            return get_jwt_identity() or get_remote_address()
        except:
            return get_remote_address()
    
    return get_user_id

# ============================================
# DETECCIÓN DE AMENAZAS
# ============================================

class ThreatDetection:
    """Sistema básico de detección de amenazas"""
    
    # Contador de intentos sospechosos por IP
    suspicious_ips = {}
    blocked_ips = set()
    
    @staticmethod
    def check_suspicious_activity(client_ip, activity_type):
        """Verifica actividad sospechosa"""
        if client_ip in ThreatDetection.blocked_ips:
            return True
        
        if client_ip not in ThreatDetection.suspicious_ips:
            ThreatDetection.suspicious_ips[client_ip] = {}
        
        if activity_type not in ThreatDetection.suspicious_ips[client_ip]:
            ThreatDetection.suspicious_ips[client_ip][activity_type] = 0
        
        ThreatDetection.suspicious_ips[client_ip][activity_type] += 1
        
        # Bloquear si hay demasiados intentos fallidos
        if ThreatDetection.suspicious_ips[client_ip].get(activity_type, 0) > 10:
            ThreatDetection.blocked_ips.add(client_ip)
            logger.critical(f"IP {client_ip} bloqueada por actividad sospechosa: {activity_type}")
            return True
        
        return False
    
    @staticmethod
    def reset_ip_counter(client_ip, activity_type=None):
        """Resetear contador para una IP"""
        if client_ip in ThreatDetection.suspicious_ips:
            if activity_type:
                ThreatDetection.suspicious_ips[client_ip][activity_type] = 0
            else:
                ThreatDetection.suspicious_ips[client_ip] = {}

def check_blocked_ip(f):
    """Decorador para verificar IPs bloqueadas"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        if ThreatDetection.check_suspicious_activity(client_ip, 'general'):
            logger.warning(f"Acceso denegado para IP bloqueada: {client_ip}")
            return jsonify({'error': 'Acceso temporalmente restringido'}), 429
        
        return f(*args, **kwargs)
    return wrapper