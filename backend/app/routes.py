from flask import jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from .database import db
from .models import User

# Crear Blueprint para rutas principales
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def main_home():
    return jsonify({'message': 'Bienvenido a la API de TechApp'})

@main_bp.route('/dashboard')
@jwt_required()
def main_dashboard():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
            
        return jsonify({
            'message': f'Bienvenido al dashboard, {user.username}',
            'user': user.username,
            'email': user.email,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"Error en dashboard: {str(e)}")
        return jsonify({'error': 'Error al acceder al dashboard'}), 500

@main_bp.route('/health')
def main_health():
    return jsonify({'status': 'healthy', 'message': 'API funcionando correctamente'})