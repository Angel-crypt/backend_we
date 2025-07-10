from flask import Blueprint, jsonify
from app.utils.supabase_connection import supabaseConnection as sC
from app.models import Alumno

alumnos_admin_bp = Blueprint("alumnos_admin", __name__)

# Ruta para obtener todos los alumnos
@alumnos_admin_bp.route('/alumnos')
def get_alumnos():
    """"Endpoint para obtener todos los alumnos registrados en la base de datos."""
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Consultar datos de alumnos
        response = supabase.table('alumno').select('*').execute()
        
        # Convertir datos a objetos Alumno y usar to_dict()
        alumnos = [Alumno.from_dict(row) for row in response.data]
        alumnos_data = [alumno.to_dict() for alumno in alumnos]
        
        return jsonify({
            'success': True,
            'data': alumnos_data,
            'total': len(alumnos_data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Ruta para obtener un alumno por ID
@alumnos_admin_bp.route('/alumnos/<string:id_alumno>')
def get_alumno(id_alumno):
    """Endpoint para obtener un alumno por su ID."""
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Consultar datos del alumno
        response = supabase.table('alumno').select('*').eq('id_alumno', id_alumno).execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'Alumno no encontrado'
            }), 404
        
        # Convertir a objeto Alumno y usar to_dict()
        alumno = Alumno.from_dict(response.data[0])
        
        return jsonify({
            'success': True,
            'data': alumno.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Ruta para obtener alumnos por nombre completo
@alumnos_admin_bp.route('/alumnos/nombre/<string:nombre>')
def get_alumno_by_name(nombre):
    """Endpoint para obtener un alumno por su nombre completo.
    
    Busca en nombre, apellido_paterno y apellido_materno usando palabras clave.
    El usuario puede enviar cualquier combinación de nombre y apellidos.
    """
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Limpiar y preparar el término de búsqueda
        nombre_limpio = nombre.strip()
        
        # Dividir el nombre en palabras para buscar individualmente
        palabras = nombre_limpio.split()
        
        # Construir consulta flexible que busque en nombre, apellido_paterno y apellido_materno
        query = supabase.table('alumno').select('*')
        
        # Para cada palabra, buscar en cualquiera de los campos de nombre
        for palabra in palabras:
            # Usar or_ para buscar la palabra en cualquiera de los tres campos
            query = query.or_(
                f'nombre.ilike.%{palabra}%,'
                f'apellido_paterno.ilike.%{palabra}%,'
                f'apellido_materno.ilike.%{palabra}%'
            )
        
        response = query.execute()
        
        # Si no hay resultados, intentar búsqueda más amplia con el texto completo
        if not response.data:
            # Búsqueda alternativa: concatenar campos y buscar el texto completo
            response = supabase.table('alumno').select('*').or_(
                f'nombre.ilike.%{nombre_limpio}%,'
                f'apellido_paterno.ilike.%{nombre_limpio}%,'
                f'apellido_materno.ilike.%{nombre_limpio}%'
            ).execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': f'No se encontraron alumnos con el nombre: {nombre_limpio}',
                'searched_term': nombre_limpio
            }), 404
        
        # Convertir datos a objetos Alumno y usar to_dict()
        alumnos = [Alumno.from_dict(row) for row in response.data]
        alumnos_data = [alumno.to_dict() for alumno in alumnos]
        
        # Ordenar resultados por relevancia (opcional)
        # Priorizar coincidencias exactas en nombre
        alumnos_data.sort(key=lambda x: (
            # Prioridad 1: coincidencia exacta en nombre
            not x['nombre'].lower().startswith(nombre_limpio.lower()),
            # Prioridad 2: coincidencia exacta en apellido paterno (si existe)
            not (x.get('apellido_paterno') and x['apellido_paterno'].lower().startswith(nombre_limpio.lower())),
            # Prioridad 3: orden alfabético por nombre completo
            x['nombre_completo'].lower()
        ))
        
        return jsonify({
            'success': True,
            'data': alumnos_data,
            'total': len(alumnos_data),
            'searched_term': nombre_limpio
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}',
            'searched_term': nombre
        }), 500

# Ruta para obtener alumnos por grupo
@alumnos_admin_bp.route('/alumnos/grupo/<string:id_grupo>')
def get_alumnos_by_group(id_grupo):
    """Endpoint para obtener alumnos por ID de grupo."""
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Consultar datos de alumnos en el grupo especificado
        response = supabase.table('alumno').select('*').eq('id_grupo', id_grupo).execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron alumnos en este grupo'
            }), 404
        
        # Convertir datos a objetos Alumno y usar to_dict()
        alumnos = [Alumno.from_dict(row) for row in response.data]
        alumnos_data = [alumno.to_dict() for alumno in alumnos]
        
        return jsonify({
            'success': True,
            'data': alumnos_data,
            'total': len(alumnos_data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

