from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid as _uuid
from app import db
from app.models import AlertaDesvio, Justificacion, Usuario, Minibus, Turno
from app.utils import ok, error, solo_admin, admin_o_autoridad, solo_chofer
from app.services import notificar_justificacion, notificar_desvio_chofer
from app.services.calificaciones import calcular_calificacion_chofer

alertas_bp = Blueprint("alertas", __name__, url_prefix="/api/alertas")


# ─────────────────────────────────────────────────────────────
# DENUNCIA MANUAL DEL PASAJERO (posible trameo)
# ─────────────────────────────────────────────────────────────

@alertas_bp.route("/denunciar", methods=["POST"])
def denunciar_pasajero():
    """
    Endpoint PÚBLICO: el pasajero denuncia manualmente que el minibús
    no está cumpliendo su ruta (trameo). No requiere login.

    Body: {
        codigo_qr (opcional si se manda placa),
        placa (opcional si se manda codigo_qr),
        latitud_pasajero, longitud_pasajero,   -> ubicación exacta al momento de denunciar
        comentario (opcional)
    }
    """
    data = request.get_json()
    codigo_qr = data.get("codigo_qr")
    placa = data.get("placa", "").strip().upper() if data.get("placa") else None
    lat = data.get("latitud_pasajero")
    lon = data.get("longitud_pasajero")
    comentario = data.get("comentario", "").strip()

    if not codigo_qr and not placa:
        return error("Se requiere codigo_qr o placa del minibús", 400)

    # Buscar el minibús por QR o por placa
    if codigo_qr:
        bus = Minibus.query.filter_by(codigo_qr=codigo_qr, activo=True).first()
    else:
        bus = Minibus.query.filter_by(placa=placa, activo=True).first()

    if not bus:
        return error("Minibús no encontrado con esos datos", 404)

    if not bus.chofer_id:
        return error("Este minibús no tiene chofer asignado actualmente", 400)

    # Buscar turno activo del bus (si existe)
    turno = Turno.query.filter_by(
        minibus_id=bus.id, estado="activo"
    ).order_by(Turno.creado_en.desc()).first()

    # Crear la alerta marcada como disparada por el pasajero (denuncia manual)
    alerta = AlertaDesvio(
        minibus_id=bus.id,
        chofer_id=bus.chofer_id,
        turno_id=turno.id if turno else None,
        latitud_desvio=lat,
        longitud_desvio=lon,
        distancia_metros=None,  # No aplica, es denuncia manual, no cálculo GPS automático
        disparada_por="denuncia_pasajero",
    )
    db.session.add(alerta)
    db.session.flush()

    # Notificar al chofer para que justifique
    try:
        notificar_desvio_chofer(
            chofer_id=bus.chofer_id,
            alerta_id=alerta.id,
            placa=bus.placa,
            distancia=0,
        )
        alerta.notificacion_enviada = True
        alerta.notificacion_enviada_en = datetime.utcnow()
    except Exception:
        pass

    db.session.commit()

    return ok({
        "alerta_id": alerta.id,
        "placa": bus.placa,
        "mensaje_chofer": "Se notificó al chofer para que justifique."
    }, "Denuncia registrada correctamente. Gracias por reportar.", 201)


# ─────────────────────────────────────────────────────────────
# ALERTAS
# ─────────────────────────────────────────────────────────────

@alertas_bp.route("/", methods=["GET"])
@jwt_required()
def listar_alertas():
    """
    Admin/autoridad: ve todas las alertas.
    Chofer: ve solo sus propias alertas.
    """
    user_id = _uuid.UUID(str(get_jwt_identity()))
    usuario = Usuario.query.get(user_id)

    estado = request.args.get("estado")
    placa = request.args.get("placa", "").strip().upper()
    limite = request.args.get("limite", 50, type=int)

    query = AlertaDesvio.query

    # El chofer solo ve las suyas
    if usuario.rol.nombre == "chofer":
        query = query.filter_by(chofer_id=user_id)
    # Admin/autoridad puede filtrar por chofer
    elif request.args.get("chofer_id"):
        query = query.filter_by(chofer_id=request.args.get("chofer_id"))

    if estado:
        query = query.filter_by(estado=estado)

    if placa:
        query = query.join(Minibus, AlertaDesvio.minibus_id == Minibus.id)\
            .filter(Minibus.placa.ilike(f"%{placa}%"))

    alertas = query.order_by(AlertaDesvio.generada_en.desc()).limit(limite).all()
    return ok([a.to_dict() for a in alertas])


@alertas_bp.route("/<int:alerta_id>", methods=["GET"])
@jwt_required()
def obtener_alerta(alerta_id):
    """Obtiene detalle de una alerta con su justificación."""
    alerta = AlertaDesvio.query.get(alerta_id)
    if not alerta:
        return error("Alerta no encontrada", 404)
    return ok(alerta.to_dict())


@alertas_bp.route("/pendientes/count", methods=["GET"])
@jwt_required()
def count_pendientes():
    """Cuenta alertas pendientes (para el badge del dashboard)."""
    user_id = _uuid.UUID(str(get_jwt_identity()))
    usuario = Usuario.query.get(user_id)

    if usuario.rol.nombre == "chofer":
        count = AlertaDesvio.query.filter_by(
            chofer_id=user_id, estado="pendiente"
        ).count()
    else:
        count = AlertaDesvio.query.filter_by(estado="pendiente").count()

    return ok({"pendientes": count})


# ─────────────────────────────────────────────────────────────
# JUSTIFICACIONES (chofer las envía)
# ─────────────────────────────────────────────────────────────

@alertas_bp.route("/<int:alerta_id>/justificar-admin", methods=["POST"])
@jwt_required()
@solo_admin
def justificar_como_admin(alerta_id):
    """
    El admin registra una justificación EN NOMBRE del chofer, para casos
    donde el chofer no puede hacerlo desde la app (falla mecánica grave,
    accidente, sin señal, etc). Queda automáticamente aceptada porque
    la está creando el propio admin.
    Body: { motivo, descripcion }
    """
    admin_id = _uuid.UUID(str(get_jwt_identity()))
    alerta = AlertaDesvio.query.get(alerta_id)

    if not alerta:
        return error("Alerta no encontrada", 404)

    if alerta.justificacion:
        return error("Esta alerta ya tiene una justificación registrada", 400)

    data = request.get_json()
    motivo = data.get("motivo", "").strip()
    descripcion = data.get("descripcion", "").strip()

    motivos_validos = ["gasolina", "emergencia", "desvio_trafico",
                       "accidente", "falla_mecanica", "orden_superior", "otro"]
    if motivo not in motivos_validos:
        return error(f"Motivo inválido. Opciones: {', '.join(motivos_validos)}", 400)

    justificacion = Justificacion(
        alerta_id=alerta_id,
        chofer_id=alerta.chofer_id,
        motivo=motivo,
        descripcion=descripcion,
        estado="aceptada",
        revisado_por=admin_id,
        comentario_admin="Registrado directamente por el admin.",
        revisada_en=datetime.utcnow(),
    )
    db.session.add(justificacion)
    alerta.estado = "justificada"
    db.session.commit()

    # Recalcular calificación del chofer afectado
    try:
        periodo = alerta.generada_en.strftime("%Y-%m") if alerta.generada_en else None
        calcular_calificacion_chofer(str(alerta.chofer_id), periodo)
    except Exception:
        pass

    return ok(justificacion.to_dict(), "Justificación registrada y aceptada", 201)


@alertas_bp.route("/<int:alerta_id>/justificar", methods=["POST"])
@jwt_required()
@solo_chofer
def enviar_justificacion(alerta_id):
    """
    El chofer envía una justificación para una alerta de desvío.
    Body: { motivo, descripcion }
    motivos válidos: gasolina, emergencia, desvio_trafico, accidente, falla_mecanica, orden_superior, otro
    """
    user_id = _uuid.UUID(str(get_jwt_identity()))
    alerta = AlertaDesvio.query.get(alerta_id)

    if not alerta:
        return error("Alerta no encontrada", 404)

    if str(alerta.chofer_id) != str(user_id):
        return error("Esta alerta no te pertenece", 403)

    if alerta.estado != "pendiente":
        return error("Esta alerta ya fue procesada", 400)

    if alerta.plazo_vencido:
        return error("El plazo de 24 horas para justificar venció", 400)

    # Verificar que no haya ya una justificación
    if alerta.justificacion:
        return error("Ya enviaste una justificación para esta alerta", 400)

    data = request.get_json()
    motivo = data.get("motivo", "").strip()
    descripcion = data.get("descripcion", "").strip()

    motivos_validos = ["gasolina", "emergencia", "desvio_trafico",
                       "accidente", "falla_mecanica", "orden_superior", "otro"]
    if motivo not in motivos_validos:
        return error(f"Motivo inválido. Opciones: {', '.join(motivos_validos)}", 400)

    justificacion = Justificacion(
        alerta_id=alerta_id,
        chofer_id=user_id,
        motivo=motivo,
        descripcion=descripcion,
    )
    db.session.add(justificacion)

    # Actualizar estado de la alerta
    alerta.estado = "justificada"
    db.session.commit()

    return ok(justificacion.to_dict(), "Justificación enviada correctamente. Espera la revisión del admin.", 201)


# ─────────────────────────────────────────────────────────────
# REVISIÓN DE JUSTIFICACIONES (admin las aprueba/rechaza)
# ─────────────────────────────────────────────────────────────

@alertas_bp.route("/justificaciones/pendientes", methods=["GET"])
@jwt_required()
@solo_admin
def justificaciones_pendientes():
    """Lista todas las justificaciones que el admin debe revisar."""
    justificaciones = Justificacion.query.filter_by(estado="pendiente")\
        .order_by(Justificacion.enviada_en.asc()).all()
    return ok([j.to_dict() for j in justificaciones])


@alertas_bp.route("/justificaciones/<int:justif_id>/revisar", methods=["PUT"])
@jwt_required()
@solo_admin
def revisar_justificacion(justif_id):
    """
    El admin acepta o rechaza una justificación.
    Body: { decision: 'aceptada' | 'rechazada', comentario }
    """
    admin_id = get_jwt_identity()
    justificacion = Justificacion.query.get(justif_id)

    if not justificacion:
        return error("Justificación no encontrada", 404)

    if justificacion.estado != "pendiente":
        return error("Esta justificación ya fue revisada", 400)

    data = request.get_json()
    decision = data.get("decision", "").strip()
    comentario = data.get("comentario", "").strip()

    if decision not in ["aceptada", "rechazada"]:
        return error("decision debe ser 'aceptada' o 'rechazada'", 400)

    justificacion.estado = decision
    justificacion.revisado_por = admin_id
    justificacion.comentario_admin = comentario
    justificacion.revisada_en = datetime.utcnow()

    # Actualizar estado de la alerta
    alerta = justificacion.alerta
    if decision == "aceptada":
        alerta.estado = "justificada"
    else:
        alerta.estado = "rechazada"

    db.session.commit()

    # Notificar al chofer
    try:
        notificar_justificacion(
            chofer_id=str(justificacion.chofer_id),
            estado=decision,
            comentario=comentario,
        )
    except Exception:
        pass

    # Recalcular calificación del chofer afectado
    try:
        periodo = alerta.generada_en.strftime("%Y-%m") if alerta.generada_en else None
        calcular_calificacion_chofer(str(justificacion.chofer_id), periodo)
    except Exception:
        pass

    return ok(justificacion.to_dict(), f"Justificación {decision} correctamente")


@alertas_bp.route("/vencidas/procesar", methods=["POST"])
@jwt_required()
@solo_admin
def procesar_vencidas():
    """
    Marca como 'sin_respuesta' las alertas cuyo plazo venció y no fueron justificadas.
    Puede llamarse manualmente o por un cron job.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import and_

    ahora = datetime.utcnow()
    alertas_vencidas = AlertaDesvio.query.filter(
        AlertaDesvio.estado == "pendiente",
        AlertaDesvio.generada_en <= ahora - timedelta(hours=24)
    ).all()

    count = 0
    for alerta in alertas_vencidas:
        if not alerta.justificacion:
            alerta.estado = "sin_respuesta"
            count += 1
            # Recalcular calificación
            try:
                periodo = alerta.generada_en.strftime("%Y-%m")
                calcular_calificacion_chofer(str(alerta.chofer_id), periodo)
            except Exception:
                pass

    db.session.commit()
    return ok({"procesadas": count}, f"{count} alertas marcadas como sin respuesta")
