from flask import Blueprint, jsonify, request, session
from datetime import datetime
from app.utils.supabase_connection import supabaseConnection as sC

maestro_profile_bp = Blueprint("maestro_profile", __name__)

@maestro_profile_bp.route('/profile', methods=['GET', 'PUT'])
def manage_profile():
    """Endpoint para obtener o actualizar la información personal del maestro"""
    try:
        # Verificar si el usuario está autenticado
        if 'user_id' not in session or 'role' not in session:
            return jsonify({
                'success': False,
                'error': 'No autenticado'
            }), 401
        
        # Verificar que el usuario sea maestro
        if session['role'] != 'maestro':
            return jsonify({
                'success': False,
                'error': 'Acceso denegado - Solo maestros'
            }), 403
        
        user_id = session['user_id']
        supabase = sC.get_instance().get_client()
        
        if request.method == 'GET':
            # Obtener información personal del maestro
            maestro_response = supabase.table('maestro').select('*').eq('id_usuario', user_id).execute()
            if not maestro_response.data:
                return jsonify({
                    'success': False,
                    'error': 'Información del maestro no encontrada'
                }), 404
            
            return jsonify({
                'success': True,
                'data': maestro_response.data[0]
            })
        
        elif request.method == 'PUT':
            data = request.json
            
            # Validar que se envió JSON
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No se proporcionaron datos JSON'
                }), 400
            
            # Campos permitidos para actualización
            allowed_fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'fecha_nacimiento', 'especialidad']
            update_data = {field: data[field] for field in allowed_fields if field in data}
            
            # Validar fecha de nacimiento si se proporciona
            if 'fecha_nacimiento' in update_data:
                try:
                    datetime.strptime(update_data['fecha_nacimiento'], '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Formato de fecha de nacimiento inválido. Use YYYY-MM-DD'
                    }), 400
            
            # Actualizar información personal
            update_response = supabase.table('maestro').update(update_data).eq('id_usuario', user_id).execute()
            if not update_response.data:
                return jsonify({
                    'success': False,
                    'error': 'Error al actualizar la información'
                }), 500
            
            return jsonify({
                'success': True,
                'message': 'Información personal actualizada exitosamente',
                'data': update_response.data[0]
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@maestro_profile_bp.route('/availability', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_availability():
    """Endpoint para gestionar la disponibilidad horaria del maestro"""
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
        
        if request.method == 'GET':
            # Obtener toda la disponibilidad del maestro
            availability_response = supabase.table('disponibilidad').select('*').eq('id_maestro', user_id).execute()
            
            return jsonify({
                'success': True,
                'data': availability_response.data,
                'total': len(availability_response.data)
            })
        
        elif request.method == 'POST':
            # Crear nueva disponibilidad
            data = request.json
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No se proporcionaron datos JSON'
                }), 400
            
            # Validar campos requeridos
            required_fields = ['dia_semana', 'hora_inicio', 'hora_fin']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            
            if missing_fields:
                return jsonify({
                    'success': False,
                    'error': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
                }), 400
            
            # Validar formato de horas
            try:
                datetime.strptime(data['hora_inicio'], '%H:%M')
                datetime.strptime(data['hora_fin'], '%H:%M')
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de hora inválido. Use HH:MM'
                }), 400
            
            # Validar días de la semana válidos
            valid_days = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
            if data['dia_semana'].lower() not in valid_days:
                return jsonify({
                    'success': False,
                    'error': f'Día de la semana inválido. Debe ser uno de: {", ".join(valid_days)}'
                }), 400
            
            # Verificar que la hora de fin sea posterior a la hora de inicio
            inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
            fin = datetime.strptime(data['hora_fin'], '%H:%M').time()
            
            if fin <= inicio:
                return jsonify({
                    'success': False,
                    'error': 'La hora de fin debe ser posterior a la hora de inicio'
                }), 400
            
            # Verificar conflictos de horario
            existing_availability = supabase.table('disponibilidad').select('*').eq('id_maestro', user_id).eq('dia_semana', data['dia_semana']).execute()
            
            for existing in existing_availability.data:
                existing_inicio = datetime.strptime(existing['hora_inicio'], '%H:%M:%S').time()
                existing_fin = datetime.strptime(existing['hora_fin'], '%H:%M:%S').time()
                
                # Verificar solapamiento
                if not (fin <= existing_inicio or inicio >= existing_fin):
                    return jsonify({
                        'success': False,
                        'error': f'Conflicto de horario con disponibilidad existente: {existing["hora_inicio"]} - {existing["hora_fin"]}'
                    }), 409
            
            # Crear nueva disponibilidad
            availability_data = {
                'id_maestro': user_id,
                'dia_semana': data['dia_semana'].lower(),
                'hora_inicio': data['hora_inicio'],
                'hora_fin': data['hora_fin']
            }
            
            create_response = supabase.table('disponibilidad').insert(availability_data).execute()
            
            if not create_response.data:
                return jsonify({
                    'success': False,
                    'error': 'Error al crear la disponibilidad'
                }), 500
            
            return jsonify({
                'success': True,
                'message': 'Disponibilidad creada exitosamente',
                'data': create_response.data[0]
            }), 201
        
        elif request.method == 'PUT':
            # Actualizar disponibilidad existente
            data = request.json
            
            if not data or 'id_disponibilidad' not in data:
                return jsonify({
                    'success': False,
                    'error': 'ID de disponibilidad requerido'
                }), 400
            
            id_disponibilidad = data['id_disponibilidad']
            
            # Verificar que la disponibilidad pertenece al maestro
            existing_response = supabase.table('disponibilidad').select('*').eq('id_disponibilidad', id_disponibilidad).eq('id_maestro', user_id).execute()
            
            if not existing_response.data:
                return jsonify({
                    'success': False,
                    'error': 'Disponibilidad no encontrada o no pertenece al maestro'
                }), 404
            
            # Campos permitidos para actualización
            allowed_fields = ['dia_semana', 'hora_inicio', 'hora_fin']
            update_data = {field: data[field] for field in allowed_fields if field in data}
            
            # Validar formato de horas si se proporcionan
            if 'hora_inicio' in update_data:
                try:
                    datetime.strptime(update_data['hora_inicio'], '%H:%M')
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Formato de hora de inicio inválido. Use HH:MM'
                    }), 400
            
            if 'hora_fin' in update_data:
                try:
                    datetime.strptime(update_data['hora_fin'], '%H:%M')
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Formato de hora de fin inválido. Use HH:MM'
                    }), 400
            
            # Validar día de la semana si se proporciona
            if 'dia_semana' in update_data:
                valid_days = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
                if update_data['dia_semana'].lower() not in valid_days:
                    return jsonify({
                        'success': False,
                        'error': f'Día de la semana inválido. Debe ser uno de: {", ".join(valid_days)}'
                    }), 400
                update_data['dia_semana'] = update_data['dia_semana'].lower()
            
            # Actualizar disponibilidad
            update_response = supabase.table('disponibilidad').update(update_data).eq('id_disponibilidad', id_disponibilidad).execute()
            
            if not update_response.data:
                return jsonify({
                    'success': False,
                    'error': 'Error al actualizar la disponibilidad'
                }), 500
            
            return jsonify({
                'success': True,
                'message': 'Disponibilidad actualizada exitosamente',
                'data': update_response.data[0]
            })
        
        elif request.method == 'DELETE':
            # Eliminar disponibilidad
            data = request.json
            
            if not data or 'id_disponibilidad' not in data:
                return jsonify({
                    'success': False,
                    'error': 'ID de disponibilidad requerido'
                }), 400
            
            id_disponibilidad = data['id_disponibilidad']
            
            # Verificar que la disponibilidad pertenece al maestro
            existing_response = supabase.table('disponibilidad').select('*').eq('id_disponibilidad', id_disponibilidad).eq('id_maestro', user_id).execute()
            
            if not existing_response.data:
                return jsonify({
                    'success': False,
                    'error': 'Disponibilidad no encontrada o no pertenece al maestro'
                }), 404
            
            # Eliminar disponibilidad
            delete_response = supabase.table('disponibilidad').delete().eq('id_disponibilidad', id_disponibilidad).execute()
            
            if not delete_response.data:
                return jsonify({
                    'success': False,
                    'error': 'Error al eliminar la disponibilidad'
                }), 500
            
            return jsonify({
                'success': True,
                'message': 'Disponibilidad eliminada exitosamente',
                'data': delete_response.data[0]
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@maestro_profile_bp.route('/availability/summary', methods=['GET'])
def get_availability_summary():
    """Endpoint para obtener un resumen de la disponibilidad del maestro por día"""
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
        
        # Obtener disponibilidad ordenada por día y hora
        availability_response = supabase.table('disponibilidad').select('*').eq('id_maestro', user_id).order('dia_semana').order('hora_inicio').execute()
        
        # Organizar por día de la semana
        days_order = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        summary = {day: [] for day in days_order}
        
        for availability in availability_response.data:
            day = availability['dia_semana']
            if day in summary:
                summary[day].append({
                    'id_disponibilidad': availability['id_disponibilidad'],
                    'hora_inicio': availability['hora_inicio'],
                    'hora_fin': availability['hora_fin']
                })
        
        return jsonify({
            'success': True,
            'data': summary,
            'total_slots': len(availability_response.data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500
