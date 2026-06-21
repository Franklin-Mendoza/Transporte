from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Turno, Minibus, Usuario
from app.utils import ok, error, solo_chofer, admin_o_autoridad

turnos_bp = Blueprint("turnos", __name__, url_prefix="/api/turnos")


@turnos_bp.route("/mi-turno", methods=["GET"])
@jwt_required()
@solo_chofer
def mi_turno_activo():
    """El chofer consulta su turno activo actual con la ruta y paradas."""
    import uuid as _uuid
    user_id = _uuid.UUID(str(get_jwt_identity()))

    turno = Turno.query.filter_by(
        chofer_id=user_id, estado="activo"
    ).order_by(Turno.creado_en.desc()).first()

    if not turno:
        return ok(None, "Sin turno activo en este momento")

    data = turno.to_dict()
    # Incluir las paradas de la ruta
    if turno.ruta:
        data["paradas"] = [p.to_dict() for p in turno.ruta.paradas]

    # Incluir registros del turno actual
    registros = turno.registros.order_by(
        db.text("registrado_en DESC")
    ).limit(20).all()
    data["registros_recientes"] = [r.to_dict() for r in registros]

    return ok(data)


@turnos_bp.route("/mi-historial", methods=["GET"])
@jwt_required()
@solo_chofer
def mi_historial():
    """Historial de turnos del chofer autenticado."""
    import uuid as _uuid
    user_id = _uuid.UUID(str(get_jwt_identity()))
    limite = request.args.get("limite", 20, type=int)

    turnos = Turno.query.filter_by(chofer_id=user_id)\
        .order_by(Turno.creado_en.desc()).limit(limite).all()

    return ok([t.to_dict() for t in turnos])


@turnos_bp.route("/iniciar", methods=["POST"])
@jwt_required()
@solo_chofer
def iniciar_turno():
    """
    El chofer inicia su turno manualmente desde la app.
    """
    import uuid as _uuid
    user_id_str = get_jwt_identity()
    try:
        user_id = _uuid.UUID(str(user_id_str))
    except (ValueError, AttributeError):
        return error("Token inválido", 401)

    # silent=True evita que Flask/Werkzeug truene con un BadRequest cuando
    # el cliente (la app Flutter) manda el POST sin body. Este endpoint no
    # necesita ningún dato del body de todas formas.
    data = request.get_json(silent=True) or {}

    # Verificar que no tenga ya un turno activo
    turno_activo = Turno.query.filter_by(chofer_id=user_id, estado="activo").first()
    if turno_activo:
        return error("Ya tienes un turno activo. Finalízalo primero.", 400)

    bus = Minibus.query.filter_by(chofer_id=user_id, activo=True).first()

    if not bus:
        return error("No tienes un minibús asignado. Contacta al admin.", 400)

    if not bus.ruta_id:
        return error("El minibús no tiene una ruta asignada.", 400)

    turno = Turno(
        minibus_id=bus.id,
        chofer_id=user_id,
        ruta_id=bus.ruta_id,
        hora_inicio=datetime.utcnow(),
        estado="activo",
    )
    db.session.add(turno)
    db.session.commit()

    data_resp = turno.to_dict()
    if turno.ruta:
        data_resp["paradas"] = [p.to_dict() for p in turno.ruta.paradas]

    return ok(data_resp, "Turno iniciado correctamente", 201)


@turnos_bp.route("/<int:turno_id>/finalizar", methods=["PUT"])
@jwt_required()
@solo_chofer
def finalizar_turno(turno_id):
    """El chofer finaliza su turno."""
    import uuid as _uuid
    user_id = _uuid.UUID(str(get_jwt_identity()))
    turno = Turno.query.filter_by(id=turno_id, chofer_id=user_id).first()

    if not turno:
        return error("Turno no encontrado", 404)

    if turno.estado != "activo":
        return error("Este turno ya fue finalizado", 400)

    turno.estado = "finalizado"
    turno.hora_fin = datetime.utcnow()
    db.session.commit()

    # Recalcular calificación del chofer
    try:
        from app.services.calificaciones import calcular_calificacion_chofer
        periodo = datetime.utcnow().strftime("%Y-%m")
        calcular_calificacion_chofer(user_id, periodo)
    except Exception:
        pass

    return ok(turno.to_dict(), "Turno finalizado correctamente")


@turnos_bp.route("/", methods=["GET"])
@jwt_required()
@admin_o_autoridad
def listar_turnos():
    """Admin/autoridad lista todos los turnos con filtros."""
    chofer_id = request.args.get("chofer_id")
    estado = request.args.get("estado")
    limite = request.args.get("limite", 50, type=int)

    query = Turno.query
    if chofer_id:
        query = query.filter_by(chofer_id=chofer_id)
    if estado:
        query = query.filter_by(estado=estado)

    turnos = query.order_by(Turno.creado_en.desc()).limit(limite).all()
    return ok([t.to_dict() for t in turnos])
