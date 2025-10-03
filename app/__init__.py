from flask import Flask
from app.database import db

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Solo crea tablas en app.db
    return app