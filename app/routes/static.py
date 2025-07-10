from flask import send_from_directory, Blueprint
import os

static_bp = Blueprint('static_bp', __name__)

@static_bp.route('/planeaciones/<path:filename>', methods=['GET'])
def get_planeacion(filename):
    directory = os.path.join(os.getcwd(), 'static', 'uploads', 'planeaciones')
    return send_from_directory(directory, filename)