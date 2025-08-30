from flask import request, jsonify, Blueprint
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .database import db
from .models import User

# Crear Blueprint para autenticación
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def auth_login():
    try:
        data = request.get_json()
        print(f"Datos recibidos: {data}")
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Se requieren username y password'}), 400
            
        user = User.query.filter_by(username=data.get('username')).first()
        
        if user and user.check_password(data.get('password')):
            token = create_access_token(identity=user.id)
            return jsonify({
                'token': token, 
                'user_id': user.id,
                'username': user.username,
                'message': 'Login exitoso'
            })
        
        return jsonify({'error': 'Credenciales inválidas'}), 401
        
    except Exception as e:
        print(f"Error en login: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@auth_bp.route('/register', methods=['POST'])
def auth_register():
    try:
        data = request.get_json()
        print(f"Datos de registro: {data}")
        
        # Validar campos requeridos
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'El campo {field} es requerido'}), 400
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(username=data.get('username')).first():
            return jsonify({'error': 'El usuario ya existe'}), 400
        
        # Verificar si el email ya existe
        if User.query.filter_by(email=data.get('email')).first():
            return jsonify({'error': 'El email ya está registrado'}), 400
        
        # Crear nuevo usuario
        user = User(username=data.get('username'), email=data.get('email'))
        user.set_password(data.get('password'))
        
        db.session.add(user)
        db.session.commit()
        
        print(f"Usuario creado exitosamente: {user.username}")
        return jsonify({
            'message': 'Usuario creado exitosamente',
            'user_id': user.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al crear usuario: {str(e)}")
        return jsonify({'error': f'Error al crear usuario: {str(e)}'}), 500

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def auth_protected():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
            
        return jsonify({
            'message': 'Acceso permitido',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
        
    except Exception as e:
        print(f"Error en endpoint protegido: {str(e)}")
        return jsonify({'error': 'Error de autenticación'}), 401

@auth_bp.route('/user', methods=['GET'])
@jwt_required()
def auth_get_user():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
            
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        })
        
    except Exception as e:
        print(f"Error obteniendo usuario: {str(e)}")
        return jsonify({'error': 'Error al obtener información del usuario'}), 500