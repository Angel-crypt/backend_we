from flask import Blueprint, jsonify, request
import bcrypt
from datetime import datetime
from app.utils.supabase_connection import supabaseConnection as sC
from app.models import Maestro
from .auth import admin_required

maestros_admin_bp = Blueprint("maestros_admin", __name__)


# === Rutas para la gestión de maestros ===

# Ruta para ver todos los maestros y crear uno nuevo
@maestros_admin_bp.route('/maestros', methods=['GET', 'POST'])
@admin_required
def manejo_maestros():
    if request.method == 'GET':
        return get_maestros()
    elif request.method == 'POST':
        return crear_maestro()

def get_maestros():
    """Endpoint para obtener todos los maestros registrados en la base de datos."""
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Consultar datos de maestros
        response = supabase.table('maestro').select('*').execute()
        
        maestros = [Maestro.from_dict(row) for row in response.data]
        maestros_data = [maestro.to_dict() for maestro in maestros]
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron maestros'
            }), 404
        
        return jsonify({
            'success': True,
            'data': maestros_data,
            'total': len(maestros_data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def crear_maestro():
    """Endpoint para crear un nuevo maestro y su usuario asociado."""
    try:
        data = request.json
        
        # Validar que se envió JSON
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos JSON'
            }), 400
        
        # Validar campos requeridos
        required_fields = ['id_usuario', 'nombre', 'apellido_paterno', 'contrasena']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
            }), 400
        
        # Validar formato del ID (6 caracteres)
        if len(data['id_usuario']) != 6:
            return jsonify({
                'success': False,
                'error': 'El ID de usuario debe tener exactamente 6 caracteres'
            }), 400
        
        # Validar longitud mínima de contraseña
        if len(data['contrasena']) < 6:
            return jsonify({
                'success': False,
                'error': 'La contraseña debe tener al menos 6 caracteres'
            }), 400
        
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Verificar si ya existe el ID de usuario
        existing_user = supabase.table('usuario').select('id_usuario').eq('id_usuario', data['id_usuario']).execute()
        if existing_user.data:
            return jsonify({
                'success': False,
                'error': f'El ID de usuario {data["id_usuario"]} ya existe'
            }), 409
        
        # Encriptar contraseña
        password_bytes = data['contrasena'].encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        
        # Preparar datos del usuario
        user_data = {
            'id_usuario': data['id_usuario'],
            'contrasena': hashed_password.decode('utf-8'),
            'role': data.get('role', 'maestro'),  # Default a 'maestro'
            'fecha_creacion': datetime.now().isoformat()
        }
        
        # Validar rol si se proporciona
        valid_roles = ['admin', 'maestro']
        if user_data['role'] not in valid_roles:
            return jsonify({
                'success': False,
                'error': f'Rol inválido. Debe ser uno de: {", ".join(valid_roles)}'
            }), 400
        
        # Preparar datos del maestro
        maestro_data = {
            'id_usuario': data['id_usuario'],
            'nombre': data['nombre'],
            'apellido_paterno': data['apellido_paterno'],
            'apellido_materno': data.get('apellido_materno'),
            'fecha_nacimiento': data.get('fecha_nacimiento'),
            'especialidad': data.get('especialidad')
        }
        
        # Validar fecha de nacimiento si se proporciona
        if maestro_data['fecha_nacimiento']:
            try:
                datetime.strptime(maestro_data['fecha_nacimiento'], '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de fecha de nacimiento inválido. Use YYYY-MM-DD'
                }), 400
        
        # Iniciar transacción - crear usuario primero
        try:
            # Crear usuario
            user_response = supabase.table('usuario').insert(user_data).execute()
            
            if not user_response.data:
                return jsonify({
                    'success': False,
                    'error': 'Error al crear el usuario'
                }), 500
            
            # Crear maestro
            maestro_response = supabase.table('maestro').insert(maestro_data).execute()
            
            if not maestro_response.data:
                # Si falla crear maestro, eliminar usuario creado
                supabase.table('usuario').delete().eq('id_usuario', data['id_usuario']).execute()
                return jsonify({
                    'success': False,
                    'error': 'Error al crear el maestro'
                }), 500
            
            # Preparar respuesta exitosa (sin incluir contraseña)
            created_user = user_response.data[0].copy()
            created_user.pop('contrasena', None)  # Remover contraseña de la respuesta
            
            return jsonify({
                'success': True,
                'data': {
                    'usuario': created_user,
                    'maestro': maestro_response.data[0]
                },
                'message': 'Maestro y usuario creados exitosamente'
            }), 201
            
        except Exception as db_error:
            # Limpiar usuario si se creó pero falló el maestro
            try:
                supabase.table('usuario').delete().eq('id_usuario', data['id_usuario']).execute()
            except:
                pass
            
            # Verificar si es error de duplicado
            if 'duplicate' in str(db_error).lower() or 'unique' in str(db_error).lower():
                return jsonify({
                    'success': False,
                    'error': f'El ID de usuario {data["id_usuario"]} ya existe'
                }), 409
            
            raise db_error
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

# Rutas para ver a un maestro en específico
# por id
@maestros_admin_bp.route('/maestros/<string:id_usuario>')
@admin_required
def get_maestro(id_usuario):
    """Endpoint para obtener un maestro por su ID de usuario."""
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Consultar datos del maestro
        response = supabase.table('maestro').select('*').eq('id_usuario', id_usuario).execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'Maestro no encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'data': response.data[0]
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# por nombre
@maestros_admin_bp.route('/maestros/nombre/<string:nombre>')
@admin_required
def get_maestro_by_name(nombre):
    """Endpoint para obtener un maestro por su nombre completo."""
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Limpiar y preparar el término de búsqueda
        nombre_limpio = nombre.strip()
        
        # Dividir el nombre en palabras para buscar individualmente
        palabras = nombre_limpio.split()
        
        # Construir consulta flexible que busque en nombre y apellidos
        query = supabase.table('maestro').select('*')
        
        # Para cada palabra, buscar en cualquiera de los campos de nombre
        for palabra in palabras:
            query = query.or_(
                f'nombre.ilike.%{palabra}%,'
                f'apellido_paterno.ilike.%{palabra}%,'
                f'apellido_materno.ilike.%{palabra}%'
            )
        
        response = query.execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': f'No se encontraron maestros con el nombre: {nombre_limpio}',
                'searched_term': nombre_limpio
            }), 404
        
        return jsonify({
            'success': True,
            'data': response.data,
            'total': len(response.data),
            'searched_term': nombre_limpio
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}',
            'searched_term': nombre
        }), 500

# por especialidad
@maestros_admin_bp.route('/maestros/especialidad/<string:especialidad>')
@admin_required
def get_maestros_by_specialty(especialidad):
    """Endpoint para obtener maestros por especialidad."""
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Consultar datos de maestros por especialidad
        response = supabase.table('maestro').select('*').eq('especialidad', especialidad).execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron maestros con esa especialidad'
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

# por edad
@maestros_admin_bp.route('/maestros/edad/<int:edad>')
@admin_required
def get_maestros_by_age(edad):
    """Endpoint para obtener maestros por edad."""
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Calcular fecha de nacimiento aproximada
        fecha_nacimiento = datetime.now().replace(year=datetime.now().year - edad).isoformat()
        
        # Consultar datos de maestros por fecha de nacimiento
        response = supabase.table('maestro').select('*').lte('fecha_nacimiento', fecha_nacimiento).execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron maestros con esa edad'
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

# Ruta para eliminar un maestro por su ID
@maestros_admin_bp.route('/maestros/<string:id_usuario>', methods=['DELETE'])
@admin_required
def delete_maestro(id_usuario):
    """Endpoint para eliminar un maestro por su ID de usuario."""
    try:
        # Validar formato del ID
        if not id_usuario or len(id_usuario) != 6:
            return jsonify({
                'success': False,
                'error': 'ID de usuario inválido. Debe tener exactamente 6 caracteres'
            }), 400
        
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Verificar si el maestro existe
        maestro_response = supabase.table('maestro').select('*').eq('id_usuario', id_usuario).execute()
        if not maestro_response.data:
            return jsonify({
                'success': False,
                'error': 'Maestro no encontrado'
            }), 404
        
        # Obtener información del maestro para la respuesta
        maestro_info = maestro_response.data[0]
        
        # Verificar relaciones existentes que impiden la eliminación
        relacionales_errors = []
        
        # Ejemplo: Verificar si tiene clases asignadas
        clases_response = supabase.table('clase').select('id_clase, nombre_clase').eq('id_maestro', id_usuario).execute()
        if clases_response.data:
            clases_nombres = [clase['nombre_clase'] for clase in clases_response.data]
            relacionales_errors.append({
                'tabla': 'clase',
                'count': len(clases_response.data),
                'mensaje': f'El maestro tiene {len(clases_response.data)} clase(s) asignada(s)',
                'detalles': clases_nombres
            })
        
        # Ejemplo: Verificar si tiene horarios asignados
        horarios_response = supabase.table('horario').select('id_horario, dia, hora_inicio, hora_fin').eq('id_maestro', id_usuario).execute()
        if horarios_response.data:
            horarios_info = [f"{h['dia']} {h['hora_inicio']}-{h['hora_fin']}" for h in horarios_response.data]
            relacionales_errors.append({
                'tabla': 'horario',
                'count': len(horarios_response.data),
                'mensaje': f'El maestro tiene {len(horarios_response.data)} horario(s) asignado(s)',
                'detalles': horarios_info
            })
        
        # Ejemplo: Verificar si tiene evaluaciones creadas
        evaluaciones_response = supabase.table('evaluacion').select('id_evaluacion, titulo').eq('id_maestro', id_usuario).execute()
        if evaluaciones_response.data:
            evaluaciones_titulos = [eval['titulo'] for eval in evaluaciones_response.data]
            relacionales_errors.append({
                'tabla': 'evaluacion',
                'count': len(evaluaciones_response.data),
                'mensaje': f'El maestro tiene {len(evaluaciones_response.data)} evaluación(es) creada(s)',
                'detalles': evaluaciones_titulos
            })
        
        # Ejemplo: Verificar si tiene calificaciones registradas
        calificaciones_response = supabase.table('calificacion').select('id_calificacion').eq('id_maestro', id_usuario).execute()
        if calificaciones_response.data:
            relacionales_errors.append({
                'tabla': 'calificacion',
                'count': len(calificaciones_response.data),
                'mensaje': f'El maestro tiene {len(calificaciones_response.data)} calificación(es) registrada(s)',
                'detalles': ['Calificaciones de estudiantes']
            })
        
        # Ejemplo: Verificar si tiene asistencias registradas
        asistencias_response = supabase.table('asistencia').select('id_asistencia').eq('id_maestro', id_usuario).execute()
        if asistencias_response.data:
            relacionales_errors.append({
                'tabla': 'asistencia',
                'count': len(asistencias_response.data),
                'mensaje': f'El maestro tiene {len(asistencias_response.data)} registro(s) de asistencia',
                'detalles': ['Registros de asistencia de estudiantes']
            })
        
        # Si hay relaciones, no permitir eliminación
        if relacionales_errors:
            return jsonify({
                'success': False,
                'error': 'No se puede eliminar el maestro porque tiene relaciones activas',
                'maestro_info': {
                    'id_usuario': maestro_info['id_usuario'],
                    'nombre_completo': f"{maestro_info['nombre']} {maestro_info['apellido_paterno']} {maestro_info.get('apellido_materno', '')}".strip(),
                    'especialidad': maestro_info.get('especialidad', 'No especificada')
                },
                'relaciones_activas': relacionales_errors,
                'total_relaciones': len(relacionales_errors),
                'sugerencia': 'Para eliminar este maestro, primero debe reasignar o eliminar las relaciones mencionadas'
            }), 409  # Conflict
        
        # Si no hay relaciones, proceder con la eliminación
        try:
            # Eliminar el maestro primero (por la foreign key)
            delete_maestro_response = supabase.table('maestro').delete().eq('id_usuario', id_usuario).execute()
            
            if not delete_maestro_response.data:
                return jsonify({
                    'success': False,
                    'error': 'Error al eliminar el registro del maestro'
                }), 500
            
            # Eliminar el usuario asociado
            delete_usuario_response = supabase.table('usuario').delete().eq('id_usuario', id_usuario).execute()
            
            if not delete_usuario_response.data:
                # Si falla eliminar usuario, restaurar maestro (rollback manual)
                supabase.table('maestro').insert(maestro_info).execute()
                return jsonify({
                    'success': False,
                    'error': 'Error al eliminar el usuario asociado'
                }), 500
            
            return jsonify({
                'success': True,
                'message': 'Maestro eliminado exitosamente',
                'maestro_eliminado': {
                    'id_usuario': maestro_info['id_usuario'],
                    'nombre_completo': f"{maestro_info['nombre']} {maestro_info['apellido_paterno']} {maestro_info.get('apellido_materno', '')}".strip(),
                    'especialidad': maestro_info.get('especialidad', 'No especificada')
                }
            }), 200
            
        except Exception as delete_error:
            # Manejar errores específicos de eliminación
            error_msg = str(delete_error).lower()
            
            if 'foreign key' in error_msg or 'constraint' in error_msg:
                return jsonify({
                    'success': False,
                    'error': 'No se puede eliminar el maestro debido a restricciones de integridad referencial',
                    'detalle': 'El maestro tiene relaciones activas en otras tablas',
                    'sugerencia': 'Verifique y elimine primero las relaciones dependientes'
                }), 409
            
            raise delete_error
        
    except Exception as e:
        # Manejar otros errores
        error_msg = str(e).lower()
        
        if 'connection' in error_msg or 'timeout' in error_msg:
            return jsonify({
                'success': False,
                'error': 'Error de conexión con la base de datos',
                'detalle': 'Intente nuevamente en unos momentos'
            }), 503
        
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

# Ruta para ver los cursos de un maestro
@maestros_admin_bp.route('/maestros/<string:id_maestro>/cursos', methods=['GET'])
@admin_required
def get_cursos_maestro(id_maestro):
    """
    Endpoint para obtener los cursos asignados a un maestro por su ID.
    """
    try:
        # Validar formato del ID
        if not id_maestro or not isinstance(id_maestro, str):
            return jsonify({
                'success': False,
                'error': 'ID de maestro es requerido y debe ser una cadena'
            }), 400
        
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Consultar cursos del maestro
        response = supabase.table('asignacion').select(
            'id_asignacion, curso(id_curso, nombre, codigo, descripcion), grupo(nombre_grupo), maestro(nombre, apellido_paterno)'
        ).eq('id_maestro', id_maestro).execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron cursos asignados al maestro',
                'id_maestro': id_maestro
            }), 404
        
        return jsonify({
            'success': True,
            'data': response.data,
            'total_cursos': len(response.data),
            'id_maestro': id_maestro
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}',
            'id_maestro': id_maestro
        }), 500

