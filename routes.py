# FileName: /pagina-web-main/backend/app/routes.py
from flask import request, jsonify, Blueprint, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from app.database import db
from .models import User, Student
import socket
import os
import sqlite3
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Crear Blueprint para rutas principales
main_bp = Blueprint('main', __name__)

MESSAGES_FILE = os.path.join(os.path.dirname(__file__), '../instance/messages.txt')
MENSAJES_DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'mensajes.db'))

@main_bp.route('/')
def main_home():
    logger.info("Acceso a la ruta principal.")
    return jsonify({'message': 'Bienvenido a la API de Colegio San Isidro'})

@main_bp.route('/dashboard')
@jwt_required()
def main_dashboard():
    """
    Endpoint del dashboard para usuarios autenticados.
    """
    try:
        current_user_id = get_jwt_identity()

        user_result = db.session.execute(
            text('SELECT username, email, is_admin FROM users WHERE id = :user_id'),
            {'user_id': current_user_id}
        ).fetchone()

        if not user_result:
            logger.warning(f"Dashboard: Usuario con ID {current_user_id} no encontrado.")
            return jsonify({'error': 'Usuario no encontrado'}), 404

        username, email, is_admin = user_result
        logger.info(f"Acceso a dashboard para usuario: {username} (ID: {current_user_id})")
        return jsonify({
            'message': f'Bienvenido al dashboard, {username}',
            'user': {
                'id': current_user_id,
                'username': username,
                'email': email,
                'is_admin': bool(is_admin)
            },
            'status': 'success'
        })

    except Exception as e:
        logger.error(f"Error en dashboard para usuario ID {get_jwt_identity()}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error al acceder al dashboard'}), 500

@main_bp.route('/user/profile')
@jwt_required()
def get_user_profile():
    """
    Endpoint para obtener el perfil básico del usuario autenticado.
    """
    try:
        current_user_id = get_jwt_identity()

        user_result = db.session.execute(
            text('SELECT username, email, is_admin FROM users WHERE id = :user_id'),
            {'user_id': current_user_id}
        ).fetchone()

        if not user_result:
            logger.warning(f"Perfil de usuario: Usuario con ID {current_user_id} no encontrado.")
            return jsonify({'error': 'Usuario no encontrado'}), 404

        username, email, is_admin = user_result

        student_result = db.session.execute(
            text('SELECT nombre, apellido, grado, seccion, turno, especialidad, matricula, estado FROM students WHERE username = :username'),
            {'username': username}
        ).fetchone()

        if student_result:
            nombre, apellido, grado, seccion, turno, especialidad, matricula, estado = student_result
            user_data = {
                'id': current_user_id,
                'username': username,
                'email': email,
                'is_admin': bool(is_admin),
                'role': 'Estudiante',
                'matricula': matricula,
                'nombre': nombre,
                'apellido': apellido,
                'grado': grado,
                'seccion': seccion,
                'turno': turno,
                'especialidad': especialidad,
                'estado': estado
            }
        else:
            user_data = {
                'id': current_user_id,
                'username': username,
                'email': email,
                'is_admin': bool(is_admin),
                'role': 'Administrador' if is_admin else 'Usuario',
                'matricula': f"ADM-{current_user_id:04d}" if is_admin else f"USR-{current_user_id:04d}",
                'nombre': username,
                'apellido': '',
                'grado': 'Administración' if is_admin else 'No asignado',
                'seccion': '',
                'turno': '',
                'especialidad': '',
                'estado': 'Activo'
            }
        logger.info(f"Perfil de usuario obtenido para {username} (ID: {current_user_id}).")
        return jsonify({
            'success': True,
            'user': user_data
        })

    except Exception as e:
        logger.error(f"Error obteniendo perfil de usuario ID {get_jwt_identity()}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error al obtener información del usuario'}), 500

@main_bp.route('/user/full-profile')
@jwt_required()
def get_full_user_profile():
    """
    Endpoint para obtener el perfil completo del usuario autenticado.
    """
    try:
        current_user_id = get_jwt_identity()

        user_result = db.session.execute(
            text('SELECT username, email, is_admin FROM users WHERE id = :user_id'),
            {'user_id': current_user_id}
        ).fetchone()

        if not user_result:
            logger.warning(f"Perfil completo: Usuario con ID {current_user_id} no encontrado.")
            return jsonify({'error': 'Usuario no encontrado'}), 404

        username, email, is_admin = user_result

        student_result = db.session.execute(
            text('SELECT nombre, apellido, grado, seccion, turno, especialidad, matricula, estado FROM students WHERE username = :username'),
            {'username': username}
        ).fetchone()

        if student_result:
            nombre, apellido, grado, seccion, turno, especialidad, matricula, estado = student_result
            user_data = {
                'id': current_user_id,
                'username': username,
                'email': email,
                'is_admin': bool(is_admin),
                'role': 'Estudiante',
                'matricula': matricula,
                'nombre': nombre,
                'apellido': apellido,
                'grado': grado,
                'seccion': seccion,
                'turno': turno,
                'especialidad': especialidad,
                'estado': estado
            }
        else:
            user_data = {
                'id': current_user_id,
                'username': username,
                'email': email,
                'is_admin': bool(is_admin),
                'role': 'Administrador' if is_admin else 'Usuario',
                'matricula': f"ADM-{current_user_id:04d}" if is_admin else f"USR-{current_user_id:04d}",
                'nombre': username,
                'apellido': '',
                'grado': 'Administración' if is_admin else 'No asignado',
                'seccion': '',
                'turno': '',
                'especialidad': '',
                'estado': 'Activo'
            }
        logger.info(f"Perfil completo de usuario obtenido para {username} (ID: {current_user_id}).")
        return jsonify({
            'success': True,
            'user': user_data
        })

    except Exception as e:
        logger.error(f"Error obteniendo perfil completo de usuario ID {get_jwt_identity()}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error al obtener información del usuario'}), 500

@main_bp.route('/user/academic-info')
@jwt_required()
def get_academic_info():
    """
    Endpoint para obtener información académica del usuario autenticado.
    """
    try:
        current_user_id = get_jwt_identity()

        user_result = db.session.execute(
            text('SELECT username FROM users WHERE id = :user_id'),
            {'user_id': current_user_id}
        ).fetchone()

        if not user_result:
            logger.warning(f"Info académica: Usuario con ID {current_user_id} no encontrado.")
            return jsonify({'error': 'Usuario no encontrado'}), 404

        username = user_result[0]

        student_result = db.session.execute(
            text('SELECT grado, seccion, especialidad, estado FROM students WHERE username = :username'),
            {'username': username}
        ).fetchone()

        if student_result:
            grado, seccion, especialidad, estado = student_result
            academic_data = {
                'promedio_general': 8.5, # Datos de ejemplo
                'asistencia': 95,       # Datos de ejemplo
                'materias_activas': 12, # Datos de ejemplo
                'ultimo_acceso': '2024-08-29 21:45:00', # Datos de ejemplo
                'estado': estado,
                'grado': grado,
                'seccion': seccion,
                'especialidad': especialidad
            }
        else:
            academic_data = {
                'promedio_general': 0.0,
                'asistencia': 0,
                'materias_activas': 0,
                'ultimo_acceso': 'N/A',
                'estado': 'Activo',
                'grado': 'No asignado',
                'seccion': '',
                'especialidad': ''
            }
        logger.info(f"Información académica obtenida para {username} (ID: {current_user_id}).")
        return jsonify({
            'success': True,
            'academic_info': academic_data
        })

    except Exception as e:
        logger.error(f"Error obteniendo información académica de usuario ID {get_jwt_identity()}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error al obtener información académica'}), 500

@main_bp.route('/network-info')
def network_info():
    """Endpoint para obtener información de red del servidor"""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        logger.info(f"Información de red solicitada: Hostname={hostname}, IP={ip_address}")
        return jsonify({
            'success': True,
            'hostname': hostname,
            'ip_address': ip_address,
            'message': 'Servidor accesible desde la red',
            'access_url': f'http://{ip_address}:5000'
        })
    except Exception as e:
        logger.error(f"Error obteniendo información de red: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Error obteniendo información de red: {str(e)}'
        }), 500

@main_bp.route('/health')
def main_health():
    """Endpoint de salud para verificar que la API principal está funcionando."""
    logger.debug("Endpoint de salud principal accedido.")
    return jsonify({'status': 'healthy', 'message': 'API funcionando correctamente'})

@main_bp.route('/api/publish-text', methods=['POST'])
def publish_text():
    """
    Endpoint para publicar texto (ejemplo, sin persistencia real en este contexto).
    """
    data = request.get_json()
    text_content = data.get('text', '').strip() # Renombrado 'text' a 'text_content' para evitar conflicto con la función text de sqlalchemy
    if not text_content or len(text_content) > 1000:
        logger.warning(f"Intento de publicar texto inválido: '{text_content[:50]}...'")
        return jsonify({'message': 'El mensaje no puede estar vacío o es demasiado largo.'}), 400
    
    # Aquí iría la lógica para guardar el mensaje, por ejemplo, en la base de datos de mensajes.
    # Por ahora, solo se registra.
    logger.info(f"Texto publicado: {text_content}")
    return jsonify({'success': True, 'message': 'Texto recibido correctamente.'}), 200
