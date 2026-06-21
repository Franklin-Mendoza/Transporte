from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask import jsonify
from app.models import Usuario
import uuid


def rol_requerido(*roles):
    """
    Decorador que verifica que el usuario autenticado tenga uno de los roles indicados.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id_str = get_jwt_identity()

            # Convertir explícitamente a UUID para evitar fallos silenciosos
            # de SQLAlchemy al comparar string vs UUID en PostgreSQL
            try:
                user_uuid = uuid.UUID(str(user_id_str))
            except (ValueError, AttributeError):
                return jsonify({"ok": False, "mensaje": "Token inválido"}), 401

            usuario = Usuario.query.get(user_uuid)

            if not usuario or not usuario.activo:
                return jsonify({"ok": False, "mensaje": "Usuario no encontrado o inactivo"}), 401

            if usuario.rol.nombre not in roles:
                return jsonify({
                    "ok": False,
                    "mensaje": f"Acceso denegado. Se requiere rol: {', '.join(roles)}"
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def solo_admin(fn):
    return rol_requerido("admin")(fn)


def admin_o_autoridad(fn):
    return rol_requerido("admin", "autoridad")(fn)


def solo_chofer(fn):
    return rol_requerido("chofer")(fn)


def usuario_activo_requerido(fn):
    """Solo verifica que el JWT sea válido y el usuario esté activo."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        usuario = Usuario.query.get(user_id)
        if not usuario or not usuario.activo:
            return jsonify({"ok": False, "mensaje": "Usuario inactivo o no existe"}), 401
        return fn(*args, **kwargs)
    return wrapper
