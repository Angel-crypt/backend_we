from flask import Blueprint, jsonify, request, session
import bcrypt
from app.utils.supabase_connection import supabaseConnection as sC

maestro_auth_bp = Blueprint("maestro_auth", __name__)

@maestro_auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint para autenticar maestros"""
    try:
        data = request.json
        
        # Validar que se envió JSON
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos JSON'
            }), 400
        
        # Validar campos requeridos
        required_fields = ['id_usuario', 'contrasena']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
            }), 400
        
        id_usuario = data['id_usuario']
        contrasena = data['contrasena']
        
        # Obtener conexión a Supabase
        supabase = sC.get_instance().get_client()
        
        # Buscar usuario
        user_response = supabase.table('usuario').select('*').eq('id_usuario', id_usuario).execute()
        
        if not user_response.data:
            return jsonify({
                'success': False,
                'error': 'Credenciales inválidas'
            }), 401
        
        user = user_response.data[0]
        
        # Verificar que el usuario sea maestro
        if user['role'] != 'maestro':
            return jsonify({
                'success': False,
                'error': 'Acceso denegado - Solo maestros pueden acceder'
            }), 403
        
        # Verificar contraseña
        if not bcrypt.checkpw(contrasena.encode('utf-8'), user['contrasena'].encode('utf-8')):
            return jsonify({
                'success': False,
                'error': 'Credenciales inválidas'
            }), 401
        
        # Obtener información del maestro
        maestro_response = supabase.table('maestro').select('*').eq('id_usuario', id_usuario).execute()
        
        if not maestro_response.data:
            return jsonify({
                'success': False,
                'error': 'Información del maestro no encontrada'
            }), 404
        
        maestro = maestro_response.data[0]
        
        # Crear sesión
        session['user_id'] = id_usuario
        session['role'] = user['role']
        session['authenticated'] = True
        
        # Respuesta exitosa (sin incluir contraseña)
        return jsonify({
            'success': True,
            'message': 'Login exitoso'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@maestro_auth_bp.route('/logout', methods=['POST'])
def logout():
    """Endpoint para cerrar sesión de maestros"""
    try:
        # Limpiar sesión
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Sesión cerrada exitosamente'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@maestro_auth_bp.route('/session', methods=['GET'])
def check_session():
    """Endpoint para verificar el estado de la sesión"""
    try:
        if 'user_id' not in session or 'role' not in session or not session.get('authenticated'):
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'No hay sesión activa'
            }), 401
        
        # Verificar que sea maestro
        if session['role'] != 'maestro':
            session.clear()
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'Rol inválido'
            }), 403
        
        return jsonify({
            'success': True,
            'authenticated': True,
            'data': {
                'user_id': session['user_id'],
                'role': session['role']
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500
