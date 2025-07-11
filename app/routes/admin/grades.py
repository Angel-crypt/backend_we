from flask import Blueprint, jsonify, request
from app.utils.supabase_connection import supabaseConnection as sC
from .auth import admin_required

grades_admin_bp = Blueprint("grades_admin", __name__)

@grades_admin_bp.route('/grades/assignments/<int:id_asignacion>', methods=['GET'])
@admin_required
def get_grades_by_assignment(id_asignacion):
    """Endpoint para que el administrador vea todas las calificaciones de una asignación"""
    try:
        supabase = sC.get_instance().get_client()
        
        # Verificar que la asignación existe
        asignacion_response = supabase.table('asignacion').select(
            'id_asignacion, curso(id_curso, nombre, codigo), grupo(id_grupo, nombre_grupo), maestro(id_usuario, nombre, apellido_paterno, apellido_materno)'
        ).eq('id_asignacion', id_asignacion).execute()

        if not asignacion_response.data:
            return jsonify({
                'success': False,
                'error': 'Asignación no encontrada'
            }), 404
        
        asignacion_info = asignacion_response.data[0]
        
        # Obtener todas las calificaciones de la asignación
        calificaciones_response = supabase.table('calificaciones').select(
            '*, alumno(id_alumno, nombre, apellido_paterno, apellido_materno)'
        ).eq('id_asignacion', id_asignacion).execute()
        
        return jsonify({
            'success': True,
            'data': {
                'asignacion_info': asignacion_info,
                'calificaciones': calificaciones_response.data,
                'total_calificaciones': len(calificaciones_response.data)
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@grades_admin_bp.route('/grades/maestro/<string:id_maestro>', methods=['GET'])
@admin_required
def get_grades_by_teacher(id_maestro):
    """Endpoint para que el administrador vea todas las calificaciones de un maestro"""
    try:
        supabase = sC.get_instance().get_client()
        
        # Verificar que el maestro existe
        maestro_response = supabase.table('maestro').select('*').eq('id_usuario', id_maestro).execute()
        if not maestro_response.data:
            return jsonify({
                'success': False,
                'error': 'Maestro no encontrado'
            }), 404
        
        maestro_info = maestro_response.data[0]
        
        # Obtener asignaciones del maestro
        asignaciones_response = supabase.table('asignacion').select(
            'id_asignacion, curso(id_curso, nombre, codigo), grupo(id_grupo, nombre_grupo)'
        ).eq('id_maestro', id_maestro).execute()

        grades_data = []
        
        for asignacion in asignaciones_response.data:
            # Obtener calificaciones para cada asignación
            calificaciones_response = supabase.table('calificaciones').select(
                '*, alumno(id_alumno, nombre, apellido_paterno, apellido_materno)'
            ).eq('id_asignacion', asignacion['id_asignacion']).execute()
            
            grades_data.append({
                'asignacion': asignacion,
                'calificaciones': calificaciones_response.data
            })
        
        return jsonify({
            'success': True,
            'data': {
                'maestro_info': maestro_info,
                'asignaciones_con_calificaciones': grades_data,
                'total_asignaciones': len(grades_data)
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@grades_admin_bp.route('/lesson-plans', methods=['GET'])
@admin_required
def get_all_lesson_plans():
    """Endpoint para que el administrador vea todas las planificaciones subidas por maestros"""
    try:
        supabase = sC.get_instance().get_client()
        
        # Obtener todas las asignaciones con planificaciones
        planificaciones_response = supabase.table('asignacion').select(
            'id_asignacion, planeacion_pdf_url, curso(id_curso, nombre, codigo), grupo(id_grupo, nombre_grupo), maestro(id_usuario, nombre, apellido_paterno, apellido_materno)'
        ).not_.is_('planeacion_pdf_url', 'null').execute()
        
        if not planificaciones_response.data:
            return jsonify({
                'success': False,
                'error': 'No se encontraron planificaciones'
            }), 404
        
        return jsonify({
            'success': True,
            'data': planificaciones_response.data,
            'total_planificaciones': len(planificaciones_response.data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@grades_admin_bp.route('/lesson-plans/maestro/<string:id_maestro>', methods=['GET'])
@admin_required
def get_lesson_plans_by_teacher(id_maestro):
    """Endpoint para que el administrador vea las planificaciones de un maestro específico"""
    try:
        supabase = sC.get_instance().get_client()
        
        # Verificar que el maestro existe
        maestro_response = supabase.table('maestro').select('*').eq('id_usuario', id_maestro).execute()
        if not maestro_response.data:
            return jsonify({
                'success': False,
                'error': 'Maestro no encontrado'
            }), 404
        
        maestro_info = maestro_response.data[0]
        
        # Obtener planificaciones del maestro
        planificaciones_response = supabase.table('asignacion').select(
            'id_asignacion, planeacion_pdf_url, curso(id_curso, nombre, codigo), grupo(id_grupo, nombre_grupo)'
        ).eq('id_maestro', id_maestro).execute()

        # Filtrar solo las que tienen planificación
        planificaciones_con_pdf = [p for p in planificaciones_response.data if p['planeacion_pdf_url']]
        
        return jsonify({
            'success': True,
            'data': {
                'maestro_info': maestro_info,
                'planificaciones': planificaciones_con_pdf,
                'total_planificaciones': len(planificaciones_con_pdf),
                'total_asignaciones': len(planificaciones_response.data)
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500
