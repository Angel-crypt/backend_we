from flask import Blueprint, jsonify, session
from app.utils.supabase_connection import supabaseConnection as sC
from .auth import admin_auth_bp, admin_required
from .grades import grades_admin_bp
from .alums import alumnos_admin_bp
from .teachers import maestros_admin_bp
from .courses import cursos_admin_bp
from .groups import grupos_admin_bp
from .assignments import asignaciones_admin_bp

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route('/ping')
@admin_required
def ping():
    return {'msg': 'pong'}

@admin_bp.route('/parciales')
@admin_required
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

@admin_bp.route('/parciales', methods=['POST'])
@admin_required
def create_partial_period():
    """
    Endpoint para crear un nuevo periodo de calificaciones parciales.
    """
    try:
        from flask import request
        from datetime import datetime
        
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos JSON'
            }), 400
        
        # Validar campos requeridos
        required_fields = ['id_asignacion', 'numero_parcial', 'fecha_inicio', 'fecha_fin']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
            }), 400
        
        # Validar formato de fechas
        try:
            datetime.fromisoformat(data['fecha_inicio'])
            datetime.fromisoformat(data['fecha_fin'])
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Formato de fecha inválido. Use formato ISO (YYYY-MM-DDTHH:MM:SS)'
            }), 400
        
        # Validar número de parcial
        if not isinstance(data['numero_parcial'], int) or data['numero_parcial'] < 1 or data['numero_parcial'] > 3:
            return jsonify({
                'success': False,
                'error': 'El número de parcial debe ser 1, 2 o 3'
            }), 400
        
        supabase = sC.get_instance().get_client()
        
        # Verificar que la asignación existe
        asignacion_response = supabase.table('asignacion').select('id_asignacion').eq('id_asignacion', data['id_asignacion']).execute()
        if not asignacion_response.data:
            return jsonify({
                'success': False,
                'error': 'La asignación especificada no existe'
            }), 404
        
        # Verificar que no existe ya un periodo para esta asignación y parcial
        existing_response = supabase.table('fechas_parciales').select('*').eq('id_asignacion', data['id_asignacion']).eq('numero_parcial', data['numero_parcial']).execute()
        if existing_response.data:
            return jsonify({
                'success': False,
                'error': f'Ya existe un periodo para el parcial {data["numero_parcial"]} de esta asignación'
            }), 409
        
        # Crear el periodo de calificaciones
        periodo_data = {
            'id_asignacion': data['id_asignacion'],
            'numero_parcial': data['numero_parcial'],
            'fecha_inicio': data['fecha_inicio'],
            'fecha_fin': data['fecha_fin']
        }
        
        create_response = supabase.table('fechas_parciales').insert(periodo_data).execute()
        
        if not create_response.data:
            return jsonify({
                'success': False,
                'error': 'Error al crear el periodo de calificaciones'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Periodo de calificaciones creado exitosamente',
            'data': create_response.data[0]
        }), 201
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@admin_bp.route('/parciales/<int:id_fecha_parcial>', methods=['PUT'])
@admin_required
def update_partial_period(id_fecha_parcial):
    """
    Endpoint para actualizar un periodo de calificaciones parciales.
    """
    try:
        from flask import request
        from datetime import datetime
        
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos JSON'
            }), 400
        
        supabase = sC.get_instance().get_client()
        
        # Verificar que el periodo existe
        existing_response = supabase.table('fechas_parciales').select('*').eq('id_fecha_parcial', id_fecha_parcial).execute()
        if not existing_response.data:
            return jsonify({
                'success': False,
                'error': 'Periodo de calificaciones no encontrado'
            }), 404
        
        # Campos permitidos para actualización
        allowed_fields = ['fecha_inicio', 'fecha_fin']
        update_data = {field: data[field] for field in allowed_fields if field in data}
        
        # Validar formato de fechas si se proporcionan
        for field in ['fecha_inicio', 'fecha_fin']:
            if field in update_data:
                try:
                    datetime.fromisoformat(update_data[field])
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': f'Formato de fecha inválido en {field}. Use formato ISO (YYYY-MM-DDTHH:MM:SS)'
                    }), 400
        
        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron campos válidos para actualizar'
            }), 400
        
        # Actualizar el periodo
        update_response = supabase.table('fechas_parciales').update(update_data).eq('id_fecha_parcial', id_fecha_parcial).execute()
        
        if not update_response.data:
            return jsonify({
                'success': False,
                'error': 'Error al actualizar el periodo de calificaciones'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Periodo de calificaciones actualizado exitosamente',
            'data': update_response.data[0]
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@admin_bp.route('/parciales/<int:id_fecha_parcial>', methods=['DELETE'])
@admin_required
def delete_partial_period(id_fecha_parcial):
    """
    Endpoint para eliminar un periodo de calificaciones parciales.
    """
    try:
        supabase = sC.get_instance().get_client()
        
        # Verificar que el periodo existe
        existing_response = supabase.table('fechas_parciales').select('*').eq('id_fecha_parcial', id_fecha_parcial).execute()
        if not existing_response.data:
            return jsonify({
                'success': False,
                'error': 'Periodo de calificaciones no encontrado'
            }), 404
        
        periodo_info = existing_response.data[0]
        
        # Eliminar el periodo
        delete_response = supabase.table('fechas_parciales').delete().eq('id_fecha_parcial', id_fecha_parcial).execute()
        
        if not delete_response.data:
            return jsonify({
                'success': False,
                'error': 'Error al eliminar el periodo de calificaciones'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Periodo de calificaciones eliminado exitosamente',
            'data': periodo_info
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    """
    Dashboard principal para administradores con estadísticas del sistema.
    """
    try:
        supabase = sC.get_instance().get_client()
        
        # Obtener estadísticas generales
        stats = {}
        
        # Contar maestros
        maestros_response = supabase.table('maestro').select('id_usuario', count='exact').execute()
        stats['total_maestros'] = maestros_response.count or 0
        
        # Contar alumnos
        alumnos_response = supabase.table('alumno').select('id_alumno', count='exact').execute()
        stats['total_alumnos'] = alumnos_response.count or 0
        
        # Contar grupos
        grupos_response = supabase.table('grupo').select('id_grupo', count='exact').execute()
        stats['total_grupos'] = grupos_response.count or 0
        
        # Contar cursos
        cursos_response = supabase.table('curso').select('id_curso', count='exact').execute()
        stats['total_cursos'] = cursos_response.count or 0
        
        # Contar asignaciones
        asignaciones_response = supabase.table('asignacion').select('id_asignacion', count='exact').execute()
        stats['total_asignaciones'] = asignaciones_response.count or 0
        
        # Contar periodos de calificaciones activos
        from datetime import datetime
        now = datetime.now().isoformat()
        parciales_activos_response = supabase.table('fechas_parciales').select('id_fecha_parcial', count='exact').lte('fecha_inicio', now).gte('fecha_fin', now).execute()
        stats['parciales_activos'] = parciales_activos_response.count or 0
        
        return jsonify({
            'success': True,
            'data': {
                'estadisticas': stats,
                'user_info': {
                    'user_id': session['user_id'],
                    'role': session['role']
                }
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

# Registrar sub-blueprints
admin_bp.register_blueprint(admin_auth_bp)
admin_bp.register_blueprint(grades_admin_bp)
admin_bp.register_blueprint(alumnos_admin_bp)
admin_bp.register_blueprint(maestros_admin_bp)
admin_bp.register_blueprint(cursos_admin_bp)
admin_bp.register_blueprint(grupos_admin_bp)
admin_bp.register_blueprint(asignaciones_admin_bp)
