from flask import Blueprint, jsonify, request
import os
from flask import send_from_directory
from app.services.fechas_parciales_service import crear_fecha_parcial
from urllib.parse import urlparse
from datetime import datetime
from app.utils.supabase_connection import supabaseConnection as sC

asignaciones_admin_bp = Blueprint("asignaciones_admin", __name__)

# == Ruta para gestion de asignaciones ==
# Listar asignaciones
@asignaciones_admin_bp.route('/asignaciones')
def get_asignaciones():
    """
    Endpoint para obtener todas las asignaciones registradas en la base de datos.
    """
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Consultar datos de asignaciones
        response = supabase.table('asignacion').select(
            'id_asignacion, id_curso, id_grupo, id_maestro, curso(nombre), grupo(nombre_grupo), maestro(nombre, apellido_paterno)'
        ).execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron asignaciones'
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

@asignaciones_admin_bp.route('/asignaciones/<string:id_asignacion>/planeacion', methods=['GET'])
def ver_pdf_planeacion_asignacion(id_asignacion):
    """
    Devuelve directamente el archivo PDF asociado a una asignación.
    """
    try:
        # Validar ID
        if not id_asignacion.isdigit() or int(id_asignacion) <= 0:
            return jsonify({'success': False, 'error': 'ID de asignación inválido'}), 400

        # Supabase
        supabase = sC.get_instance().get_client()
        response = supabase.table('asignacion').select("planeacion_pdf_url").eq('id_asignacion', id_asignacion).execute()

        if not response.data:
            return jsonify({'success': False, 'error': 'Asignación no encontrada'}), 404

        pdf_url = response.data[0].get("planeacion_pdf_url")
        if not pdf_url:
            return jsonify({'success': False, 'error': 'Asignación no tiene planeación PDF'}), 404

        # Si es ruta local (no una URL completa tipo http)
        parsed = urlparse(pdf_url)
        if not parsed.netloc:
            filename = os.path.basename(pdf_url)
            directory = os.path.join(os.getcwd(), 'static', 'uploads', 'planeaciones')
            return send_from_directory(directory, filename)

        # Si es una URL completa externa, redirigir
        return jsonify({'success': True, 'external_url': pdf_url}), 200

    except Exception as e:
        print(f"Error al servir planeación: {e}")
        return jsonify({'success': False, 'error': 'Error interno'}), 500
