from flask import Blueprint, jsonify, request, session
from app.utils.supabase_connection import supabaseConnection as sC

maestro_planning_bp = Blueprint("maestro_planning", __name__)

def _get_public_url(supabase, path):
    """Obtiene la URL pública de un archivo en Supabase Storage."""
    url_response = supabase.storage.from_("pdfs").get_public_url(path)
    
    # Manejar diferentes tipos de respuesta de Supabase
    if isinstance(url_response, dict):
        return url_response.get('publicUrl')
    elif isinstance(url_response, str):
        return url_response
    else:
        # Si tiene atributo publicUrl
        return getattr(url_response, 'publicUrl', None)

@maestro_planning_bp.route('/planning/<int:id_asignacion>', methods=['POST'])
def upload_planning(id_asignacion):
    """Subir planificación a Supabase Storage y guardar su URL en la DB."""
    try:
        user_id = session['user_id']
        supabase = sC.get_instance().get_client()
        
        # Validar que la asignación pertenezca al maestro
        asignacion_response = supabase.table('asignacion').select(
            'id_asignacion'
        ).eq('id_asignacion', id_asignacion).eq('id_maestro', user_id).execute()
        
        if not asignacion_response.data:
            return jsonify({'success': False, 'error': 'Asignación no encontrada'}), 404
        
        file = request.files.get('file')
        if not file:
            return jsonify({'success': False, 'error': 'No se envió archivo'}), 400
        
        # Preparar archivo para subida
        filename = f"asignacion_{id_asignacion}.pdf"
        path = f"planeaciones/{filename}"
        
        # Leer el archivo solo una vez
        file_content = file.read()

        # Subir con upsert = true
        try:
            supabase.storage.from_("pdfs").upload(
                path,
                file_content,
                {
                    "content-type": "application/pdf",
                    "upsert": "true"
                }
            )
        except Exception as upload_error:
            return jsonify({'success': False, 'error': f'Error al subir archivo: {str(upload_error)}'}), 500


        
        # Obtener URL pública
        public_url = _get_public_url(supabase, path)
        if not public_url:
            return jsonify({'success': False, 'error': 'Error obteniendo URL'}), 500
        
        # Actualizar base de datos
        supabase.table('asignacion').update({
            'planeacion_pdf_url': public_url
        }).eq('id_asignacion', id_asignacion).execute()
        
        return jsonify({
            'success': True,
            'url': public_url,
            'message': 'Planificación subida correctamente'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@maestro_planning_bp.route('/planning/<int:id_asignacion>', methods=['GET'])
def get_planning(id_asignacion):
    """Obtiene la URL pública del PDF de planificación."""
    try:
        user_id = session['user_id']
        supabase = sC.get_instance().get_client()
        
        # Obtener URL de la planificación
        asignacion_response = supabase.table('asignacion').select(
            'planeacion_pdf_url'
        ).eq('id_asignacion', id_asignacion).eq('id_maestro', user_id).execute()
        
        if not asignacion_response.data:
            return jsonify({'success': False, 'error': 'Asignación no encontrada'}), 404
        
        url = asignacion_response.data[0]['planeacion_pdf_url']
        if not url:
            return jsonify({'success': False, 'error': 'No hay planificación registrada'}), 404
        
        return jsonify({'success': True, 'url': url})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500