from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Notificacion, TokenDispositivo
from app.utils import ok, error

notificaciones_bp = Blueprint("notificaciones", __name__, url_prefix="/api/notificaciones")


@notificaciones_bp.route("/", methods=["GET"])
@jwt_required()
def mis_notificaciones():
    """Lista las notificaciones del usuario autenticado."""
    import uuid as _uuid; user_id = _uuid.UUID(str(get_jwt_identity()))
    solo_no_leidas = request.args.get("no_leidas", "false").lower() == "true"
    limite = request.args.get("limite", 30, type=int)

    query = Notificacion.query.filter_by(usuario_id=user_id)
    if solo_no_leidas:
        query = query.filter_by(leida=False)

    notifs = query.order_by(Notificacion.creada_en.desc()).limit(limite).all()
    return ok([n.to_dict() for n in notifs])


@notificaciones_bp.route("/<int:notif_id>/leer", methods=["PUT"])
@jwt_required()
def marcar_leida(notif_id):
    """Marca una notificación como leída."""
    import uuid as _uuid; user_id = _uuid.UUID(str(get_jwt_identity()))
    notif = Notificacion.query.filter_by(id=notif_id, usuario_id=user_id).first()
    if not notif:
        return error("Notificación no encontrada", 404)
    notif.leida = True
    notif.leida_en = datetime.utcnow()
    db.session.commit()
    return ok(mensaje="Notificación marcada como leída")


@notificaciones_bp.route("/leer-todas", methods=["PUT"])
@jwt_required()
def marcar_todas_leidas():
    """Marca todas las notificaciones del usuario como leídas."""
    import uuid as _uuid; user_id = _uuid.UUID(str(get_jwt_identity()))
    Notificacion.query.filter_by(usuario_id=user_id, leida=False)\
        .update({"leida": True, "leida_en": datetime.utcnow()})
    db.session.commit()
    return ok(mensaje="Todas las notificaciones marcadas como leídas")


@notificaciones_bp.route("/no-leidas/count", methods=["GET"])
@jwt_required()
def count_no_leidas():
    """Cuenta notificaciones no leídas (para el badge en la app)."""
    import uuid as _uuid; user_id = _uuid.UUID(str(get_jwt_identity()))
    count = Notificacion.query.filter_by(usuario_id=user_id, leida=False).count()
    return ok({"no_leidas": count})


@notificaciones_bp.route("/token", methods=["POST"])
@jwt_required()
def registrar_token():
    """
    Registra o actualiza el token FCM del dispositivo del usuario.
    Body: { token, plataforma }  plataforma: android | ios
    La app Flutter llama esto al iniciar sesión.
    """
    import uuid as _uuid; user_id = _uuid.UUID(str(get_jwt_identity()))
    data = request.get_json()
    token = data.get("token", "").strip()
    plataforma = data.get("plataforma", "android")

    if not token:
        return error("token es obligatorio", 400)

    # Desactivar tokens anteriores del mismo usuario
    TokenDispositivo.query.filter_by(usuario_id=user_id, activo=True)\
        .update({"activo": False})

    nuevo_token = TokenDispositivo(
        usuario_id=user_id,
        token=token,
        plataforma=plataforma,
        activo=True,
    )
    db.session.add(nuevo_token)
    db.session.commit()
    return ok(mensaje="Token FCM registrado correctamente")


@notificaciones_bp.route("/token", methods=["DELETE"])
@jwt_required()
def eliminar_token():
    """Desactiva el token FCM (cuando el usuario cierra sesión)."""
    import uuid as _uuid; user_id = _uuid.UUID(str(get_jwt_identity()))
    TokenDispositivo.query.filter_by(usuario_id=user_id, activo=True)\
        .update({"activo": False})
    db.session.commit()
    return ok(mensaje="Token FCM desactivado")
