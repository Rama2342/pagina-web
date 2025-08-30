import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Clave secreta para sesiones y tokens
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu-clave-super-secreta-aqui-cambia-en-produccion'
    
    # Configuración de base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-clave-super-secreta-cambia-en-produccion'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)