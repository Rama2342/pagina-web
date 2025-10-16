# ============================================
# SCHEMAS DE VALIDACIÓN - SISTEMA ESCOLAR
# ============================================
"""
Schemas de validación usando Marshmallow para garantizar que todos los datos
de entrada sean válidos y seguros antes de procesarlos en la aplicación.
"""

from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from marshmallow.validate import Length, Email, Regexp
import re
from app.segurity import InputValidator

# ============================================
# VALIDADORES PERSONALIZADOS
# ============================================

class StrongPassword(validate.Validator):
    """Validador de contraseñas fuertes"""
    
    default_message = "La contraseña debe tener al menos 8 caracteres, incluir mayúsculas, minúsculas, números y símbolos especiales"
    
    def __call__(self, value):
        is_valid, error_message = InputValidator.validate_password_strength(value)
        if not is_valid:
            raise ValidationError(error_message)
        return value

class SafeString(validate.Validator):
    """Validador para cadenas seguras sin contenido malicioso"""
    
    default_message = "Contenido no válido detectado"
    
    def __call__(self, value):
        try:
            InputValidator.sanitize_string(value)
            return value
        except Exception as e:
            raise ValidationError(str(e))

# ============================================
# SCHEMAS DE USUARIO
# ============================================

class UserRegistrationSchema(Schema):
    """Schema para registro de usuarios"""
    
    username = fields.Str(
        required=True,
        validate=[
            Length(min=3, max=20, error="El nombre de usuario debe tener entre 3 y 20 caracteres"),
            Regexp(r'^[a-zA-Z0-9_]+$', error="Solo se permiten letras, números y guiones bajos"),
            SafeString()
        ],
        error_messages={'required': 'El nombre de usuario es requerido'}
    )
    
    email = fields.Email(
        required=True,
        validate=[
            Email(error="Formato de email inválido"),
            Length(max=120, error="El email no puede exceder 120 caracteres"),
            SafeString()
        ],
        error_messages={'required': 'El email es requerido'}
    )
    
    password = fields.Str(
        required=True,
        validate=[
            StrongPassword(),
            Length(min=8, max=128, error="La contraseña debe tener entre 8 y 128 caracteres")
        ],
        error_messages={'required': 'La contraseña es requerida'},
        load_only=True  # No incluir en serialización
    )
    
    confirm_password = fields.Str(
        required=True,
        validate=[Length(min=8, max=128)],
        error_messages={'required': 'La confirmación de contraseña es requerida'},
        load_only=True
    )
    
    @validates('username')
    def validate_username_uniqueness(self, value):
        """Validar que el username no exista"""
        from app.models import User
        from app.database import db
        
        if db.session.query(User).filter_by(username=value).first():
            raise ValidationError("El nombre de usuario ya está en uso")
    
    @validates('email')
    def validate_email_uniqueness(self, value):
        """Validar que el email no exista"""
        from app.models import User
        from app.database import db
        
        if db.session.query(User).filter_by(email=value).first():
            raise ValidationError("El email ya está registrado")
    
    @validates('password')
    def validate_password_not_common(self, value):
        """Validar que la contraseña no sea común"""
        common_passwords = [
            'password', '12345678', 'qwerty123', 'admin123',
            'password123', '123456789', 'welcome123'
        ]
        if value.lower() in common_passwords:
            raise ValidationError("La contraseña es demasiado común")
    
    def validate_passwords_match(self, data, **kwargs):
        """Validar que las contraseñas coincidan"""
        if 'password' in data and 'confirm_password' in data:
            if data['password'] != data['confirm_password']:
                raise ValidationError({'confirm_password': 'Las contraseñas no coinciden'})

class UserLoginSchema(Schema):
    """Schema para login de usuarios"""
    
    username = fields.Str(
        required=True,
        validate=[
            Length(min=1, max=50, error="Nombre de usuario inválido"),
            SafeString()
        ],
        error_messages={'required': 'El nombre de usuario es requerido'}
    )
    
    password = fields.Str(
        required=True,
        validate=[Length(min=1, max=128, error="Contraseña inválida")],
        error_messages={'required': 'La contraseña es requerida'},
        load_only=True
    )

# ============================================
# SCHEMAS DE ESTUDIANTE
# ============================================

class StudentSchema(Schema):
    """Schema para datos de estudiantes"""
    
    dni = fields.Str(
        required=True,
        validate=[
            Length(min=7, max=8, error="El DNI debe tener 7 u 8 dígitos"),
            Regexp(r'^\d+$', error="El DNI solo puede contener números"),
            SafeString()
        ],
        error_messages={'required': 'El DNI es requerido'}
    )
    
    nombre = fields.Str(
        required=True,
        validate=[
            Length(min=2, max=50, error="El nombre debe tener entre 2 y 50 caracteres"),
            Regexp(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', error="Solo se permiten letras y espacios"),
            SafeString()
        ],
        error_messages={'required': 'El nombre es requerido'}
    )
    
    apellido = fields.Str(
        required=True,
        validate=[
            Length(min=2, max=50, error="El apellido debe tener entre 2 y 50 caracteres"),
            Regexp(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', error="Solo se permiten letras y espacios"),
            SafeString()
        ],
        error_messages={'required': 'El apellido es requerido'}
    )
    
    username = fields.Str(
        required=True,
        validate=[
            Length(min=3, max=20, error="El nombre de usuario debe tener entre 3 y 20 caracteres"),
            Regexp(r'^[a-zA-Z0-9_]+$', error="Solo se permiten letras, números y guiones bajos"),
            SafeString()
        ],
        error_messages={'required': 'El nombre de usuario es requerido'}
    )
    
    email = fields.Email(
        required=True,
        validate=[
            Email(error="Formato de email inválido"),
            Length(max=120, error="El email no puede exceder 120 caracteres"),
            SafeString()
        ],
        error_messages={'required': 'El email es requerido'}
    )
    
    grado = fields.Str(
        required=True,
        validate=[
            validate.OneOf(['1', '2', '3', '4', '5', '6'], error="El año tiene que estar entre 1ro y 6to"),
            SafeString()
        ],
        error_messages={'required': 'El año es requerido'}
    )
    
    seccion = fields.Str(
        required=True,
        validate=[
            Regexp(r'^[A-Z]$', error="La sección debe ser una letra mayúscula"),
            SafeString()
        ],
        error_messages={'required': 'La sección es requerida'}
    )
    
    turno = fields.Str(
        required=True,
        validate=[
            validate.OneOf(['Mañana', 'Tarde'], error="El turno debe ser Mañana o Tarde"),
            SafeString()
        ],
        error_messages={'required': 'El turno es requerido'}
    )
    
    especialidad = fields.Str(
        required=False,
        validate=[
            Length(max=100, error="La especialidad no puede exceder 100 caracteres"),
            SafeString()
        ],
        allow_none=True
    )
    
    matricula = fields.Str(
        required=True,
        validate=[
            Length(min=5, max=20, error="La matrícula debe tener entre 5 y 20 caracteres"),
            Regexp(r'^[A-Z0-9-]+$', error="Solo se permiten letras mayúsculas, números y guiones"),
            SafeString()
        ],
        error_messages={'required': 'La matrícula es requerida'}
    )
    
    estado = fields.Str(
        required=False,
        validate=[
            validate.OneOf(['Activo', 'Inactivo', 'Suspendido'], 
                         error="El estado debe ser Activo, Inactivo o Suspendido"),
            SafeString()
        ],
        missing='Activo'  # Valor por defecto
    )
    
    @validates('dni')
    def validate_dni_uniqueness(self, value):
        """Validar que el DNI no exista"""
        from app.models import Student
        from app.database import db
        
        if db.session.query(Student).filter_by(dni=value).first():
            raise ValidationError("El DNI ya está registrado")
    
    @validates('matricula')
    def validate_matricula_uniqueness(self, value):
        """Validar que la matrícula no exista"""
        from app.models import Student
        from app.database import db
        
        if db.session.query(Student).filter_by(matricula=value).first():
            raise ValidationError("La matrícula ya está registrada")
    
    @validates('username')
    def validate_username_uniqueness(self, value):
        """Validar que el username no exista"""
        from app.models import Student, User
        from app.database import db
        
        if (db.session.query(Student).filter_by(username=value).first() or
            db.session.query(User).filter_by(username=value).first()):
            raise ValidationError("El nombre de usuario ya está en uso")
    
    @validates('email')
    def validate_email_uniqueness(self, value):
        """Validar que el email no exista"""
        from app.models import Student, User
        from app.database import db
        
        if (db.session.query(Student).filter_by(email=value).first() or
            db.session.query(User).filter_by(email=value).first()):
            raise ValidationError("El email ya está registrado")

# ============================================
# SCHEMAS DE RESPUESTA
# ============================================

class UserResponseSchema(Schema):
    """Schema para respuestas de usuario (sin datos sensibles)"""
    
    id = fields.Int()
    username = fields.Str()
    email = fields.Str()
    is_admin = fields.Bool()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')

class StudentResponseSchema(Schema):
    """Schema para respuestas de estudiante"""
    
    id = fields.Int()
    dni = fields.Str()
    nombre = fields.Str()
    apellido = fields.Str()
    username = fields.Str()
    email = fields.Str()
    grado = fields.Str()
    seccion = fields.Str()
    turno = fields.Str()
    especialidad = fields.Str()
    matricula = fields.Str()
    estado = fields.Str()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')

# ============================================
# ESQUEMAS DE ACTUALIZACIÓN
# ============================================

class UserUpdateSchema(Schema):
    """Schema para actualización de usuarios"""
    
    email = fields.Email(
        required=False,
        validate=[
            Email(error="Formato de email inválido"),
            Length(max=120, error="El email no puede exceder 120 caracteres"),
            SafeString()
        ]
    )
    
    current_password = fields.Str(
        required=False,
        validate=[Length(min=1, max=128)],
        load_only=True
    )
    
    new_password = fields.Str(
        required=False,
        validate=[
            StrongPassword(),
            Length(min=8, max=128)
        ],
        load_only=True
    )
    
    def validate_password_change(self, data, **kwargs):
        """Si se cambia la contraseña, debe proporcionar la actual"""
        if 'new_password' in data and 'current_password' not in data:
            raise ValidationError({'current_password': 'Debe proporcionar la contraseña actual'})

# ============================================
# INSTANCIAS DE SCHEMAS
# ============================================

# Schemas de entrada (validación)
user_registration_schema = UserRegistrationSchema()
user_login_schema = UserLoginSchema()
student_schema = StudentSchema()
user_update_schema = UserUpdateSchema()

# Schemas de salida (serialización)
user_response_schema = UserResponseSchema()
users_response_schema = UserResponseSchema(many=True)
student_response_schema = StudentResponseSchema()
students_response_schema = StudentResponseSchema(many=True)