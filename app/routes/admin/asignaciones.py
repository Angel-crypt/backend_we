from flask import Blueprint, jsonify, request
import requests
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

# Ver planeación PDF de una asignación
@asignaciones_admin_bp.route('/asignaciones/<string:id_asignacion>/planeacion', methods=['GET'])
def get_planeacion_asignacion(id_asignacion):
    """
    Endpoint para obtener la planeación de una asignación en formato PDF.
    """
    try:
        # Validar formato del ID
        if not id_asignacion:
            return jsonify({
                'success': False,
                'error': 'ID de asignación es requerido'
            }), 400
            
        if not isinstance(id_asignacion, str):
            return jsonify({
                'success': False,
                'error': 'ID de asignación debe ser una cadena'
            }), 400
            
        # Validar que sea un número entero válido (ya que id_asignacion es SERIAL)
        try:
            id_asignacion_int = int(id_asignacion)
            if id_asignacion_int <= 0:
                return jsonify({
                    'success': False,
                    'error': 'ID de asignación debe ser un número entero positivo'
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'ID de asignación debe ser un número entero válido'
            }), 400

        # Obtener parámetros de consulta
        validate_url = request.args.get('validate_url', 'false').lower() == 'true'
        include_metadata = request.args.get('include_metadata', 'false').lower() == 'true'

        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Consultar la asignación por ID con información relacionada
        response = supabase.table('asignacion').select(
            """
            id_asignacion, 
            planeacion_pdf_url,
            curso(id_curso, nombre, codigo, descripcion),
            grupo(id_grupo, nombre_grupo, generacion, facultad),
            maestro(id_usuario, nombre, apellido_paterno, apellido_materno, especialidad)
            """
        ).eq('id_asignacion', id_asignacion).execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'Asignación no encontrada',
                'id_asignacion': id_asignacion
            }), 404

        asignacion = response.data[0]
        
        # Verificar si tiene planeación PDF
        pdf_url = asignacion.get('planeacion_pdf_url')
        if not pdf_url or not pdf_url.strip():
            return jsonify({
                'success': False,
                'error': 'No se encontró planeación PDF para esta asignación',
                'id_asignacion': id_asignacion,
                'curso': asignacion.get('curso', {}).get('nombre', 'N/A'),
                'grupo': asignacion.get('grupo', {}).get('nombre_grupo', 'N/A')
            }), 404

        # Validar formato de URL
        parsed_url = urlparse(pdf_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return jsonify({
                'success': False,
                'error': 'URL de planeación PDF inválida',
                'id_asignacion': id_asignacion,
                'url_invalida': pdf_url
            }), 400

        # Preparar información del curso
        curso_info = asignacion.get('curso', {})
        grupo_info = asignacion.get('grupo', {})
        maestro_info = asignacion.get('maestro', {})
        
        # Construir nombre completo del maestro
        maestro_nombre = maestro_info.get('nombre', '')
        maestro_apellido_paterno = maestro_info.get('apellido_paterno', '')
        maestro_apellido_materno = maestro_info.get('apellido_materno', '')
        
        nombre_completo_maestro = f"{maestro_nombre} {maestro_apellido_paterno}".strip()
        if maestro_apellido_materno:
            nombre_completo_maestro += f" {maestro_apellido_materno}"
        
        # Validar accesibilidad de la URL si se solicita
        url_status = None
        if validate_url:
            try:
                # Hacer una petición HEAD para verificar si la URL es accesible
                head_response = requests.head(pdf_url, timeout=10, allow_redirects=True)
                url_status = {
                    'accesible': head_response.status_code == 200,
                    'codigo_estado': head_response.status_code,
                    'content_type': head_response.headers.get('content-type', 'N/A'),
                    'content_length': head_response.headers.get('content-length', 'N/A')
                }
                
                # Verificar si realmente es un PDF
                content_type = head_response.headers.get('content-type', '').lower()
                if 'application/pdf' not in content_type:
                    url_status['es_pdf'] = False
                    url_status['advertencia'] = 'El archivo no parece ser un PDF'
                else:
                    url_status['es_pdf'] = True
                    
            except requests.exceptions.RequestException as e:
                url_status = {
                    'accesible': False,
                    'error': str(e),
                    'codigo_estado': None
                }
                
                # Si la URL no es accesible y se solicitó validación, retornar error
                return jsonify({
                    'success': False,
                    'error': 'URL de planeación PDF no accesible',
                    'id_asignacion': id_asignacion,
                    'url_error': str(e),
                    'planeacion_pdf_url': pdf_url
                }), 503

        # Preparar respuesta base
        response_data = {
            'id_asignacion': asignacion['id_asignacion'],
            'planeacion_pdf_url': pdf_url,
            'curso': {
                'id_curso': curso_info.get('id_curso', 'N/A'),
                'nombre': curso_info.get('nombre', 'N/A'),
                'codigo': curso_info.get('codigo', 'N/A')
            },
            'grupo': {
                'id_grupo': grupo_info.get('id_grupo', 'N/A'),
                'nombre_grupo': grupo_info.get('nombre_grupo', 'N/A'),
                'generacion': grupo_info.get('generacion', 'N/A'),
                'facultad': grupo_info.get('facultad', 'N/A')
            },
            'maestro': {
                'id_usuario': maestro_info.get('id_usuario', 'N/A'),
                'nombre_completo': nombre_completo_maestro or 'N/A',
                'especialidad': maestro_info.get('especialidad', 'N/A')
            }
        }

        # Agregar metadata adicional si se solicita
        if include_metadata:
            response_data['metadata'] = {
                'curso_descripcion': curso_info.get('descripcion', 'N/A'),
                'url_dominio': parsed_url.netloc,
                'url_esquema': parsed_url.scheme,
                'maestro_nombres_separados': {
                    'nombre': maestro_info.get('nombre', 'N/A'),
                    'apellido_paterno': maestro_info.get('apellido_paterno', 'N/A'),
                    'apellido_materno': maestro_info.get('apellido_materno', 'N/A')
                },
                'consulta_timestamp': datetime.now().isoformat()
            }

        # Agregar información de validación de URL si se solicitó
        if validate_url and url_status:
            response_data['url_validation'] = url_status

        return jsonify({
            'success': True,
            'message': 'Planeación PDF encontrada exitosamente',
            'data': response_data
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Error de validación: {str(e)}',
            'error_type': 'validation_error',
            'id_asignacion': id_asignacion
        }), 400
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Error al validar URL: {str(e)}',
            'error_type': 'url_validation_error',
            'id_asignacion': id_asignacion
        }), 503
        
    except Exception as e:
        # Log del error para debugging
        print(f"Error al obtener planeación para asignación {id_asignacion}: {str(e)}")
        
        # Determinar el tipo de error
        error_message = 'Error interno del servidor'
        status_code = 500
        
        # Errores específicos de Supabase
        if 'PGRST' in str(e):
            error_message = 'Error de base de datos. Verifique la conexión'
        elif 'network' in str(e).lower():
            error_message = 'Error de conexión a la base de datos'
        elif 'permission' in str(e).lower():
            error_message = 'Error de permisos en la base de datos'
            
        return jsonify({
            'success': False,
            'error': error_message,
            'error_type': 'internal_server_error',
            'id_asignacion': id_asignacion
        }), status_code


@asignaciones_admin_bp.route('/asignaciones/<int:id_asignacion>/fechas-parciales', methods=['POST'])
def registrar_fecha_parcial(id_asignacion):
    data = request.get_json()
    numero_parcial = data.get("numero_parcial")
    fecha_inicio = data.get("fecha_inicio")
    fecha_fin = data.get("fecha_fin")
    activo = data.get("activo", True)

    # Validación básica
    if numero_parcial not in [1, 2, 3]:
        return jsonify({"error": "El número de parcial debe ser 1, 2 o 3"}), 400

    try:
        fecha_inicio_dt = datetime.fromisoformat(fecha_inicio)
        fecha_fin_dt = datetime.fromisoformat(fecha_fin)
    except Exception:
        return jsonify({"error": "Formato de fecha inválido. Usa ISO 8601."}), 400

    if fecha_fin_dt <= fecha_inicio_dt:
        return jsonify({"error": "La fecha de fin debe ser posterior a la de inicio"}), 400

    # Lógica de servicio
    resultado = crear_fecha_parcial(id_asignacion, numero_parcial, fecha_inicio_dt, fecha_fin_dt, activo)
    if resultado.get("error"):
        return jsonify(resultado), 400

    return jsonify(resultado), 201

