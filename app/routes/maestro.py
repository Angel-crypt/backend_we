from flask import Blueprint

maestro_bp = Blueprint('maestro', __name__)

@maestro_bp.route('/ping')
def ping():
    return {'msg': 'pong'}
