# FileName: /pagina-web-main/backend/app/admin.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import pandas as pd
import io
import random
import string
import logging

from .database import db
from .models import User, Student
from werkzeug.security import generate_password_hash

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Crear Blueprint para administración
admin_bp = Blueprint('admin', __name__)

# Función decoradora para requerir admin
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)

            if not current_user:
                logger.warning(f"Intento de acceso no autenticado a ruta de admin.")
                return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401

            is_admin = getattr(current_user, 'is_admin', False)
            if not is_admin:
                logger.warning(f"Acceso denegado a admin para usuario {current_user.username} (ID: {current_user_id}).")
                return jsonify({'success': False, 'error': 'Acceso no autorizado. Se requiere rol de administrador'}), 403

            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en require_admin: {e}", exc_info=True)
            return jsonify({'success': False, 'error': 'Error de autenticación'}), 401
    return decorated_function

def _generate_strong_password(length=12):
    """Genera una contraseña aleatoria fuerte."""
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def _validate_student_data(row, index, required_columns):
    """Valida los datos de una fila de estudiante."""
    errors = []
    data = {}

    for col in required_columns:
        value = str(row.get(col, '')).strip()
        if not value:
            errors.append(f"Columna '{col}' vacía.")
        data[col] = value

    # Validaciones de formato específicas
    if 'email' in data and '@' not in data['email']:
        errors.append("Formato de email inválido.")
    if 'dni' in data and not data['dni'].isdigit():
        errors.append("DNI debe contener solo dígitos.")
    if 'matricula' in data and not data['matricula'].isalnum(): # Ejemplo: alfanumérico
        errors.append("Matrícula debe ser alfanumérica.")

    data['especialidad'] = str(row.get('especialidad', '')).strip()
    data['estado'] = str(row.get('estado', 'Activo')).strip()

    if errors:
        return None, f"Fila {index + 2}: {'; '.join(errors)}"
    return data, None

def _process_student_row(session, student_data, existing_students_map, existing_users_map, new_users_to_add, updated_users_to_update):
    """Procesa una fila de estudiante, actualizando o creando el estudiante y su usuario."""
    dni = student_data['dni']
    username = student_data['username']
    email = student_data['email']
    matricula = student_data['matricula']

    student_id = None
    student_action = 'created'
    user_action = 'created'

    # Buscar estudiante existente por DNI, username, email o matrícula
    existing_student_entry = existing_students_map.get(dni) or \
                             existing_students_map.get(username) or \
                             existing_students_map.get(email) or \
                             existing_students_map.get(matricula)

    if existing_student_entry:
        student_id = existing_student_entry['id']
        student_action = 'updated'
        # Actualizar estudiante existente
        session.execute(
            text('''
            UPDATE students SET
                nombre = :nombre, apellido = :apellido, grado = :grado,
                seccion = :seccion, turno = :turno, especialidad = :especialidad,
                estado = :estado, email = :email, dni = :dni, matricula = :matricula
            WHERE id = :id
            '''),
            {
                'nombre': student_data['nombre'], 'apellido': student_data['apellido'],
                'grado': student_data['grado'], 'seccion': student_data['seccion'],
                'turno': student_data['turno'], 'especialidad': student_data['especialidad'],
                'estado': student_data['estado'], 'email': email, 'dni': dni,
                'matricula': matricula, 'id': student_id
            }
        )
        logger.info(f"Estudiante actualizado: {username} (ID: {student_id})")
    else:
        # Crear nuevo estudiante
        result = session.execute(
            text('''
            INSERT INTO students
            (dni, nombre, apellido, username, email, grado, seccion, turno, especialidad, matricula, estado)
            VALUES
            (:dni, :nombre, :apellido, :username, :email, :grado, :seccion, :turno, :especialidad, :matricula, :estado)
            '''),
            {
                'dni': dni, 'nombre': student_data['nombre'], 'apellido': student_data['apellido'],
                'username': username, 'email': email, 'grado': student_data['grado'],
                'seccion': student_data['seccion'], 'turno': student_data['turno'],
                'especialidad': student_data['especialidad'], 'matricula': matricula,
                'estado': student_data['estado']
            }
        )
        student_id = result.lastrowid
        logger.info(f"Nuevo estudiante creado: {username} (ID: {student_id})")

    # --- Lógica para crear/vincular usuario en la tabla 'users' ---
    existing_user_entry = existing_users_map.get(username) or existing_users_map.get(email)

    if existing_user_entry:
        user_id = existing_user_entry['id']
        # Actualizar el student_id si el usuario ya existe y no está vinculado
        if existing_user_entry['student_id'] is None:
            updated_users_to_update.append({
                'id': user_id,
                'student_id': student_id,
                'email': email
            })
            user_action = 'linked'
            logger.info(f"Usuario existente {username} vinculado a estudiante {student_id}")
        else:
            user_action = 'already_linked'
            logger.debug(f"Usuario existente {username} ya vinculado a estudiante {existing_user_entry['student_id']}")
    else:
        # Crear un nuevo usuario para el estudiante
        default_password = _generate_strong_password() # Generar contraseña fuerte
        default_password_hash = generate_password_hash(default_password)
        new_users_to_add.append({
            'username': username,
            'email': email,
            'password_hash': default_password_hash,
            'is_admin': False,
            'student_id': student_id
        })
        logger.info(f"Nuevo usuario creado para estudiante: {username}")

    return student_action, user_action, student_id

@admin_bp.route('/upload-students', methods=['POST'])
@jwt_required()
@require_admin
def upload_students():
    """
    Endpoint para subir un archivo Excel con datos de estudiantes.
    Crea o actualiza estudiantes y sus usuarios asociados.
    Desactiva estudiantes que estaban activos en la DB pero no están en el archivo.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No se encontró el archivo'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No se seleccionó ningún archivo'}), 400

        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'El archivo debe ser un Excel (.xlsx o .xls)'}), 400

        excel_data = file.read()
        try:
            df = pd.read_excel(io.BytesIO(excel_data))
        except Exception as e:
            logger.error(f"Error al leer el archivo Excel: {e}", exc_info=True)
            return jsonify({'success': False, 'error': f'Error al leer el archivo Excel. Asegúrate de que sea un formato válido: {str(e)}'}), 400

        logger.info(f"Excel leído. Columnas: {df.columns.tolist()}")
        logger.debug(f"Primeras filas:\n{df.head()}")

        required_columns = ['dni', 'nombre', 'apellido', 'username', 'email', 'grado', 'seccion', 'turno', 'matricula']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return jsonify({
                'success': False,
                'error': f'Faltan columnas requeridas en el archivo: {", ".join(missing_columns)}'
            }), 400

        # Cargar todos los estudiantes y usuarios existentes en memoria para optimizar
        existing_students = db.session.execute(
            text("SELECT id, dni, username, email, matricula, estado FROM students")
        ).fetchall()
        existing_students_map = {}
        for s in existing_students:
            existing_students_map[s.dni] = {'id': s.id, 'username': s.username, 'email': s.email, 'matricula': s.matricula, 'estado': s.estado}
            existing_students_map[s.username] = {'id': s.id, 'dni': s.dni, 'email': s.email, 'matricula': s.matricula, 'estado': s.estado}
            existing_students_map[s.email] = {'id': s.id, 'dni': s.dni, 'username': s.username, 'matricula': s.matricula, 'estado': s.estado}
            existing_students_map[s.matricula] = {'id': s.id, 'dni': s.dni, 'username': s.username, 'email': s.email, 'estado': s.estado}

        existing_users = db.session.execute(
            text("SELECT id, username, email, student_id FROM users")
        ).fetchall()
        existing_users_map = {}
        for u in existing_users:
            existing_users_map[u.username] = {'id': u.id, 'email': u.email, 'student_id': u.student_id}
            existing_users_map[u.email] = {'id': u.id, 'username': u.username, 'student_id': u.student_id}

        usernames_in_excel = set()
        new_users_to_add = []
        updated_users_to_update = []
        success_count = 0
        error_count = 0
        errors = []

        for index, row in df.iterrows():
            validated_data, validation_error = _validate_student_data(row, index, required_columns)
            if validation_error:
                error_count += 1
                errors.append(validation_error)
                logger.warning(f"Error de validación en Excel: {validation_error}")
                continue

            usernames_in_excel.add(validated_data['username'])

            try:
                student_action, user_action, student_id = _process_student_row(
                    db.session, validated_data, existing_students_map, existing_users_map,
                    new_users_to_add, updated_users_to_update
                )
                success_count += 1
            except IntegrityError as e:
                db.session.rollback()
                error_count += 1
                error_msg = f"Fila {index + 2} ({validated_data.get('username', 'N/A')}): Error de integridad de datos (DNI, Username, Email o Matrícula duplicados). Detalles: {e.orig}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)
            except Exception as e:
                db.session.rollback()
                error_count += 1
                error_msg = f"Fila {index + 2} ({validated_data.get('username', 'N/A')}): Error inesperado al procesar. Detalles: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)

        # Realizar inserciones y actualizaciones masivas de usuarios
        if new_users_to_add:
            db.session.bulk_insert_mappings(User, new_users_to_add)
            logger.info(f"Insertados {len(new_users_to_add)} nuevos usuarios en bloque.")
        if updated_users_to_update:
            db.session.bulk_update_mappings(User, updated_users_to_update)
            logger.info(f"Actualizados {len(updated_users_to_update)} usuarios en bloque.")

        # --- Lógica para desactivar estudiantes no presentes en el Excel ---
        all_active_students_usernames_db = {s.username for s in existing_students if s.estado == 'Activo'}
        students_to_deactivate = all_active_students_usernames_db - usernames_in_excel

        deactivated_count = 0
        if students_to_deactivate:
            try:
                # Desactivar estudiantes
                db.session.execute(
                    text("UPDATE students SET estado = 'Inactivo' WHERE username IN :usernames"),
                    {'usernames': tuple(students_to_deactivate)}
                )
                # Desactivar usuarios asociados (si no son admin)
                db.session.execute(
                    text("UPDATE users SET is_admin = FALSE WHERE username IN :usernames AND is_admin = FALSE"),
                    {'usernames': tuple(students_to_deactivate)}
                )
                deactivated_count = len(students_to_deactivate)
                logger.info(f"Desactivados {deactivated_count} estudiantes y usuarios asociados.")
            except Exception as e:
                db.session.rollback()
                error_count += 1
                error_msg = f"Error al desactivar estudiantes: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)

        db.session.commit()
        logger.info(f"Procesamiento completado. Éxitos: {success_count}, Errores: {error_count}, Desactivados: {deactivated_count}")

        return jsonify({
            'success': True,
            'message': f'Procesamiento completado. Estudiantes actualizados/creados: {success_count}, Desactivados: {deactivated_count}, Errores: {error_count}',
            'success_count': success_count,
            'error_count': error_count,
            'deactivated_count': deactivated_count,
            'errors': errors if errors else None
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error general al procesar Excel: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': f'Error interno del servidor al procesar el archivo: {str(e)}'}), 500

@admin_bp.route('/students', methods=['GET'])
@jwt_required()
@require_admin
def get_students():
    """
    Endpoint para obtener una lista paginada y buscable de estudiantes.
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')

        query = Student.query

        if search:
            query = query.filter(
                (Student.nombre.ilike(f'%{search}%')) |
                (Student.apellido.ilike(f'%{search}%')) |
                (Student.username.ilike(f'%{search}%')) |
                (Student.matricula.ilike(f'%{search}%')) |
                (Student.dni.ilike(f'%{search}%')) |
                (Student.email.ilike(f'%{search}%')) # Añadido email a la búsqueda
            )

        students = query.order_by(Student.apellido, Student.nombre).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'success': True,
            'students': [student.to_dict() for student in students.items],
            'total': students.total,
            'pages': students.pages,
            'current_page': page
        })

    except Exception as e:
        logger.error(f"Error obteniendo estudiantes: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error al obtener estudiantes'}), 500

@admin_bp.route('/student/<username>', methods=['GET'])
@jwt_required()
def get_student_by_username(username):
    """
    Endpoint para obtener la información de un estudiante por su username.
    Solo administradores pueden ver cualquier estudiante; los estudiantes solo pueden ver su propio perfil.
    """
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401

        is_admin = getattr(current_user, 'is_admin', False)
        if not is_admin and current_user.username != username:
            logger.warning(f"Acceso no autorizado: Usuario {current_user.username} intentó ver perfil de {username}.")
            return jsonify({'success': False, 'error': 'Acceso no autorizado. Solo puedes ver tu propio perfil.'}), 403

        student = Student.query.filter_by(username=username).first()

        if not student:
            return jsonify({'success': False, 'error': 'Estudiante no encontrado'}), 404

        return jsonify({
            'success': True,
            'student': student.to_dict()
        })

    except Exception as e:
        logger.error(f"Error obteniendo estudiante {username}: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error al obtener información del estudiante'}), 500

@admin_bp.route('/students/count', methods=['GET'])
@jwt_required()
@require_admin
def get_students_count():
    """
    Endpoint para obtener el conteo total de estudiantes.
    """
    try:
        total_students = Student.query.count()

        return jsonify({
            'success': True,
            'total_students': total_students
        })

    except Exception as e:
        logger.error(f"Error obteniendo conteo de estudiantes: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error al obtener conteo de estudiantes'}), 500
