from flask import Blueprint, jsonify
from app.utils.supabase_connection import supabaseConnection as sC
from .alumnos import alumnos_admin_bp
from .maestros import maestros_admin_bp
from .cursos import cursos_admin_bp
from .grupos import grupos_admin_bp
from .asignaciones import asignaciones_admin_bp

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route('/ping')
def ping():
    return {'msg': 'pong'}

@admin_bp.route('/parciales')
def get_parciales():
    """
    Endpoint para obtener todas las fechas parciales registradas en la base de datos.
    """
    try:
        supabase = sC.get_instance().get_client()

        response = supabase.table('fechas_parciales').select('*').execute()

        if not response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron fechas parciales'
            }), 404

        return jsonify({
            'success': True,
            'data': response.data,
            'total': len(response.data)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Registrar sub-blueprints
admin_bp.register_blueprint(alumnos_admin_bp)
admin_bp.register_blueprint(maestros_admin_bp)
admin_bp.register_blueprint(cursos_admin_bp)
admin_bp.register_blueprint(grupos_admin_bp)
admin_bp.register_blueprint(asignaciones_admin_bp)
