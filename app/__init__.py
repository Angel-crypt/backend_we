from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)  # Permitir frontend Angular

    from app.routes import admin_bp, maestro_bp, static_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(maestro_bp, url_prefix='/maestro')
    app.register_blueprint(static_bp, url_prefix='/static-files')

    return app
