from flask import Blueprint, jsonify, request, session
from app.utils.supabase_connection import supabaseConnection as sC
from .auth import maestro_auth_bp
from .profile import maestro_profile_bp
from .groups import maestro_groups_bp
from .grades import maestro_grades_bp
from .planning import maestro_planning_bp

maestro_bp = Blueprint("maestro", __name__, url_prefix="/maestro")

@maestro_bp.route('/ping')
def ping():
    """Endpoint para verificar que el servicio de maestros está funcionando"""
    return jsonify({'msg': 'maestro service is running'})

@maestro_bp.route('/dashboard')
def dashboard():
    """Dashboard principal para maestros - información general"""
    try:
        # Verificar si el usuario está autenticado
        if 'user_id' not in session or 'role' not in session:
            return jsonify({
                'success': False,
                'error': 'No autenticado'
            }), 401
        
        # Verificar que el usuario sea maestro
        if session['role'] != 'maestro':
            return jsonify({
                'success': False,
                'error': 'Acceso denegado - Solo maestros'
            }), 403
        
        user_id = session['user_id']
        supabase = sC.get_instance().get_client()
        
        # Obtener información básica del maestro
        maestro_response = supabase.table('maestro').select('*').eq('id_usuario', user_id).execute()
        if not maestro_response.data:
            return jsonify({
                'success': False,
                'error': 'Maestro no encontrado'
            }), 404
        
        maestro_info = maestro_response.data[0]
        
        # Obtener resumen de asignaciones
        asignaciones_response = supabase.table('asignacion').select(
            'id_asignacion, curso(nombre, codigo), grupo(nombre_grupo)'
        ).eq('id_maestro', user_id).execute()
        
        # Obtener disponibilidad
        disponibilidad_response = supabase.table('disponibilidad').select('*').eq('id_maestro', user_id).execute()
        
        return jsonify({
            'success': True,
            'data': {
                'maestro': maestro_info,
                'asignaciones': asignaciones_response.data,
                'disponibilidad': disponibilidad_response.data,
                'total_asignaciones': len(asignaciones_response.data),
                'total_disponibilidad': len(disponibilidad_response.data)
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

# Registrar sub-blueprints
maestro_bp.register_blueprint(maestro_auth_bp)
maestro_bp.register_blueprint(maestro_profile_bp)
maestro_bp.register_blueprint(maestro_groups_bp)
maestro_bp.register_blueprint(maestro_grades_bp)
maestro_bp.register_blueprint(maestro_planning_bp)
