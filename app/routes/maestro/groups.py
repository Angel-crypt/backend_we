from flask import Blueprint, jsonify, request, session
from app.utils.supabase_connection import supabaseConnection as sC

maestro_groups_bp = Blueprint("maestro_groups", __name__)

@maestro_groups_bp.route('/groups', methods=['GET'])
def get_assigned_groups():
    """Endpoint para obtener grupos asignados al maestro."""
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

        # Obtener grupos asignados al maestro
        grupos_response = supabase.table('asignacion').select(
            'id_asignacion, curso(id_curso, nombre, codigo), grupo(id_grupo, nombre_grupo)',
        ).eq('id_maestro', user_id).execute()
        
        if not grupos_response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron grupos asignados'
            }), 404

        return jsonify({
            'success': True,
            'data': grupos_response.data,
            'total_grupos': len(grupos_response.data)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@maestro_groups_bp.route('/groups/<string:id_grupo>/students', methods=['GET'])
def get_students_in_group(id_grupo):
    """Endpoint para obtener estudiantes en un grupo específico."""
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

        # Verificar que el grupo esté asignado al maestro
        asignacion_response = supabase.table('asignacion').select('id_asignacion').eq('id_maestro', user_id).eq('id_grupo', id_grupo).execute()
        if not asignacion_response.data:
            return jsonify({
                'success': False,
                'error': 'Este grupo no está asignado al maestro'
            }), 403

        # Obtener estudiantes en el grupo
        estudiantes_response = supabase.table('alumno').select(
            'id_alumno, nombre, apellido_paterno, apellido_materno'
        ).eq('id_grupo', id_grupo).execute()
        
        if not estudiantes_response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron estudiantes en el grupo'
            }), 404

        return jsonify({
            'success': True,
            'data': estudiantes_response.data,
            'total_estudiantes': len(estudiantes_response.data)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@maestro_groups_bp.route('/groups/<string:id_grupo>/details', methods=['GET'])
def get_group_details(id_grupo):
    """Endpoint para obtener detalles completos de un grupo asignado al maestro."""
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

        # Verificar que el grupo esté asignado al maestro y obtener información completa
        asignacion_response = supabase.table('asignacion').select(
            'id_asignacion, planeacion_pdf_url, curso(id_curso, nombre, codigo, descripcion), grupo(id_grupo, nombre_grupo, generacion, facultad)'
        ).eq('id_maestro', user_id).eq('id_grupo', id_grupo).execute()
        
        if not asignacion_response.data:
            return jsonify({
                'success': False,
                'error': 'Este grupo no está asignado al maestro'
            }), 403

        asignacion_info = asignacion_response.data[0]

        # Obtener estudiantes en el grupo con información completa
        estudiantes_response = supabase.table('alumno').select(
            'id_alumno, nombre, apellido_paterno, apellido_materno, fecha_nacimiento, sexo'
        ).eq('id_grupo', id_grupo).execute()

        # Obtener horarios de la asignación
        horarios_response = supabase.table('horario_asignacion').select(
            'id_horario, dia_semana, hora_inicio, hora_fin'
        ).eq('id_asignacion', asignacion_info['id_asignacion']).execute()

        return jsonify({
            'success': True,
            'data': {
                'asignacion': asignacion_info,
                'estudiantes': estudiantes_response.data,
                'horarios': horarios_response.data,
                'total_estudiantes': len(estudiantes_response.data),
                'total_horarios': len(horarios_response.data)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@maestro_groups_bp.route('/assignments', methods=['GET'])
def get_all_assignments():
    """Endpoint para obtener todas las asignaciones del maestro con información detallada."""
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

        # Obtener todas las asignaciones del maestro
        asignaciones_response = supabase.table('asignacion').select(
            'id_asignacion, planeacion_pdf_url, curso(id_curso, nombre, codigo, descripcion), grupo(id_grupo, nombre_grupo, generacion, facultad)'
        ).eq('id_maestro', user_id).execute()
        
        if not asignaciones_response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron asignaciones'
            }), 404

        # Enriquecer cada asignación con información adicional
        asignaciones_detalladas = []
        
        for asignacion in asignaciones_response.data:
            # Contar estudiantes en el grupo
            estudiantes_count = supabase.table('alumno').select(
                'id_alumno', count='exact'
            ).eq('id_grupo', asignacion['grupo']['id_grupo']).execute()
            
            # Obtener horarios
            horarios = supabase.table('horario_asignacion').select(
                'dia_semana, hora_inicio, hora_fin'
            ).eq('id_asignacion', asignacion['id_asignacion']).execute()
            
            asignacion_detallada = {
                'id_asignacion': asignacion['id_asignacion'],
                'curso': asignacion['curso'],
                'grupo': asignacion['grupo'],
                'planeacion_pdf_url': asignacion['planeacion_pdf_url'],
                'total_estudiantes': estudiantes_count.count if estudiantes_count.count else 0,
                'horarios': horarios.data,
                'tiene_planeacion': bool(asignacion['planeacion_pdf_url'])
            }
            
            asignaciones_detalladas.append(asignacion_detallada)

        return jsonify({
            'success': True,
            'data': asignaciones_detalladas,
            'total_asignaciones': len(asignaciones_detalladas)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@maestro_groups_bp.route('/assignments/<int:id_asignacion>/students', methods=['GET'])
def get_students_by_assignment(id_asignacion):
    """Endpoint para obtener estudiantes de una asignación específica."""
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
            'id_asignacion, id_grupo, curso(nombre), grupo(nombre_grupo)'
        ).eq('id_asignacion', id_asignacion).eq('id_maestro', user_id).execute()
        
        if not asignacion_response.data:
            return jsonify({
                'success': False,
                'error': 'Asignación no encontrada o no pertenece al maestro'
            }), 403

        asignacion_info = asignacion_response.data[0]
        id_grupo = asignacion_info['id_grupo']

        # Obtener estudiantes del grupo
        estudiantes_response = supabase.table('alumno').select(
            'id_alumno, nombre, apellido_paterno, apellido_materno, fecha_nacimiento, sexo'
        ).eq('id_grupo', id_grupo).execute()

        return jsonify({
            'success': True,
            'data': {
                'asignacion_info': {
                    'id_asignacion': id_asignacion,
                    'curso': asignacion_info['curso']['nombre'],
                    'grupo': asignacion_info['grupo']['nombre_grupo']
                },
                'estudiantes': estudiantes_response.data,
                'total_estudiantes': len(estudiantes_response.data)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@maestro_groups_bp.route('/assignments/<int:id_asignacion>/schedule', methods=['GET'])
def get_assignment_schedule(id_asignacion):
    """Endpoint para obtener el horario de una asignación específica."""
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
            'id_asignacion, curso(nombre), grupo(nombre_grupo)'
        ).eq('id_asignacion', id_asignacion).eq('id_maestro', user_id).execute()
        
        if not asignacion_response.data:
            return jsonify({
                'success': False,
                'error': 'Asignación no encontrada o no pertenece al maestro'
            }), 403

        asignacion_info = asignacion_response.data[0]

        # Obtener horarios de la asignación
        horarios_response = supabase.table('horario_asignacion').select(
            'id_horario, dia_semana, hora_inicio, hora_fin'
        ).eq('id_asignacion', id_asignacion).order('dia_semana').order('hora_inicio').execute()

        # Organizar horarios por día de la semana
        days_order = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        horarios_organizados = {day: [] for day in days_order}
        
        for horario in horarios_response.data:
            day = horario['dia_semana']
            if day in horarios_organizados:
                horarios_organizados[day].append({
                    'id_horario': horario['id_horario'],
                    'hora_inicio': horario['hora_inicio'],
                    'hora_fin': horario['hora_fin']
                })

        return jsonify({
            'success': True,
            'data': {
                'asignacion_info': {
                    'id_asignacion': id_asignacion,
                    'curso': asignacion_info['curso']['nombre'],
                    'grupo': asignacion_info['grupo']['nombre_grupo']
                },
                'horarios': horarios_organizados,
                'total_horarios': len(horarios_response.data)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500
