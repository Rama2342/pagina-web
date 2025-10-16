from .database import db
from .models import User, Student
from .auth import auth_bp
from .routes import main_bp
from .admin import admin_bp

__all__ = ['db', 'User', 'Student', 'auth_bp', 'main_bp', 'admin_bp']