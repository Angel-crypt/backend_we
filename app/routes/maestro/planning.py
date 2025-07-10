from flask import Blueprint, jsonify, request, session
from app.utils.supabase_connection import supabaseConnection as sC

maestro_planning_bp = Blueprint("maestro_planning", __name__)

from flask import send_from_directory, current_app, jsonify, session
import os

@maestro_planning_bp.route('/planning/<int:id_asignacion>', methods=['GET'])
def get_planning(id_asignacion):
    """Endpoint para obtener y enviar la planificación PDF de un grupo específico."""
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

        # Verificar que la asignación pertenece al maestro y obtener el nombre del archivo
        asignacion_response = supabase.table('asignacion').select(
            'planeacion_pdf_url'
        ).eq('id_asignacion', id_asignacion).eq('id_maestro', user_id).execute()
        
        if not asignacion_response.data:
            return jsonify({
                'success': False,
                'error': 'Asignación no encontrada o no pertenece al maestro'
            }), 403

        planeacion_url = asignacion_response.data[0]['planeacion_pdf_url']

        if not planeacion_url:
            return jsonify({
                'success': False,
                'error': 'No se encontró planificación para este grupo'
            }), 404

        # Extraer solo el nombre del archivo desde la URL (por ejemplo, "/static/uploads/planeaciones/archivo.pdf")
        filename = os.path.basename(planeacion_url)

        # Definir el directorio donde están los PDFs
        directory = os.path.join(os.getcwd(), 'static', 'uploads', 'planeaciones')

        # Verificar que el archivo exista
        file_path = os.path.join(directory, filename)
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'El archivo de planificación no fue encontrado en el servidor'
            }), 404

        # Enviar el archivo PDF
        return send_from_directory(directory, filename)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500


@maestro_planning_bp.route('/planning/<int:id_asignacion>', methods=['POST'])
def upload_planning(id_asignacion):
    """Endpoint para subir o actualizar la planificación de un grupo específico."""
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

        data = request.json
        if not data or 'planeacion_pdf_url' not in data:
            return jsonify({
                'success': False,
                'error': 'Es necesario proporcionar la URL del PDF de planificación'
            }), 400

        planeacion_pdf_url = data['planeacion_pdf_url']

        # Actualizar planificación en la base de datos
        update_response = supabase.table('asignacion').update({
            'planeacion_pdf_url': planeacion_pdf_url
        }).eq('id_asignacion', id_asignacion).execute()

        if not update_response.data:
            return jsonify({
                'success': False,
                'error': 'Error al actualizar la planificación'
            }), 500

        return jsonify({
            'success': True,
            'message': 'Planificación actualizada exitosamente'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500
