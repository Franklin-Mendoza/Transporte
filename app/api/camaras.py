from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import uuid as _uuid
from app import db
from app.models import CamaraParada, Parada
from app.utils import ok, error, solo_admin, admin_o_autoridad

camaras_bp = Blueprint("camaras", __name__, url_prefix="/api/camaras")


@camaras_bp.route("/", methods=["GET"])
@jwt_required()
@admin_o_autoridad
def listar_camaras():
    """Lista todas las asignaciones cámara-parada existentes."""
    asignaciones = CamaraParada.query.all()
    return ok([a.to_dict() for a in asignaciones])


@camaras_bp.route("/parada/<int:parada_id>", methods=["GET"])
@jwt_required()
@admin_o_autoridad
def obtener_camara_de_parada(parada_id):
    """Obtiene la cámara asignada a una parada específica (si existe)."""
    asignacion = CamaraParada.query.filter_by(parada_id=parada_id).first()
    if not asignacion:
        return ok(None, "Esta parada no tiene cámara asignada")
    return ok(asignacion.to_dict())


@camaras_bp.route("/asignar", methods=["POST"])
@jwt_required()
@solo_admin
def asignar_camara():
    """
    Asigna (o reasigna) una cámara web a una parada.
    Body: { parada_id, device_id, device_label }
    """
    admin_id = _uuid.UUID(str(get_jwt_identity()))
    data = request.get_json()

    parada_id = data.get("parada_id")
    device_id = data.get("device_id", "").strip()
    device_label = data.get("device_label", "").strip()

    if not parada_id or not device_id:
        return error("parada_id y device_id son obligatorios", 400)

    parada = Parada.query.get(parada_id)
    if not parada:
        return error("Parada no encontrada", 404)

    # Si esta parada ya tiene una cámara asignada, la actualizamos
    asignacion = CamaraParada.query.filter_by(parada_id=parada_id).first()
    if asignacion:
        asignacion.device_id = device_id
        asignacion.device_label = device_label
        asignacion.activa = True
        asignacion.asignada_por = admin_id
    else:
        asignacion = CamaraParada(
            parada_id=parada_id,
            device_id=device_id,
            device_label=device_label,
            asignada_por=admin_id,
        )
        db.session.add(asignacion)

    db.session.commit()
    return ok(asignacion.to_dict(), "Cámara asignada correctamente")


@camaras_bp.route("/<int:asignacion_id>", methods=["DELETE"])
@jwt_required()
@solo_admin
def quitar_asignacion(asignacion_id):
    """Quita la asignación de cámara de una parada (vuelve a quedar sin cámara)."""
    asignacion = CamaraParada.query.get(asignacion_id)
    if not asignacion:
        return error("Asignación no encontrada", 404)
    db.session.delete(asignacion)
    db.session.commit()
    return ok(mensaje="Asignación eliminada. La parada ya no tiene cámara.")


@camaras_bp.route("/<int:asignacion_id>/activar", methods=["PUT"])
@jwt_required()
@solo_admin
def alternar_activa(asignacion_id):
    """Activa o desactiva una cámara sin eliminar la asignación (ej: cámara dañada temporalmente)."""
    asignacion = CamaraParada.query.get(asignacion_id)
    if not asignacion:
        return error("Asignación no encontrada", 404)

    data = request.get_json(silent=True) or {}
    if "activa" in data:
        asignacion.activa = bool(data["activa"])
    else:
        asignacion.activa = not asignacion.activa

    db.session.commit()
    return ok(asignacion.to_dict(), "Estado de la cámara actualizado")
