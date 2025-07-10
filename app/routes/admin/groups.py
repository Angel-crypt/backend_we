from flask import Blueprint, jsonify
from app.utils.supabase_connection import supabaseConnection as sC

grupos_admin_bp = Blueprint("grupos_admin", __name__)


# == Ruta para la gestion de grupos ==
@grupos_admin_bp.route('/grupos')
def get_grupos():
    """
    Endpoint para obtener todos los grupos registrados en la base de datos.
    """
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Consultar datos de grupos
        response = supabase.table('grupo').select('*').execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron grupos'
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

# ver grupos por id, nombre o codigo
@grupos_admin_bp.route('/grupos/<string:identificador>')
def get_grupo(identificador):
    """
    Endpoint para obtener un grupo por su ID, nombre o código.
    """
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Limpiar y preparar el identificador
        identificador_limpio = identificador.strip().upper()  # Normalizar a mayúsculas
        
        # Consultar por ID de grupo
        response = supabase.table('grupo').select('*').eq('id_grupo', identificador_limpio).execute()
        
        if not response.data:
            # Si no se encuentra por ID, buscar por nombre o código
            response = supabase.table('grupo').select('*').or_(
                f'nombre_grupo.ilike.%{identificador_limpio}%,'
                f'codigo.ilike.%{identificador_limpio}%'
            ).execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': f'No se encontró ningún grupo con el identificador: {identificador_limpio}',
                'searched_term': identificador_limpio
            }), 404
        
        return jsonify({
            'success': True,
            'data': response.data[0],
            'searched_term': identificador_limpio
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}',
            'searched_term': identificador
        }), 500
