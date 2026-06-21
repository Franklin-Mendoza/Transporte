from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from flask_bcrypt import Bcrypt
from app import db
from app.models import Usuario, Rol
from app.utils import ok, error

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
bcrypt = Bcrypt()


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login con CI o email + contraseña.
    Devuelve access_token y refresh_token.
    """
    data = request.get_json()
    if not data:
        return error("Se requiere JSON con credenciales", 400)

    identificador = data.get("identificador") or data.get("email") or data.get("numero_ci")
    password = data.get("password")

    if not identificador or not password:
        return error("Se requiere identificador (CI o email) y contraseña", 400)

    # Buscar por email o CI
    usuario = Usuario.query.filter(
        (Usuario.email == identificador) | (Usuario.numero_ci == identificador)
    ).first()

    if not usuario or not usuario.activo:
        return error("Usuario no encontrado o inactivo", 401)

    if not bcrypt.check_password_hash(usuario.password_hash, password):
        return error("Contraseña incorrecta", 401)

    access_token = create_access_token(identity=str(usuario.id))
    refresh_token = create_refresh_token(identity=str(usuario.id))

    return ok({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "usuario": usuario.to_dict(),
    }, "Login exitoso")


@auth_bp.route("/registro-pasajero", methods=["POST"])
def registro_pasajero():
    """
    Autoregistro solo para pasajeros.
    Campos: nombre, apellido, numero_ci, password (email opcional).
    """
    data = request.get_json()
    if not data:
        return error("Se requiere JSON", 400)

    nombre = data.get("nombre", "").strip()
    apellido = data.get("apellido", "").strip()
    numero_ci = data.get("numero_ci", "").strip()
    password = data.get("password", "")
    email = data.get("email", "").strip() or None

    if not nombre or not apellido or not numero_ci or not password:
        return error("nombre, apellido, numero_ci y password son obligatorios", 400)

    if len(password) < 6:
        return error("La contraseña debe tener al menos 6 caracteres", 400)

    # Verificar CI duplicado
    if Usuario.query.filter_by(numero_ci=numero_ci).first():
        return error("Ya existe un usuario con ese número de CI", 409)

    if email and Usuario.query.filter_by(email=email).first():
        return error("Ya existe un usuario con ese email", 409)

    rol_pasajero = Rol.query.filter_by(nombre="pasajero").first()
    if not rol_pasajero:
        return error("Configuración de roles incorrecta", 500)

    hash_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    nuevo = Usuario(
        nombre=nombre,
        apellido=apellido,
        numero_ci=numero_ci,
        email=email,
        password_hash=hash_pw,
        rol_id=rol_pasajero.id,
        puede_autoregistrarse=True,
        creado_por=None,  # Se autoregistró
    )
    db.session.add(nuevo)
    db.session.commit()

    access_token = create_access_token(identity=str(nuevo.id))
    return ok({
        "access_token": access_token,
        "usuario": nuevo.to_dict(),
    }, "Registro exitoso", 201)


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Renueva el access_token usando el refresh_token."""
    import uuid as _uuid; user_id = _uuid.UUID(str(get_jwt_identity()))
    nuevo_token = create_access_token(identity=user_id)
    return ok({"access_token": nuevo_token}, "Token renovado")


@auth_bp.route("/perfil", methods=["GET"])
@jwt_required()
def perfil():
    """Devuelve los datos del usuario autenticado."""
    import uuid as _uuid; user_id = _uuid.UUID(str(get_jwt_identity()))
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return error("Usuario no encontrado", 404)
    return ok(usuario.to_dict())


@auth_bp.route("/cambiar-password", methods=["PUT"])
@jwt_required()
def cambiar_password():
    """Cambia la contraseña del usuario autenticado."""
    import uuid as _uuid; user_id = _uuid.UUID(str(get_jwt_identity()))
    usuario = Usuario.query.get(user_id)
    data = request.get_json()

    password_actual = data.get("password_actual")
    password_nuevo = data.get("password_nuevo")

    if not password_actual or not password_nuevo:
        return error("Se requiere password_actual y password_nuevo", 400)

    if not bcrypt.check_password_hash(usuario.password_hash, password_actual):
        return error("Contraseña actual incorrecta", 401)

    if len(password_nuevo) < 6:
        return error("La nueva contraseña debe tener al menos 6 caracteres", 400)

    usuario.password_hash = bcrypt.generate_password_hash(password_nuevo).decode("utf-8")
    db.session.commit()
    return ok(mensaje="Contraseña actualizada correctamente")
