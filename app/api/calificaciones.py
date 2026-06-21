from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Calificacion, Usuario, Rol, AlertaDesvio, RegistroParada, Minibus
from app.utils import ok, error, solo_admin, admin_o_autoridad
from app.services.calificaciones import calcular_calificacion_chofer

calificaciones_bp = Blueprint("calificaciones", __name__, url_prefix="/api/calificaciones")


@calificaciones_bp.route("/", methods=["GET"])
@jwt_required()
@admin_o_autoridad
def listar_calificaciones():
    """Lista calificaciones con filtro por período, chofer y/o placa."""
    periodo = request.args.get("periodo", datetime.utcnow().strftime("%Y-%m"))
    chofer_id = request.args.get("chofer_id")
    placa = request.args.get("placa", "").strip().upper()

    query = Calificacion.query.filter_by(periodo=periodo)
    if chofer_id:
        query = query.filter_by(chofer_id=chofer_id)

    if placa:
        from app.models import Minibus
        chofer_ids_con_placa = [
            row.chofer_id for row in
            Minibus.query.filter(Minibus.placa.ilike(f"%{placa}%")).all()
            if row.chofer_id
        ]
        if not chofer_ids_con_placa:
            return ok([])
        query = query.filter(Calificacion.chofer_id.in_(chofer_ids_con_placa))

    cals = query.order_by(Calificacion.calificacion.desc()).all()
    return ok([c.to_dict() for c in cals])


@calificaciones_bp.route("/chofer/<string:chofer_id>", methods=["GET"])
@jwt_required()
def calificacion_chofer(chofer_id):
    """Calificación de un chofer específico. El chofer puede ver la suya."""
    import uuid as _uuid; user_id = _uuid.UUID(str(get_jwt_identity()))
    usuario = Usuario.query.get(user_id)

    # El chofer solo puede ver la suya
    if usuario.rol.nombre == "chofer" and str(user_id) != str(chofer_id):
        return error("Acceso denegado", 403)

    periodo = request.args.get("periodo", datetime.utcnow().strftime("%Y-%m"))
    cal = Calificacion.query.filter_by(chofer_id=chofer_id, periodo=periodo).first()

    if not cal:
        return ok(None, "Sin calificación para este período")

    return ok(cal.to_dict())


@calificaciones_bp.route("/calcular/<string:chofer_id>", methods=["POST"])
@jwt_required()
@solo_admin
def calcular_manualmente(chofer_id):
    """El admin puede forzar el recálculo de la calificación de un chofer."""
    periodo = request.json.get("periodo") if request.json else None
    cal = calcular_calificacion_chofer(chofer_id, periodo)
    return ok(cal.to_dict(), "Calificación recalculada")


@calificaciones_bp.route("/calcular-todos", methods=["POST"])
@jwt_required()
@solo_admin
def calcular_todos():
    """Recalcula la calificación de todos los choferes activos para el período dado."""
    data = request.get_json() or {}
    periodo = data.get("periodo", datetime.utcnow().strftime("%Y-%m"))

    choferes = Usuario.query.join(Rol).filter(
        Rol.nombre == "chofer", Usuario.activo == True
    ).all()

    resultados = []
    for chofer in choferes:
        try:
            cal = calcular_calificacion_chofer(str(chofer.id), periodo)
            resultados.append(cal.to_dict())
        except Exception as e:
            resultados.append({"chofer_id": str(chofer.id), "error": str(e)})

    return ok(resultados, f"Calificaciones calculadas para {len(resultados)} choferes")


# ─────────────────────────────────────────────────────────────
# DASHBOARD (admin / autoridad)
# ─────────────────────────────────────────────────────────────

@calificaciones_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@admin_o_autoridad
def dashboard():
    """
    Datos del dashboard principal: resumen del día actual.
    """
    hoy = datetime.utcnow().date()
    mes_actual = datetime.utcnow().strftime("%Y-%m")

    # Buses activos en ruta
    buses_activos = Minibus.query.filter_by(activo=True).count()

    # Registros de hoy
    registros_hoy = RegistroParada.query.filter(
        db.func.date(RegistroParada.registrado_en) == hoy
    ).count()

    registros_ok_hoy = RegistroParada.query.filter(
        db.func.date(RegistroParada.registrado_en) == hoy,
        RegistroParada.en_ruta == True
    ).count()

    # Alertas de hoy
    alertas_hoy = AlertaDesvio.query.filter(
        db.func.date(AlertaDesvio.generada_en) == hoy
    ).count()

    alertas_pendientes = AlertaDesvio.query.filter_by(estado="pendiente").count()

    # Top 5 choferes del mes
    top_choferes = Calificacion.query.filter_by(periodo=mes_actual)\
        .order_by(Calificacion.calificacion.desc()).limit(5).all()

    # Choferes con peor desempeño
    peor_desempeno = Calificacion.query.filter_by(periodo=mes_actual)\
        .order_by(Calificacion.calificacion.asc()).limit(5).all()

    cumplimiento_hoy = round(
        (registros_ok_hoy / registros_hoy * 100) if registros_hoy > 0 else 0, 1
    )

    return ok({
        "resumen_hoy": {
            "fecha": hoy.isoformat(),
            "buses_activos": buses_activos,
            "registros_total": registros_hoy,
            "registros_ok": registros_ok_hoy,
            "cumplimiento_pct": cumplimiento_hoy,
            "alertas_generadas": alertas_hoy,
            "alertas_pendientes": alertas_pendientes,
        },
        "top_choferes_mes": [c.to_dict() for c in top_choferes],
        "peor_desempeno_mes": [c.to_dict() for c in peor_desempeno],
        "periodo": mes_actual,
    })
