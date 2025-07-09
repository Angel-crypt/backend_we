from flask import Blueprint, jsonify, request
from app.utils.supabase_connection import supabaseConnection as sC
import re
from datetime import datetime

cursos_admin_bp = Blueprint("cursos_admin", __name__)

# === Ruta para la gestión de cursos ===
@cursos_admin_bp.route('/cursos', methods=['GET', 'POST'])
def manejo_cursos():
    if request.method == 'GET':
        return get_cursos()
    elif request.method == 'POST':
        return crear_curso()

def get_cursos():
    """Endpoint para obtener todos los cursos registrados en la base de datos."""
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Consultar datos de cursos
        response = supabase.table('curso').select('*').execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron cursos'
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

def crear_curso():
    """Endpoint para crear un nuevo curso."""
    try:
        data = request.json
        
        # Validar que se envió JSON
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos JSON'
            }), 400
        
        # Validar campos requeridos
        required_fields = ['id_curso', 'nombre', 'descripcion']
        missing_fields = [field for field in required_fields if field not in data or not data[field].strip()]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Campos requeridos faltantes o vacíos: {", ".join(missing_fields)}'
            }), 400
        
        # Validar formato del ID (6 caracteres)
        if len(data['id_curso'].strip()) != 6:
            return jsonify({
                'success': False,
                'error': 'El ID de curso debe tener exactamente 6 caracteres'
            }), 400
        
        # Validar que el ID solo contenga caracteres alfanuméricos
        if not re.match(r'^[A-Za-z0-9]{6}$', data['id_curso'].strip()):
            return jsonify({
                'success': False,
                'error': 'El ID de curso solo puede contener letras y números'
            }), 400
        
        # Validar longitud del nombre
        nombre = data['nombre'].strip()
        if len(nombre) < 3:
            return jsonify({
                'success': False,
                'error': 'El nombre del curso debe tener al menos 3 caracteres'
            }), 400
        
        if len(nombre) > 100:
            return jsonify({
                'success': False,
                'error': 'El nombre del curso no puede exceder 100 caracteres'
            }), 400
        
        # Validar código si se proporciona
        codigo = data.get('codigo', '').strip() if data.get('codigo') else None
        if codigo:
            if len(codigo) > 20:
                return jsonify({
                    'success': False,
                    'error': 'El código del curso no puede exceder 20 caracteres'
                }), 400
            
            if not re.match(r'^[A-Za-z0-9-_]{1,20}$', codigo):
                return jsonify({
                    'success': False,
                    'error': 'El código del curso solo puede contener letras, números, guiones y guiones bajos'
                }), 400
        
        # Validar descripción
        descripcion = data['descripcion'].strip()
        if len(descripcion) < 10:
            return jsonify({
                'success': False,
                'error': 'La descripción del curso debe tener al menos 10 caracteres'
            }), 400
        
        if len(descripcion) > 500:
            return jsonify({
                'success': False,
                'error': 'La descripción del curso no puede exceder 500 caracteres'
            }), 400
        
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Verificar duplicados - ID, nombre y código
        conflicts = []
        
        # Verificar ID duplicado
        existing_id = supabase.table('curso').select('id_curso, nombre').eq('id_curso', data['id_curso'].strip()).execute()
        if existing_id.data:
            conflicts.append({
                'campo': 'id_curso',
                'valor': data['id_curso'].strip(),
                'mensaje': f'El ID de curso "{data["id_curso"].strip()}" ya existe',
                'curso_existente': existing_id.data[0]['nombre']
            })
        
        # Verificar nombre duplicado (case-insensitive)
        existing_name = supabase.table('curso').select('id_curso, nombre').ilike('nombre', nombre).execute()
        if existing_name.data:
            conflicts.append({
                'campo': 'nombre',
                'valor': nombre,
                'mensaje': f'Ya existe un curso con el nombre "{nombre}"',
                'curso_existente': {
                    'id_curso': existing_name.data[0]['id_curso'],
                    'nombre': existing_name.data[0]['nombre']
                }
            })
        
        # Verificar código duplicado si se proporciona
        if codigo:
            existing_code = supabase.table('curso').select('id_curso, nombre, codigo').eq('codigo', codigo).execute()
            if existing_code.data:
                conflicts.append({
                    'campo': 'codigo',
                    'valor': codigo,
                    'mensaje': f'El código "{codigo}" ya está en uso',
                    'curso_existente': {
                        'id_curso': existing_code.data[0]['id_curso'],
                        'nombre': existing_code.data[0]['nombre']
                    }
                })
        
        # Si hay conflictos, retornar error detallado
        if conflicts:
            return jsonify({
                'success': False,
                'error': 'No se puede crear el curso debido a conflictos de unicidad',
                'conflictos': conflicts,
                'total_conflictos': len(conflicts),
                'sugerencia': 'Modifique los campos conflictivos antes de intentar crear el curso'
            }), 409
        
        # Preparar datos del curso
        curso_data = {
            'id_curso': data['id_curso'].strip().upper(),  # Normalizar a mayúsculas
            'nombre': nombre,
            'codigo': codigo.upper() if codigo else None,  # Normalizar código a mayúsculas
            'descripcion': descripcion
        }
        
        # Crear el curso
        try:
            course_response = supabase.table('curso').insert(curso_data).execute()
            
            if not course_response.data:
                return jsonify({
                    'success': False,
                    'error': 'Error al crear el curso - no se obtuvieron datos'
                }), 500
            
            # Respuesta exitosa
            created_course = course_response.data[0]
            
            return jsonify({
                'success': True,
                'data': {
                    'id_curso': created_course['id_curso'],
                    'nombre': created_course['nombre'],
                    'codigo': created_course['codigo'],
                    'descripcion': created_course['descripcion']
                },
                'message': 'Curso creado exitosamente',
                'fecha_creacion': datetime.now().isoformat()
            }), 201
            
        except Exception as db_error:
            error_msg = str(db_error).lower()
            
            # Manejar diferentes tipos de errores de duplicado
            if 'duplicate' in error_msg or 'unique' in error_msg:
                if 'id_curso' in error_msg:
                    return jsonify({
                        'success': False,
                        'error': f'El ID de curso "{data["id_curso"].strip()}" ya existe en la base de datos'
                    }), 409
                elif 'nombre' in error_msg:
                    return jsonify({
                        'success': False,
                        'error': f'Ya existe un curso con el nombre "{nombre}"'
                    }), 409
                elif 'codigo' in error_msg:
                    return jsonify({
                        'success': False,
                        'error': f'El código "{codigo}" ya está en uso por otro curso'
                    }), 409
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Error de duplicado en la base de datos'
                    }), 409
            
            # Manejar errores de conexión
            if 'connection' in error_msg or 'timeout' in error_msg:
                return jsonify({
                    'success': False,
                    'error': 'Error de conexión con la base de datos',
                    'detalle': 'Intente nuevamente en unos momentos'
                }), 503
            
            # Otros errores de base de datos
            return jsonify({
                'success': False,
                'error': f'Error de base de datos: {str(db_error)}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

# Ruta para obtener un curso por su ID, nombre o código
@cursos_admin_bp.route('/cursos/<string:identificador>')
def get_curso(identificador):
    """Endpoint para obtener un curso por su ID, nombre o código."""
    try:
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Limpiar y preparar el identificador
        identificador_limpio = identificador.strip().upper()  # Normalizar a mayúsculas
        
        # Consultar por ID de curso
        response = supabase.table('curso').select('*').eq('id_curso', identificador_limpio).execute()
        
        if not response.data:
            # Si no se encuentra por ID, buscar por nombre o código
            response = supabase.table('curso').select('*').or_(
                f'nombre.ilike.%{identificador_limpio}%,'
                f'codigo.ilike.%{identificador_limpio}%'
            ).execute()
        
        if not response.data:
            return jsonify({
                'success': False,
                'error': f'No se encontró ningún curso con el identificador: {identificador_limpio}',
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

# Ruta para eliminar un curso por su ID
@cursos_admin_bp.route('/cursos/<string:id_curso>', methods=['DELETE'])
def delete_curso(id_curso):
    """
    Endpoint para eliminar un curso por su ID.
    """
    try:
        # Validar formato del ID
        if not id_curso:
            return jsonify({
                'success': False,
                'error': 'ID de curso es requerido'
            }), 400
            
        if not isinstance(id_curso, str) or len(id_curso) != 6:
            return jsonify({
                'success': False,
                'error': 'ID de curso inválido. Debe ser una cadena de exactamente 6 caracteres'
            }), 400
            
        # Validar que el ID solo contenga caracteres alfanuméricos
        if not id_curso.isalnum():
            return jsonify({
                'success': False,
                'error': 'ID de curso inválido. Solo se permiten caracteres alfanuméricos'
            }), 400

        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Verificar si el curso existe
        curso_response = supabase.table('curso').select('*').eq('id_curso', id_curso).execute()
        
        if not curso_response.data:
            return jsonify({
                'success': False,
                'error': 'Curso no encontrado'
            }), 404

        # Obtener información del curso para la respuesta
        curso_info = curso_response.data[0]
        
        # Verificar relaciones existentes que impiden la eliminación
        relacionales_errors = []
        
        # Verificar si tiene asignaciones activas
        asignaciones_response = supabase.table('asignacion').select(
            'id_asignacion, id_grupo, id_maestro, grupo(nombre_grupo), maestro(nombre, apellido_paterno)'
        ).eq('id_curso', id_curso).execute()
        
        if asignaciones_response.data:
            asignaciones_detalles = []
            for asignacion in asignaciones_response.data:
                grupo_nombre = asignacion.get('grupo', {}).get('nombre_grupo', 'N/A')
                maestro_info = asignacion.get('maestro', {})
                maestro_nombre = f"{maestro_info.get('nombre', 'N/A')} {maestro_info.get('apellido_paterno', '')}"
                
                asignaciones_detalles.append({
                    'id_asignacion': asignacion['id_asignacion'],
                    'grupo': grupo_nombre,
                    'maestro': maestro_nombre.strip()
                })
            
            relacionales_errors.append({
                'tabla': 'asignacion',
                'count': len(asignaciones_response.data),
                'mensaje': f'El curso tiene {len(asignaciones_response.data)} asignación(es) activa(s)',
                'detalles': asignaciones_detalles
            })
        
        # Verificar si tiene calificaciones asociadas a través de asignaciones
        if asignaciones_response.data:
            asignacion_ids = [asig['id_asignacion'] for asig in asignaciones_response.data]
            
            # Usar filtro 'in' para verificar calificaciones
            calificaciones_response = supabase.table('calificaciones_alumno_curso').select(
                'id_calif_alum_curso, id_alumno, alumno(nombre, apellido_paterno)'
            ).in_('id_asignacion', asignacion_ids).execute()
            
            if calificaciones_response.data:
                calificaciones_detalles = []
                for calif in calificaciones_response.data[:10]:  # Limitar a 10 para no sobrecargar
                    alumno_info = calif.get('alumno', {})
                    alumno_nombre = f"{alumno_info.get('nombre', 'N/A')} {alumno_info.get('apellido_paterno', '')}"
                    
                    calificaciones_detalles.append({
                        'id_alumno': calif['id_alumno'],
                        'alumno': alumno_nombre.strip()
                    })
                
                relacionales_errors.append({
                    'tabla': 'calificaciones_alumno_curso',
                    'count': len(calificaciones_response.data),
                    'mensaje': f'El curso tiene {len(calificaciones_response.data)} calificación(es) registrada(s)',
                    'detalles': calificaciones_detalles,
                    'nota': 'Se muestran solo las primeras 10 calificaciones' if len(calificaciones_response.data) > 10 else None
                })
        
        # Verificar si tiene horarios asociados a través de asignaciones
        if asignaciones_response.data:
            asignacion_ids = [asig['id_asignacion'] for asig in asignaciones_response.data]
            
            horarios_response = supabase.table('horario_asignacion').select(
                'id_horario, dia_semana, hora_inicio, hora_fin'
            ).in_('id_asignacion', asignacion_ids).execute()
            
            if horarios_response.data:
                horarios_detalles = []
                for horario in horarios_response.data:
                    horarios_detalles.append({
                        'dia': horario['dia_semana'],
                        'hora_inicio': horario['hora_inicio'],
                        'hora_fin': horario['hora_fin']
                    })
                
                relacionales_errors.append({
                    'tabla': 'horario_asignacion',
                    'count': len(horarios_response.data),
                    'mensaje': f'El curso tiene {len(horarios_response.data)} horario(s) programado(s)',
                    'detalles': horarios_detalles
                })
        
        # Si hay relaciones, no permitir eliminación
        if relacionales_errors:
            return jsonify({
                'success': False,
                'error': 'No se puede eliminar el curso porque tiene relaciones activas',
                'curso_info': {
                    'id_curso': curso_info['id_curso'],
                    'nombre': curso_info['nombre'],
                    'codigo': curso_info.get('codigo', 'N/A')
                },
                'relaciones_activas': relacionales_errors,
                'sugerencia': 'Elimine primero las asignaciones, calificaciones y horarios asociados antes de eliminar el curso'
            }), 409
        
        # Proceder con la eliminación
        delete_response = supabase.table('curso').delete().eq('id_curso', id_curso).execute()
        
        # Verificar si la eliminación fue exitosa
        if not delete_response.data:
            return jsonify({
                'success': False,
                'error': 'No se pudo eliminar el curso. Verifique que el ID sea correcto'
            }), 500
        
        # Respuesta exitosa
        return jsonify({
            'success': True,
            'message': 'Curso eliminado exitosamente',
            'curso_eliminado': {
                'id_curso': curso_info['id_curso'],
                'nombre': curso_info['nombre'],
                'codigo': curso_info.get('codigo', 'N/A'),
                'descripcion': curso_info.get('descripcion', 'N/A')
            }
        }), 200
        
    except Exception as e:
        # Log del error para debugging
        print(f"Error al eliminar curso {id_curso}: {str(e)}")
        
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
            'error_type': 'internal_server_error'
        }), status_code

# Ruta para editar un curso por su ID
@cursos_admin_bp.route('/cursos/<string:id_curso>', methods=['PUT'])
def edit_curso(id_curso):
    """
    Endpoint para editar un curso por su ID.
    """
    try:
        # Validar formato del ID
        if not id_curso:
            return jsonify({
                'success': False,
                'error': 'ID de curso es requerido'
            }), 400
            
        if not isinstance(id_curso, str) or len(id_curso) != 6:
            return jsonify({
                'success': False,
                'error': 'ID de curso inválido. Debe ser una cadena de exactamente 6 caracteres'
            }), 400
            
        # Validar que el ID solo contenga caracteres alfanuméricos
        if not id_curso.isalnum():
            return jsonify({
                'success': False,
                'error': 'ID de curso inválido. Solo se permiten caracteres alfanuméricos'
            }), 400

        # Obtener datos del cuerpo de la solicitud
        data = request.json
        
        # Validar que se envió JSON
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos JSON'
            }), 400
            
        # Validar que al menos un campo esté presente para actualizar
        allowed_fields = ['nombre', 'descripcion', 'codigo']
        update_fields = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_fields:
            return jsonify({
                'success': False,
                'error': f'Debe proporcionar al menos uno de los siguientes campos: {", ".join(allowed_fields)}'
            }), 400

        # Validar campos requeridos (solo si están presentes)
        if 'nombre' in update_fields:
            nombre = update_fields['nombre']
            if not nombre or not str(nombre).strip():
                return jsonify({
                    'success': False,
                    'error': 'El nombre del curso no puede estar vacío'
                }), 400
            
            nombre = str(nombre).strip()
            update_fields['nombre'] = nombre
            
            # Validar longitud del nombre
            if len(nombre) < 3:
                return jsonify({
                    'success': False,
                    'error': 'El nombre del curso debe tener al menos 3 caracteres'
                }), 400
                
            if len(nombre) > 100:
                return jsonify({
                    'success': False,
                    'error': 'El nombre del curso no puede exceder 100 caracteres'
                }), 400

        # Validar descripción si está presente
        if 'descripcion' in update_fields:
            descripcion = update_fields['descripcion']
            if descripcion is not None:
                if not str(descripcion).strip():
                    return jsonify({
                        'success': False,
                        'error': 'La descripción no puede estar vacía'
                    }), 400
                
                descripcion = str(descripcion).strip()
                update_fields['descripcion'] = descripcion
                
                if len(descripcion) > 500:
                    return jsonify({
                        'success': False,
                        'error': 'La descripción no puede exceder 500 caracteres'
                    }), 400

        # Validar código si se proporciona
        if 'codigo' in update_fields:
            codigo = update_fields['codigo']
            if codigo is not None:
                if codigo == '':
                    # Permitir código vacío para remover el código
                    update_fields['codigo'] = None
                else:
                    codigo = str(codigo).strip()
                    if len(codigo) > 20:
                        return jsonify({
                            'success': False,
                            'error': 'El código del curso no puede exceder 20 caracteres'
                        }), 400
                    
                    if not re.match(r'^[A-Za-z0-9-_]{1,20}$', codigo):
                        return jsonify({
                            'success': False,
                            'error': 'El código del curso solo puede contener letras, números, guiones y guiones bajos'
                        }), 400
                    
                    update_fields['codigo'] = codigo

        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Verificar si el curso existe
        curso_response = supabase.table('curso').select('*').eq('id_curso', id_curso).execute()
        
        if not curso_response.data:
            return jsonify({
                'success': False,
                'error': 'Curso no encontrado'
            }), 404

        # Obtener información actual del curso
        curso_actual = curso_response.data[0]
        
        # Verificar duplicado de código si se está actualizando
        if 'codigo' in update_fields and update_fields['codigo'] is not None:
            codigo_nuevo = update_fields['codigo']
            # Solo verificar si el código realmente cambió
            if codigo_nuevo != curso_actual.get('codigo'):
                codigo_existente = supabase.table('curso').select('id_curso, nombre').eq('codigo', codigo_nuevo).execute()
                
                if codigo_existente.data:
                    curso_conflicto = codigo_existente.data[0]
                    return jsonify({
                        'success': False,
                        'error': 'El código del curso ya existe',
                        'conflicto': {
                            'id_curso': curso_conflicto['id_curso'],
                            'nombre': curso_conflicto['nombre'],
                            'codigo': codigo_nuevo
                        }
                    }), 409

        # Verificar duplicado de nombre si se está actualizando
        if 'nombre' in update_fields:
            nombre_nuevo = update_fields['nombre']
            # Solo verificar si el nombre realmente cambió
            if nombre_nuevo.lower() != curso_actual.get('nombre', '').lower():
                nombre_existente = supabase.table('curso').select('id_curso, codigo').ilike('nombre', nombre_nuevo).execute()
                
                if nombre_existente.data:
                    curso_conflicto = nombre_existente.data[0]
                    return jsonify({
                        'success': False,
                        'error': 'Ya existe un curso con ese nombre',
                        'conflicto': {
                            'id_curso': curso_conflicto['id_curso'],
                            'codigo': curso_conflicto.get('codigo', 'N/A'),
                            'nombre': nombre_nuevo
                        }
                    }), 409

        # Realizar la actualización
        update_response = supabase.table('curso').update(update_fields).eq('id_curso', id_curso).execute()
        
        # Verificar si la actualización fue exitosa
        if not update_response.data:
            return jsonify({
                'success': False,
                'error': 'No se pudo actualizar el curso. Verifique los datos proporcionados'
            }), 500

        # Obtener el curso actualizado
        curso_actualizado = update_response.data[0]
        
        # Preparar respuesta con cambios realizados
        cambios_realizados = {}
        for campo, valor_nuevo in update_fields.items():
            valor_anterior = curso_actual.get(campo)
            if valor_anterior != valor_nuevo:
                cambios_realizados[campo] = {
                    'anterior': valor_anterior,
                    'nuevo': valor_nuevo
                }
        
        # Respuesta exitosa
        return jsonify({
            'success': True,
            'message': 'Curso actualizado exitosamente',
            'curso_actualizado': {
                'id_curso': curso_actualizado['id_curso'],
                'nombre': curso_actualizado['nombre'],
                'codigo': curso_actualizado.get('codigo'),
                'descripcion': curso_actualizado.get('descripcion')
            },
            'cambios_realizados': cambios_realizados,
            'campos_actualizados': list(update_fields.keys())
        }), 200
        
    except KeyError as e:
        return jsonify({
            'success': False,
            'error': f'Campo requerido faltante: {str(e)}',
            'error_type': 'validation_error'
        }), 400
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Valor inválido proporcionado: {str(e)}',
            'error_type': 'validation_error'
        }), 400
        
    except Exception as e:
        # Log del error para debugging
        print(f"Error al editar curso {id_curso}: {str(e)}")
        
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
        elif 'unique' in str(e).lower():
            error_message = 'Violación de restricción única en la base de datos'
            
        return jsonify({
            'success': False,
            'error': error_message,
            'error_type': 'internal_server_error'
        }), status_code
