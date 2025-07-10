from flask import Blueprint, jsonify, request, session
import bcrypt
from functools import wraps
from app.utils.supabase_connection import supabaseConnection as sC

admin_auth_bp = Blueprint("admin_auth", __name__)

def admin_required(f):
    """Decorador para proteger rutas de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'role' not in session:
            return jsonify({
                'success': False,
                'error': 'No autenticado'
            }), 401
        
        if session['role'] != 'admin':
            return jsonify({
                'success': False,
                'error': 'Acceso denegado - Solo administradores'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

@admin_auth_bp.route('/login', methods=['POST'])
def admin_login():
    """Endpoint para autenticar administradores"""
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
        
        # Verificar que el usuario sea administrador
        if user['role'] != 'admin':
            return jsonify({
                'success': False,
                'error': 'Acceso denegado - Solo administradores pueden acceder'
            }), 403
        
        # Verificar contraseña
        if not bcrypt.checkpw(contrasena.encode('utf-8'), user['contrasena'].encode('utf-8')):
            return jsonify({
                'success': False,
                'error': 'Credenciales inválidas'
            }), 401
        
        # Crear sesión de administrador
        session['user_id'] = id_usuario
        session['role'] = user['role']
        session['authenticated'] = True
        session['admin_session'] = True
        
        # Respuesta exitosa (sin incluir contraseña)
        return jsonify({
            'success': True,
            'message': 'Login de administrador exitoso',
            'data': {
                'user_id': id_usuario,
                'role': user['role']
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@admin_auth_bp.route('/logout', methods=['POST'])
@admin_required
def admin_logout():
    """Endpoint para cerrar sesión de administradores"""
    try:
        # Limpiar sesión
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Sesión de administrador cerrada exitosamente'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@admin_auth_bp.route('/session', methods=['GET'])
def check_admin_session():
    """Endpoint para verificar el estado de la sesión de administrador"""
    try:
        if ('user_id' not in session or 'role' not in session or 
            not session.get('authenticated') or not session.get('admin_session')):
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'No hay sesión de administrador activa'
            }), 401
        
        # Verificar que sea administrador
        if session['role'] != 'admin':
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
