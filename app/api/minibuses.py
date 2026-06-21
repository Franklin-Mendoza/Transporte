from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Minibus, Ruta, Usuario, Rol
from app.utils import ok, error, solo_admin, admin_o_autoridad
from app.services import generar_qr_minibus

minibuses_bp = Blueprint("minibuses", __name__, url_prefix="/api/minibuses")


@minibuses_bp.route("/", methods=["GET"])
@jwt_required()
@admin_o_autoridad
def listar_minibuses():
    """Lista todos los minibuses con chofer y ruta asignados."""
    solo_activos = request.args.get("activo", "true").lower() == "true"
    ruta_id = request.args.get("ruta_id", type=int)

    query = Minibus.query
    if solo_activos:
        query = query.filter_by(activo=True)
    if ruta_id:
        query = query.filter_by(ruta_id=ruta_id)

    buses = query.all()
    return ok([b.to_dict(include_chofer=True, include_ruta=True) for b in buses])


@minibuses_bp.route("/<int:minibus_id>", methods=["GET"])
@jwt_required()
@admin_o_autoridad
def obtener_minibus(minibus_id):
    bus = Minibus.query.get(minibus_id)
    if not bus:
        return error("Minibús no encontrado", 404)
    return ok(bus.to_dict(include_chofer=True, include_ruta=True))


@minibuses_bp.route("/", methods=["POST"])
@jwt_required()
@solo_admin
def crear_minibus():
    """Crea un minibús y genera su código QR automáticamente."""
    data = request.get_json()

    placa = data.get("placa", "").strip().upper()
    ruta_id = data.get("ruta_id")
    chofer_id = data.get("chofer_id")
    modelo = data.get("modelo", "").strip()
    color = data.get("color", "").strip()
    capacidad = data.get("capacidad", 12)

    if not placa:
        return error("La placa es obligatoria", 400)

    if Minibus.query.filter_by(placa=placa).first():
        return error(f"Ya existe un minibús con la placa {placa}", 409)

    # Verificar ruta
    if ruta_id and not Ruta.query.get(ruta_id):
        return error("Ruta no encontrada", 404)

    # Verificar chofer
    if chofer_id:
        chofer = Usuario.query.get(chofer_id)
        if not chofer or chofer.rol.nombre != "chofer":
            return error("Chofer no válido", 400)

        # Un chofer solo puede estar asignado a UN minibús a la vez
        otros_buses = Minibus.query.filter_by(chofer_id=chofer_id).all()
        for otro in otros_buses:
            otro.chofer_id = None

    # Generar código QR único
    codigo_qr = f"BUS-{placa}-SIG2026"

    bus = Minibus(
        placa=placa,
        codigo_qr=codigo_qr,
        ruta_id=ruta_id,
        chofer_id=chofer_id,
        modelo=modelo,
        color=color,
        capacidad=capacidad,
    )
    db.session.add(bus)
    db.session.commit()

    # Generar imagen QR
    try:
        ruta_obj = Ruta.query.get(ruta_id) if ruta_id else None
        _, url_qr = generar_qr_minibus(
            codigo_qr=codigo_qr,
            placa=placa,
            ruta_nombre=ruta_obj.nombre if ruta_obj else "",
        )
    except Exception as e:
        url_qr = None

    data_resp = bus.to_dict(include_chofer=True, include_ruta=True)
    data_resp["qr_url"] = url_qr
    return ok(data_resp, "Minibús creado correctamente", 201)


@minibuses_bp.route("/<int:minibus_id>", methods=["PUT"])
@jwt_required()
@solo_admin
def actualizar_minibus(minibus_id):
    """Actualiza datos del minibús (ruta, chofer, info)."""
    bus = Minibus.query.get(minibus_id)
    if not bus:
        return error("Minibús no encontrado", 404)

    data = request.get_json()

    if "placa" in data:
        nueva_placa = data["placa"].strip().upper()
        if nueva_placa != bus.placa:
            if Minibus.query.filter_by(placa=nueva_placa).first():
                return error(f"Ya existe un minibús con la placa {nueva_placa}", 409)
            bus.placa = nueva_placa

    if "ruta_id" in data:
        if data["ruta_id"] and not Ruta.query.get(data["ruta_id"]):
            return error("Ruta no encontrada", 404)
        bus.ruta_id = data["ruta_id"]

    if "chofer_id" in data:
        if data["chofer_id"]:
            chofer = Usuario.query.get(data["chofer_id"])
            if not chofer or chofer.rol.nombre != "chofer":
                return error("Chofer no válido", 400)

            # Un chofer solo puede estar asignado a UN minibús a la vez.
            # Si ya manejaba otro bus, lo liberamos automáticamente para
            # evitar inconsistencias en turnos, calificaciones y reportes.
            otros_buses = Minibus.query.filter(
                Minibus.chofer_id == data["chofer_id"],
                Minibus.id != bus.id
            ).all()
            for otro in otros_buses:
                otro.chofer_id = None

        bus.chofer_id = data["chofer_id"]

    if "modelo" in data:
        bus.modelo = data["modelo"].strip()
    if "color" in data:
        bus.color = data["color"].strip()
    if "capacidad" in data:
        bus.capacidad = int(data["capacidad"])
    if "activo" in data:
        bus.activo = bool(data["activo"])

    db.session.commit()
    return ok(bus.to_dict(include_chofer=True, include_ruta=True), "Minibús actualizado")


@minibuses_bp.route("/<int:minibus_id>", methods=["DELETE"])
@jwt_required()
@solo_admin
def desactivar_minibus(minibus_id):
    bus = Minibus.query.get(minibus_id)
    if not bus:
        return error("Minibús no encontrado", 404)
    bus.activo = False
    db.session.commit()
    return ok(mensaje=f"Minibús {bus.placa} desactivado")


@minibuses_bp.route("/<int:minibus_id>/regenerar-qr", methods=["POST"])
@jwt_required()
@solo_admin
def regenerar_qr(minibus_id):
    """Regenera la imagen QR de un minibús."""
    bus = Minibus.query.get(minibus_id)
    if not bus:
        return error("Minibús no encontrado", 404)

    try:
        ruta_obj = bus.ruta
        _, url_qr = generar_qr_minibus(
            codigo_qr=bus.codigo_qr,
            placa=bus.placa,
            ruta_nombre=ruta_obj.nombre if ruta_obj else "",
        )
        return ok({"qr_url": url_qr}, "QR regenerado correctamente")
    except Exception as e:
        return error(f"Error generando QR: {str(e)}", 500)


@minibuses_bp.route("/por-qr/<string:codigo_qr>", methods=["GET"])
def info_por_qr(codigo_qr):
    """
    Endpoint PÚBLICO: el pasajero escanea el QR y obtiene la info del minibús.
    No requiere JWT.
    """
    bus = Minibus.query.filter_by(codigo_qr=codigo_qr, activo=True).first()
    if not bus:
        return error("Minibús no encontrado o inactivo", 404)

    # Obtener el último registro de parada
    from app.models import RegistroParada
    ultimo_reg = RegistroParada.query.filter_by(minibus_id=bus.id)\
        .order_by(RegistroParada.registrado_en.desc()).first()

    data = bus.to_dict(include_chofer=False, include_ruta=True)
    if ultimo_reg:
        data["ultima_parada"] = ultimo_reg.parada.nombre if ultimo_reg.parada else None
        data["ultima_parada_hora"] = ultimo_reg.registrado_en.strftime("%H:%M") if ultimo_reg.registrado_en else None
        data["en_ruta"] = ultimo_reg.en_ruta
    else:
        data["ultima_parada"] = None
        data["ultima_parada_hora"] = None
        data["en_ruta"] = None

    return ok(data)
