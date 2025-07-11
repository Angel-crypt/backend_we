import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.secret_key = os.environ.get("SECRET_KEY")
    
    api_version = 'v1'

    from app.routes import admin_bp, maestro_bp
    app.register_blueprint(admin_bp, url_prefix=f'/{api_version}/admin')
    app.register_blueprint(maestro_bp, url_prefix=f'/{api_version}/maestro')

    return app
