# FileName: /pagina-web-main/backend/app/auth.py
from flask import request, jsonify, Blueprint, session, redirect, url_for, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import traceback
import logging

from .database import db
from .models import User, Student # Asegúrate de que Student esté importado

# Configurar logging
logger = logging.getLogger(__name__)

# Crear Blueprint para autenticación
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
# Se asume que Flask-Limiter está configurado en main.py y se aplica globalmente o se puede aplicar aquí si es necesario.
# @limiter.limit("5 per minute") # Ejemplo de rate limit específico para login
def auth_login():
    """
    Endpoint para el inicio de sesión de usuarios.
    Verifica credenciales y el estado del estudiante si no es admin.
    """
    try:
        if not request.is_json:
            logger.warning("Intento de login sin JSON.")
            return jsonify({'success': False, 'error': 'Se requiere contenido JSON'}), 400

        data = request.get_json()
        logger.info(f"Intento de login para usuario: {data.get('username', 'N/A')}")

        if not data or 'username' not in data or 'password' not in data:
            logger.warning("Login fallido: Faltan username o password.")
            return jsonify({'success': False, 'error': 'Se requieren username y password'}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            logger.warning("Login fallido: Username o password vacíos.")
            return jsonify({'success': False, 'error': 'Username y password no pueden estar vacíos'}), 400

        user_result = db.session.execute(
            text('SELECT id, username, email, password_hash, is_admin, student_id FROM users WHERE username = :username'),
            {'username': username}
        ).fetchone()

        if not user_result:
            logger.warning(f"Login fallido: Usuario '{username}' no encontrado.")
            return jsonify({'success': False, 'error': 'Credenciales inválidas'}), 401

        user_id, db_username, email, password_hash, is_admin, student_id = user_result

        if not check_password_hash(password_hash, password):
            logger.warning(f"Login fallido: Contraseña incorrecta para usuario '{username}'.")
            return jsonify({'success': False, 'error': 'Credenciales inválidas'}), 401

        # --- Lógica de verificación de estudiante y estado ---
        if not is_admin:
            student_status_result = db.session.execute(
                text('SELECT estado FROM students WHERE username = :username'),
                {'username': username}
            ).fetchone()

            if not student_status_result:
                logger.warning(f"Login fallido: Usuario '{username}' no encontrado en la tabla de estudiantes.")
                return jsonify({'success': False, 'error': 'Acceso denegado. Su cuenta no está registrada como estudiante.'}), 403

            student_estado = student_status_result[0]
            if student_estado != 'Activo':
                logger.warning(f"Login fallido: Usuario '{username}' con estado '{student_estado}'.")
                return jsonify({'success': False, 'error': f'Acceso denegado. Su cuenta está {student_estado}. Contacte a administración.'}), 403
        # --- Fin Lógica de verificación ---

        token = create_access_token(identity=user_id)

        student_data = None
        if student_id:
            student_result = db.session.execute(
                text('SELECT nombre, apellido, email, grado, seccion, turno, especialidad, matricula, estado FROM students WHERE id = :student_id'),
                {'student_id': student_id}
            ).fetchone()
            if student_result:
                student_data = {
                    'nombre': student_result[0],
                    'apellido': student_result[1],
                    'email': student_result[2],
                    'grado': student_result[3],
                    'seccion': student_result[4],
                    'turno': student_result[5],
                    'especialidad': student_result[6],
                    'matricula': student_result[7],
                    'estado': student_result[8]
                }

        user_response_data = {
            'id': user_id,
            'username': db_username,
            'email': email,
            'is_admin': bool(is_admin),
            'role': 'Administrador' if is_admin else 'Estudiante'
        }

        if student_data:
            user_response_data.update(student_data)
        else:
            # Datos por defecto para admins o usuarios sin perfil de estudiante
            user_response_data.update({
                'nombre': db_username,
                'apellido': '',
                'grado': 'N/A',
                'seccion': 'N/A',
                'turno': 'N/A',
                'especialidad': 'N/A',
                'matricula': f"ADM-{user_id:04d}" if is_admin else f"USR-{user_id:04d}",
                'estado': 'Activo'
            })

        logger.info(f"Login exitoso para usuario: {db_username}, Admin: {is_admin}")
        return jsonify({
            'success': True,
            'token': token,
            'user_id': user_id,
            'message': 'Login exitoso',
            'user_data': user_response_data
        })

    except Exception as e:
        logger.error(f"ERROR en login: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor. Contacte al administrador.'
        }), 500

@auth_bp.route('/register', methods=['POST'])
def auth_register():
    """
    Endpoint para el registro de nuevos usuarios.
    Solo permite el registro si el usuario ya existe como estudiante activo y no tiene un usuario asociado.
    """
    try:
        if not request.is_json:
            logger.warning("Intento de registro sin JSON.")
            return jsonify({'success': False, 'error': 'Se requiere contenido JSON'}), 400

        data = request.get_json()
        logger.info(f"Intento de registro para usuario: {data.get('username', 'N/A')}")

        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"Registro fallido: Campo '{field}' requerido vacío.")
                return jsonify({'success': False, 'error': f'El campo {field} es requerido'}), 400

        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()

        if len(username) < 3:
            return jsonify({'success': False, 'error': 'El username debe tener al menos 3 caracteres'}), 400
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'La contraseña debe tener al menos 6 caracteres'}), 400

        # Verificar si el usuario ya existe en la tabla 'users'
        existing_user = db.session.execute(
            text('SELECT id FROM users WHERE username = :username OR email = :email'),
            {'username': username, 'email': email}
        ).fetchone()

        if existing_user:
            logger.warning(f"Registro fallido: Usuario o email ya existen en la tabla 'users' ({username}, {email}).")
            return jsonify({'success': False, 'error': 'El usuario o email ya existe'}), 400

        # --- Lógica: No permitir registro si no está en la lista de estudiantes activos ---
        existing_student = db.session.execute(
            text('SELECT id, email FROM students WHERE username = :username AND email = :email AND estado = "Activo"'),
            {'username': username, 'email': email}
        ).fetchone()

        if not existing_student:
            logger.warning(f"Registro fallido: Estudiante '{username}' no encontrado o no activo en la lista de estudiantes.")
            return jsonify({'success': False, 'error': 'No se puede registrar. Su usuario no está en la lista de estudiantes activos o el email no coincide.'}), 403

        student_id = existing_student[0]

        # Verificar si el estudiante ya tiene un usuario asociado
        user_linked_to_student = db.session.execute(
            text('SELECT id FROM users WHERE student_id = :student_id'),
            {'student_id': student_id}
        ).fetchone()

        if user_linked_to_student:
            logger.warning(f"Registro fallido: Estudiante con ID {student_id} ya tiene una cuenta de usuario asociada.")
            return jsonify({'success': False, 'error': 'Este estudiante ya tiene una cuenta de usuario asociada.'}), 403
        # --- Fin Lógica ---

        password_hash = generate_password_hash(password)
        result = db.session.execute(
            text('''
            INSERT INTO users (username, email, password_hash, is_admin, student_id)
            VALUES (:username, :email, :password_hash, :is_admin, :student_id)
            '''),
            {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'is_admin': False,
                'student_id': student_id
            }
        )
        db.session.commit()

        user_id = result.lastrowid
        logger.info(f"Usuario creado exitosamente: {username}, ID: {user_id}, Student ID: {student_id}")
        return jsonify({
            'success': True,
            'message': 'Usuario creado exitosamente y vinculado a su perfil de estudiante.',
            'user_id': user_id
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Error de integridad al registrar usuario: {e.orig}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error de integridad de datos (usuario o email duplicado).'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error general al crear usuario: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Error al crear usuario. Contacte al administrador.'
        }), 500

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def auth_protected():
    """
    Endpoint de ejemplo para una ruta protegida por JWT.
    """
    try:
        current_user_id = get_jwt_identity()
        user_result = db.session.execute(
            text('SELECT username, email, is_admin FROM users WHERE id = :user_id'),
            {'user_id': current_user_id}
        ).fetchone()

        if not user_result:
            logger.warning(f"Acceso protegido fallido: Usuario con ID {current_user_id} no encontrado.")
            return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

        username, email, is_admin = user_result
        logger.info(f"Acceso protegido exitoso para usuario: {username} (ID: {current_user_id})")
        return jsonify({
            'success': True,
            'message': 'Acceso permitido',
            'user': {
                'id': current_user_id,
                'username': username,
                'email': email,
                'is_admin': bool(is_admin)
            }
        })

    except Exception as e:
        logger.error(f"Error en endpoint protegido: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error de autenticación'}), 401

@auth_bp.route('/user', methods=['GET'])
@jwt_required()
def auth_get_user():
    """
    Endpoint para obtener la información básica del usuario autenticado.
    """
    try:
        current_user_id = get_jwt_identity()
        user_result = db.session.execute(
            text('SELECT username, email, is_admin FROM users WHERE id = :user_id'),
            {'user_id': current_user_id}
        ).fetchone()

        if not user_result:
            logger.warning(f"Obtención de usuario fallida: Usuario con ID {current_user_id} no encontrado.")
            return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

        username, email, is_admin = user_result
        return jsonify({
            'success': True,
            'user': {
                'id': current_user_id,
                'username': username,
                'email': email,
                'is_admin': bool(is_admin)
            }
        })

    except Exception as e:
        logger.error(f"Error obteniendo usuario: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error al obtener información del usuario'}), 500

@auth_bp.route('/health', methods=['GET'])
def auth_health():
    """
    Endpoint de salud para verificar que el módulo de autenticación está funcionando.
    """
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'success': True,
            'message': 'Auth module working correctly',
            'status': 'healthy'
        })
    except Exception as e:
        logger.critical(f"Database connection error in auth_health: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Database connection error: {str(e)}',
            'status': 'unhealthy'
        }), 500

# Funciones auxiliares (mantienen la misma lógica, solo se añade logging si es necesario)
def guardar_usuario(username, password):
    hashed_password = generate_password_hash(password)
    logger.info(f"Guardando usuario {username} con hash de contraseña.")
    db.session.execute(
        text('INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)'),
        {'username': username, 'password_hash': hashed_password}
    )
    db.session.commit()

def verificar_usuario(username, password):
    result = db.session.execute(
        text('SELECT password_hash FROM users WHERE username = :username'),
        {'username': username}
    ).fetchone()
    if not result:
        logger.debug(f"Intento de verificación de usuario fallido: {username} no encontrado.")
        return False
    hashed_password = result[0]
    return check_password_hash(hashed_password, password)

# La función login_required no se usa con JWT, se mantiene por si acaso pero no es parte del flujo JWT.
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper
