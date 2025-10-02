# FileName: /pagina-web-main/backend/app/models.py
from .database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True) # Email también debería ser único
    password_hash = db.Column(db.String)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=True)
    student = db.relationship('Student', backref='user', uselist=False)


    def __init__(self, username, email, is_admin=False, student_id=None):
        self.username = username
        self.email = email
        self.is_admin = is_admin
        self.student_id = student_id

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_jwt_token(self):
        return create_access_token(identity=self.id)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_admin': self.is_admin,
            'student_id': self.student_id
        }

    def __repr__(self):
        return f'<User {self.username}>'

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    grado = db.Column(db.String(20), nullable=False)
    seccion = db.Column(db.String(10), nullable=False)
    turno = db.Column(db.String(20), nullable=False)
    especialidad = db.Column(db.String(100), nullable=True)
    matricula = db.Column(db.String(50), unique=True, nullable=False)
    estado = db.Column(db.String(50), default='Activo')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'dni': self.dni,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'username': self.username,
            'email': self.email,
            'grado': self.grado,
            'seccion': self.seccion,
            'turno': self.turno,
            'especialidad': self.especialidad,
            'matricula': self.matricula,
            'estado': self.estado,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Student {self.username}>'
