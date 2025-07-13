from flask import Blueprint, jsonify, request, session
from datetime import datetime
from app.utils.supabase_connection import supabaseConnection as sC

maestro_profile_bp = Blueprint("maestro_profile", __name__)

def _error_response(message, status_code=400, details=None):
    """Helper para estandarizar respuestas de error."""
    response = {
        'success': False,
        'error': {
            'message': message,
            'code': status_code
        }
    }
    if details:
        response['error']['details'] = details
    return jsonify(response), status_code

def _check_auth(role_expected='maestro'):
    """Valida autenticación y rol, retorna error JSON si falla, o None si pasa."""
    if 'user_id' not in session or 'role' not in session:
        return _error_response('No autenticado', 401)
    if session['role'] != role_expected:
        return _error_response(f'Acceso denegado - Solo {role_expected}s', 403)
    return None

@maestro_profile_bp.route('/profile', methods=['GET', 'PUT'])
def manage_profile():
    try:
        auth_error = _check_auth()
        if auth_error:
            return auth_error

        user_id = session['user_id']
        supabase = sC.get_instance().get_client()

        if request.method == 'GET':
            try:
                maestro_response = supabase.table('maestro').select('*').eq('id_usuario', user_id).execute()
            except Exception as e:
                return _error_response(f'Error al obtener información del maestro: {str(e)}', 500)

            if not maestro_response.data:
                return _error_response('Información del maestro no encontrada', 404)

            return jsonify({
                'success': True,
                'data': maestro_response.data[0]
            })

        elif request.method == 'PUT':
            data = request.get_json(force=True, silent=True)
            if not data:
                return _error_response('No se proporcionaron datos JSON', 400)

            allowed_fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'fecha_nacimiento', 'especialidad']
            update_data = {field: data[field] for field in allowed_fields if field in data}

            if 'fecha_nacimiento' in update_data:
                try:
                    datetime.strptime(update_data['fecha_nacimiento'], '%Y-%m-%d')
                except ValueError:
                    return _error_response('Formato de fecha de nacimiento inválido. Use YYYY-MM-DD', 400)

            try:
                update_response = supabase.table('maestro').update(update_data).eq('id_usuario', user_id).execute()
            except Exception as e:
                return _error_response(f'Error al actualizar la información: {str(e)}', 500)

            if not update_response.data:
                return _error_response('No se actualizó la información (registro no encontrado)', 404)

            return jsonify({
                'success': True,
                'message': 'Información personal actualizada exitosamente',
                'data': update_response.data[0]
            })

    except Exception as e:
        return _error_response(f'Error interno del servidor: {str(e)}', 500)

@maestro_profile_bp.route('/availability', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_availability():
    """Endpoint para gestionar la disponibilidad horaria del maestro"""
    try:
        auth_error = _check_auth()
        if auth_error:
            return auth_error

        user_id = session['user_id']
        supabase = sC.get_instance().get_client()

        if request.method == 'GET':
            try:
                availability_response = supabase.table('disponibilidad').select('*').eq('id_maestro', user_id).execute()
            except Exception as e:
                return _error_response(f'Error al obtener disponibilidad: {str(e)}', 500)

            data = availability_response.data or []
            return jsonify({
                'success': True,
                'data': data,
                'total': len(data)
            })

        data = request.get_json(force=True, silent=True)
        if not data and request.method in ['POST', 'PUT', 'DELETE']:
            return _error_response('No se proporcionaron datos JSON', 400)

        valid_days = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']

        if request.method == 'POST':
            required_fields = ['dia_semana', 'hora_inicio', 'hora_fin']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return _error_response(f'Campos requeridos faltantes: {", ".join(missing_fields)}', 400)

            dia = data['dia_semana'].lower()
            if dia not in valid_days:
                return _error_response(f'Día de la semana inválido. Debe ser uno de: {", ".join(valid_days)}', 400)

            try:
                inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
                fin = datetime.strptime(data['hora_fin'], '%H:%M').time()
            except ValueError:
                return _error_response('Formato de hora inválido. Use HH:MM', 400)

            if fin <= inicio:
                return _error_response('La hora de fin debe ser posterior a la hora de inicio', 400)

            try:
                existing_availability = supabase.table('disponibilidad').select('*').eq('id_maestro', user_id).eq('dia_semana', dia).execute()
            except Exception as e:
                return _error_response(f'Error al consultar disponibilidad existente: {str(e)}', 500)

            existing_data = existing_availability.data or []
            for existing in existing_data:
                existing_inicio = datetime.strptime(existing['hora_inicio'], '%H:%M:%S').time()
                existing_fin = datetime.strptime(existing['hora_fin'], '%H:%M:%S').time()
                if not (fin <= existing_inicio or inicio >= existing_fin):
                    conflict = f"{existing['hora_inicio']} - {existing['hora_fin']}"
                    return _error_response(f'Conflicto de horario con disponibilidad existente: {conflict}', 409)

            availability_data = {
                'id_maestro': user_id,
                'dia_semana': dia,
                'hora_inicio': data['hora_inicio'],
                'hora_fin': data['hora_fin']
            }

            try:
                create_response = supabase.table('disponibilidad').insert(availability_data).execute()
            except Exception as e:
                return _error_response(f'Error al crear la disponibilidad: {str(e)}', 500)

            if not create_response.data:
                return _error_response('No se pudo crear la disponibilidad', 500)

            return jsonify({
                'success': True,
                'message': 'Disponibilidad creada exitosamente',
                'data': create_response.data[0]
            }), 201

        elif request.method == 'PUT':
            if 'id_disponibilidad' not in data:
                return _error_response('ID de disponibilidad requerido', 400)

            id_disponibilidad = data['id_disponibilidad']

            try:
                existing_response = supabase.table('disponibilidad').select('*').eq('id_disponibilidad', id_disponibilidad).eq('id_maestro', user_id).execute()
            except Exception as e:
                return _error_response(f'Error al consultar disponibilidad: {str(e)}', 500)

            if not existing_response.data:
                return _error_response('Disponibilidad no encontrada o no pertenece al maestro', 404)

            allowed_fields = ['dia_semana', 'hora_inicio', 'hora_fin']
            update_data = {field: data[field] for field in allowed_fields if field in data}

            if 'dia_semana' in update_data:
                dia = update_data['dia_semana'].lower()
                if dia not in valid_days:
                    return _error_response(f'Día de la semana inválido. Debe ser uno de: {", ".join(valid_days)}', 400)
                update_data['dia_semana'] = dia

            if 'hora_inicio' in update_data:
                try:
                    datetime.strptime(update_data['hora_inicio'], '%H:%M')
                except ValueError:
                    return _error_response('Formato de hora de inicio inválido. Use HH:MM', 400)

            if 'hora_fin' in update_data:
                try:
                    datetime.strptime(update_data['hora_fin'], '%H:%M')
                except ValueError:
                    return _error_response('Formato de hora de fin inválido. Use HH:MM', 400)

            if 'hora_inicio' in update_data and 'hora_fin' in update_data:
                inicio = datetime.strptime(update_data['hora_inicio'], '%H:%M').time()
                fin = datetime.strptime(update_data['hora_fin'], '%H:%M').time()
                if fin <= inicio:
                    return _error_response('La hora de fin debe ser posterior a la hora de inicio', 400)

            try:
                update_response = supabase.table('disponibilidad').update(update_data).eq('id_disponibilidad', id_disponibilidad).execute()
            except Exception as e:
                return _error_response(f'Error al actualizar la disponibilidad: {str(e)}', 500)

            if not update_response.data:
                return _error_response('No se actualizó la disponibilidad', 404)

            return jsonify({
                'success': True,
                'message': 'Disponibilidad actualizada exitosamente',
                'data': update_response.data[0]
            })

        elif request.method == 'DELETE':
            if 'id_disponibilidad' not in data:
                return _error_response('ID de disponibilidad requerido', 400)

            id_disponibilidad = data['id_disponibilidad']

            try:
                existing_response = supabase.table('disponibilidad').select('*').eq('id_disponibilidad', id_disponibilidad).eq('id_maestro', user_id).execute()
            except Exception as e:
                return _error_response(f'Error al consultar disponibilidad: {str(e)}', 500)

            if not existing_response.data:
                return _error_response('Disponibilidad no encontrada o no pertenece al maestro', 404)

            try:
                delete_response = supabase.table('disponibilidad').delete().eq('id_disponibilidad', id_disponibilidad).execute()
            except Exception as e:
                return _error_response(f'Error al eliminar la disponibilidad: {str(e)}', 500)

            if not delete_response.data:
                return _error_response('No se eliminó la disponibilidad', 404)

            return jsonify({
                'success': True,
                'message': 'Disponibilidad eliminada exitosamente',
                'data': delete_response.data[0]
            })

    except Exception as e:
        return _error_response(f'Error interno del servidor: {str(e)}', 500)

@maestro_profile_bp.route('/availability/summary', methods=['GET'])
def get_availability_summary():
    """Endpoint para obtener un resumen de la disponibilidad del maestro por día"""
    try:
        auth_error = _check_auth()
        if auth_error:
            return auth_error

        user_id = session['user_id']
        supabase = sC.get_instance().get_client()

        try:
            availability_response = supabase.table('disponibilidad').select('*').eq('id_maestro', user_id).order('dia_semana').order('hora_inicio').execute()
        except Exception as e:
            return _error_response(f'Error al obtener disponibilidad: {str(e)}', 500)

        data = availability_response.data or []
        if not data:
            return jsonify({
                'success': True,
                'data': {},
                'total_slots': 0
            })

        days_order = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        summary = {day: [] for day in days_order}

        for availability in data:
            day = availability['dia_semana']
            if day in summary:
                summary[day].append({
                    'id_disponibilidad': availability['id_disponibilidad'],
                    'hora_inicio': availability['hora_inicio'],
                    'hora_fin': availability['hora_fin']
                })

        total_slots = sum(len(slots) for slots in summary.values())

        return jsonify({
            'success': True,
            'data': summary,
            'total_slots': total_slots
        })


    except Exception as e:
        return _error_response(f'Error interno del servidor: {str(e)}', 500)
