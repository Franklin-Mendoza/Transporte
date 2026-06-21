from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from app import db
from app.models import Usuario, Rol
from app.utils import ok, error, solo_admin, admin_o_autoridad

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")
bcrypt = Bcrypt()


@usuarios_bp.route("/", methods=["GET"])
@jwt_required()
@admin_o_autoridad
def listar_usuarios():
    """Lista todos los usuarios. Admin ve todos, autoridad solo ve choferes y pasajeros."""
    rol_filtro = request.args.get("rol")
    activo_filtro = request.args.get("activo", "true").lower() == "true"

    query = Usuario.query.filter_by(activo=activo_filtro)
    if rol_filtro:
        query = query.join(Rol).filter(Rol.nombre == rol_filtro)

    usuarios = query.order_by(Usuario.creado_en.desc()).all()
    return ok([u.to_dict() for u in usuarios])


@usuarios_bp.route("/<string:usuario_id>", methods=["GET"])
@jwt_required()
@admin_o_autoridad
def obtener_usuario(usuario_id):
    """Obtiene un usuario por ID."""
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return error("Usuario no encontrado", 404)
    return ok(usuario.to_dict())


@usuarios_bp.route("/", methods=["POST"])
@jwt_required()
@solo_admin
def crear_usuario():
    """
    El admin crea usuarios de cualquier rol (chofer, autoridad, admin, pasajero).
    El caso de pasajero es excepcional: normalmente se autoregistra desde la
    app/web, pero el admin puede crearlo manualmente si la app falla o el
    pasajero no puede autoregistrarse.
    Solo el admin puede usar este endpoint.
    """
    data = request.get_json()
    admin_id = get_jwt_identity()

    nombre = data.get("nombre", "").strip()
    apellido = data.get("apellido", "").strip()
    numero_ci = data.get("numero_ci", "").strip()
    password = data.get("password", "")
    rol_nombre = data.get("rol", "chofer")
    email = data.get("email", "").strip() or None
    telefono = data.get("telefono", "").strip() or None

    if not nombre or not apellido or not numero_ci or not password:
        return error("nombre, apellido, numero_ci y password son obligatorios", 400)

    if len(password) < 6:
        return error("La contraseña debe tener al menos 6 caracteres", 400)

    # Verificar CI duplicado
    if Usuario.query.filter_by(numero_ci=numero_ci).first():
        return error("Ya existe un usuario con ese número de CI", 409)

    if email and Usuario.query.filter_by(email=email).first():
        return error("Ya existe un usuario con ese email", 409)

    rol = Rol.query.filter_by(nombre=rol_nombre).first()
    if not rol:
        return error(f"Rol '{rol_nombre}' no existe", 400)

    # El pasajero creado por el admin sigue pudiendo autoregistrarse en el futuro
    # con otro dispositivo, así que puede_autoregistrarse queda en True para ese rol
    puede_autoreg = (rol_nombre == "pasajero")

    hash_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    nuevo = Usuario(
        nombre=nombre,
        apellido=apellido,
        numero_ci=numero_ci,
        email=email,
        password_hash=hash_pw,
        telefono=telefono,
        rol_id=rol.id,
        puede_autoregistrarse=puede_autoreg,
        creado_por=admin_id,
    )
    db.session.add(nuevo)
    db.session.commit()

    return ok(nuevo.to_dict(), "Usuario creado correctamente", 201)


@usuarios_bp.route("/<string:usuario_id>", methods=["PUT"])
@jwt_required()
@solo_admin
def actualizar_usuario(usuario_id):
    """Actualiza datos de un usuario (solo admin)."""
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return error("Usuario no encontrado", 404)

    data = request.get_json()

    if "nombre" in data:
        usuario.nombre = data["nombre"].strip()
    if "apellido" in data:
        usuario.apellido = data["apellido"].strip()
    if "telefono" in data:
        usuario.telefono = data["telefono"].strip() or None
    if "email" in data:
        nuevo_email = data["email"].strip() or None
        if nuevo_email and nuevo_email != usuario.email:
            if Usuario.query.filter_by(email=nuevo_email).first():
                return error("Email ya en uso", 409)
        usuario.email = nuevo_email
    if "numero_ci" in data:
        nuevo_ci = data["numero_ci"].strip()
        if nuevo_ci != usuario.numero_ci:
            if Usuario.query.filter_by(numero_ci=nuevo_ci).first():
                return error("CI ya en uso", 409)
        usuario.numero_ci = nuevo_ci

    # Reset de contraseña por el admin
    if "password_nuevo" in data and data["password_nuevo"]:
        if len(data["password_nuevo"]) < 6:
            return error("La contraseña debe tener al menos 6 caracteres", 400)
        usuario.password_hash = bcrypt.generate_password_hash(
            data["password_nuevo"]
        ).decode("utf-8")

    db.session.commit()
    return ok(usuario.to_dict(), "Usuario actualizado")


@usuarios_bp.route("/<string:usuario_id>", methods=["DELETE"])
@jwt_required()
@solo_admin
def eliminar_usuario(usuario_id):
    """
    Desactiva un usuario (soft delete: activo=False).
    El admin no puede eliminarse a sí mismo.
    """
    admin_id = get_jwt_identity()
    if str(usuario_id) == str(admin_id):
        return error("No puedes desactivar tu propia cuenta", 400)

    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return error("Usuario no encontrado", 404)

    usuario.activo = False
    db.session.commit()
    return ok(mensaje=f"Usuario {usuario.nombre} {usuario.apellido} desactivado correctamente")


@usuarios_bp.route("/<string:usuario_id>/reactivar", methods=["PUT"])
@jwt_required()
@solo_admin
def reactivar_usuario(usuario_id):
    """Reactiva un usuario previamente desactivado."""
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return error("Usuario no encontrado", 404)
    usuario.activo = True
    db.session.commit()
    return ok(usuario.to_dict(), "Usuario reactivado")


@usuarios_bp.route("/choferes", methods=["GET"])
@jwt_required()
@admin_o_autoridad
def listar_choferes():
    """Listado rápido de todos los choferes activos."""
    choferes = Usuario.query.join(Rol).filter(
        Rol.nombre == "chofer",
        Usuario.activo == True
    ).all()
    return ok([u.to_dict() for u in choferes])
