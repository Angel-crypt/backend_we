from flask import Blueprint, jsonify, request, session
from app.utils.supabase_connection import supabaseConnection as sC
from app.services.calificacion_service import puede_subir_calificacion

maestro_grades_bp = Blueprint("maestro_grades", __name__)

@maestro_grades_bp.route('/grades/<int:id_asignacion>/<int:numero_parcial>', methods=['GET'])
def get_grades(id_asignacion, numero_parcial):
    """Endpoint para obtener calificaciones de un parcial específico de una asignación."""
    try:
        # Verificar autenticación
        if 'user_id' not in session or 'role' not in session:
            return jsonify({
                'success': False,
                'error': 'No autenticado'
            }), 401

        if session['role'] != 'maestro':
            return jsonify({
                'success': False,
                'error': 'Acceso denegado - Solo maestros'
            }), 403
        
        user_id = session['user_id']
        supabase = sC.get_instance().get_client()

        # Verificar que la asignación pertenece al maestro
        asignacion_response = supabase.table('asignacion').select(
            'id_asignacion'
        ).eq('id_asignacion', id_asignacion).eq('id_maestro', user_id).execute()
        
        if not asignacion_response.data:
            return jsonify({
                'success': False,
                'error': 'Asignación no encontrada o no pertenece al maestro'
            }), 403

        # Obtener calificaciones
        calificaciones_response = supabase.table('calificaciones').select(
            '*'
        ).eq('id_asignacion', id_asignacion).execute()
        
        if not calificaciones_response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron calificaciones'
            }), 404

        return jsonify({
            'success': True,
            'data': calificaciones_response.data,
            'total_calificaciones': len(calificaciones_response.data)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@maestro_grades_bp.route('/grades/<int:id_asignacion>/<int:numero_parcial>', methods=['POST'])
def upload_grades(id_asignacion, numero_parcial):
    """Endpoint para subir o actualizar calificaciones."""
    try:
        # Verificar autenticación
        if 'user_id' not in session or 'role' not in session:
            return jsonify({
                'success': False,
                'error': 'No autenticado'
            }), 401

        if session['role'] != 'maestro':
            return jsonify({
                'success': False,
                'error': 'Acceso denegado - Solo maestros'
            }), 403
        
        user_id = session['user_id']
        supabase = sC.get_instance().get_client()

        # Verificar que la asignación pertenece al maestro
        asignacion_response = supabase.table('asignacion').select(
            'id_asignacion'
        ).eq('id_asignacion', id_asignacion).eq('id_maestro', user_id).execute()
        
        if not asignacion_response.data:
            return jsonify({
                'success': False,
                'error': 'Asignación no encontrada o no pertenece al maestro'
            }), 403

        # Verificar si se puede subir calificaciones
        calificacion_status = puede_subir_calificacion(id_asignacion, numero_parcial)
        if not calificacion_status['status']:
            return jsonify({
                'success': False,
                'error': calificacion_status['mensaje']
            }), 403

        data = request.json
        if not data or not isinstance(data, list):
            return jsonify({
                'success': False,
                'error': 'Es necesario proveer una lista de calificaciones'
            }), 400

        # Procesar y subir calificaciones
        for calificacion in data:
            if 'id_alumno' not in calificacion or 'calificacion' not in calificacion:
                return jsonify({
                    'success': False,
                    'error': 'Cada objeto de calificación debe tener "id_alumno" y "calificacion"'
                }), 400

            # Actualizar calificación
            update_response = supabase.table('calificaciones').update({
                f'parcial_{numero_parcial}': calificacion['calificacion']
            }).eq('id_alumno', calificacion['id_alumno']).eq('id_asignacion', id_asignacion).execute()

            if not update_response.data:
                return jsonify({
                    'success': False,
                    'error': f'No se pudo actualizar la calificación para el alumno {calificacion["id_alumno"]}'
                }), 500

        return jsonify({
            'success': True,
            'message': 'Calificaciones subidas exitosamente'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500
