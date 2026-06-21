from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import (
    RegistroParada, EscaneosPasajero, AlertaDesvio,
    Minibus, Parada, Turno, Notificacion
)
from app.utils import ok, error, punto_en_ruta, punto_cerca_de_parada
from app.services import notificar_desvio_chofer, notificar_parada_ok
from flask import current_app

registros_bp = Blueprint("registros", __name__, url_prefix="/api/registros")


# ─────────────────────────────────────────────────────────────
# REGISTRO DE CÁMARA EN PARADA
# ─────────────────────────────────────────────────────────────

@registros_bp.route("/camara", methods=["POST"])
def registro_camara():
    """
    La cámara en la parada detecta el QR del minibús y llama este endpoint.
    Body: { codigo_qr, parada_id, latitud_camara, longitud_camara }
    No requiere JWT (la cámara es un dispositivo confiable en la red local).
    """
    data = request.get_json()
    codigo_qr = data.get("codigo_qr")
    parada_id = data.get("parada_id")
    lat = data.get("latitud_camara")
    lon = data.get("longitud_camara")

    if not codigo_qr or not parada_id:
        return error("codigo_qr y parada_id son obligatorios", 400)

    # Buscar minibús
    bus = Minibus.query.filter_by(codigo_qr=codigo_qr, activo=True).first()
    if not bus:
        return error("Minibús no encontrado con ese QR", 404)

    # Buscar parada
    parada = Parada.query.get(parada_id)
    if not parada:
        return error("Parada no encontrada", 404)

    # Validar que la parada pertenece a la ruta del minibús
    en_ruta_correcta = parada.ruta_id == bus.ruta_id

    # Calcular distancia real si hay coordenadas
    distancia = None
    if lat and lon:
        from app.utils import haversine
        distancia = haversine(lat, lon, parada.latitud, parada.longitud)

    # Buscar turno activo del chofer en ese minibús
    turno = Turno.query.filter_by(
        minibus_id=bus.id, estado="activo"
    ).order_by(Turno.creado_en.desc()).first()

    if not turno and bus.chofer_id and bus.ruta_id:
        # Crear turno automáticamente si no existe
        turno = Turno(
            minibus_id=bus.id,
            chofer_id=bus.chofer_id,
            ruta_id=bus.ruta_id,
            hora_inicio=datetime.utcnow(),
        )
        db.session.add(turno)
        db.session.flush()

    # Crear registro
    registro = RegistroParada(
        turno_id=turno.id if turno else None,
        minibus_id=bus.id,
        parada_id=parada.id,
        chofer_id=bus.chofer_id,
        latitud_real=lat,
        longitud_real=lon,
        distancia_metros=distancia,
        en_ruta=en_ruta_correcta,
        metodo_registro="camara",
    )
    db.session.add(registro)

    # Notificar al chofer que llegó a la parada
    if bus.chofer_id and en_ruta_correcta:
        hora_actual = datetime.utcnow().strftime("%H:%M")
        try:
            notificar_parada_ok(bus.chofer_id, parada.nombre, hora_actual)
        except Exception:
            pass

    # Si no está en ruta correcta, generar alerta
    if not en_ruta_correcta:
        _generar_alerta(bus, turno, lat, lon, distancia, "camara")

    db.session.commit()
    return ok({
        "minibus": bus.placa,
        "parada": parada.nombre,
        "en_ruta": en_ruta_correcta,
        "distancia_metros": round(distancia, 1) if distancia else None,
    }, "Registro guardado correctamente")


# ─────────────────────────────────────────────────────────────
# ESCANEO DEL PASAJERO (web o app Flutter)
# ─────────────────────────────────────────────────────────────

@registros_bp.route("/pasajero", methods=["POST"])
def escaneo_pasajero():
    """
    El pasajero escanea el QR del minibús y envía su ubicación GPS.
    Body: { codigo_qr, latitud_pasajero, longitud_pasajero, plataforma }
    No requiere JWT (endpoint público).
    """
    data = request.get_json()
    codigo_qr = data.get("codigo_qr")
    lat_pasajero = data.get("latitud_pasajero")
    lon_pasajero = data.get("longitud_pasajero")
    plataforma = data.get("plataforma", "web")

    if not codigo_qr:
        return error("codigo_qr es obligatorio", 400)

    # Buscar el minibús
    bus = Minibus.query.filter_by(codigo_qr=codigo_qr, activo=True).first()
    if not bus:
        return error("Minibús no encontrado", 404)

    # Obtener paradas de la ruta del bus
    paradas = bus.ruta.paradas if bus.ruta else []

    # Verificar si el bus está en su ruta usando las coordenadas del pasajero
    # (El pasajero está cerca del bus → su GPS aproxima la posición del bus)
    radio = current_app.config.get("RADIO_TOLERANCIA_METROS", 100)
    en_ruta = False
    parada_cercana = None
    distancia_min = None

    if lat_pasajero and lon_pasajero and paradas:
        en_ruta, parada_cercana, distancia_min = punto_en_ruta(
            lat_pasajero, lon_pasajero, paradas, radio
        )
    elif not lat_pasajero:
        # Sin GPS del pasajero, solo registramos el escaneo
        en_ruta = None

    # Guardar escaneo
    escaneo = EscaneosPasajero(
        minibus_id=bus.id,
        latitud_pasajero=lat_pasajero,
        longitud_pasajero=lon_pasajero,
        parada_actual_id=parada_cercana.id if parada_cercana else None,
        minibus_en_ruta=en_ruta,
        distancia_ruta_metros=distancia_min,
        plataforma=plataforma,
        ip_origen=request.remote_addr,
    )
    db.session.add(escaneo)

    # Si el bus está fuera de ruta, generar alerta
    if en_ruta is False and distancia_min and distancia_min > radio:
        turno = Turno.query.filter_by(
            minibus_id=bus.id, estado="activo"
        ).order_by(Turno.creado_en.desc()).first()
        _generar_alerta(bus, turno, lat_pasajero, lon_pasajero, distancia_min, "pasajero")

    db.session.commit()

    # Obtener último registro de parada del bus
    ultimo_reg = RegistroParada.query.filter_by(minibus_id=bus.id)\
        .order_by(RegistroParada.registrado_en.desc()).first()

    return ok({
        "bus": {
            "placa": bus.placa,
            "ruta": bus.ruta.nombre if bus.ruta else None,
            "en_ruta": en_ruta,
            "ultima_parada": ultimo_reg.parada.nombre if ultimo_reg and ultimo_reg.parada else None,
            "ultima_actualizacion": ultimo_reg.registrado_en.strftime("%H:%M") if ultimo_reg else None,
        },
        "posicion_pasajero": {
            "latitud": lat_pasajero,
            "longitud": lon_pasajero,
            "parada_cercana": parada_cercana.nombre if parada_cercana else None,
            "distancia_metros": round(distancia_min, 1) if distancia_min else None,
        }
    })


# ─────────────────────────────────────────────────────────────
# CONSULTAS DE REGISTROS (admin / autoridad)
# ─────────────────────────────────────────────────────────────

@registros_bp.route("/", methods=["GET"])
@jwt_required()
def listar_registros():
    """Lista registros con filtros: minibus_id, chofer_id, fecha, en_ruta."""
    minibus_id = request.args.get("minibus_id", type=int)
    chofer_id = request.args.get("chofer_id")
    en_ruta = request.args.get("en_ruta")
    limite = request.args.get("limite", 50, type=int)

    query = RegistroParada.query
    if minibus_id:
        query = query.filter_by(minibus_id=minibus_id)
    if chofer_id:
        query = query.filter_by(chofer_id=chofer_id)
    if en_ruta is not None:
        query = query.filter_by(en_ruta=en_ruta.lower() == "true")

    registros = query.order_by(RegistroParada.registrado_en.desc()).limit(limite).all()
    return ok([r.to_dict() for r in registros])


@registros_bp.route("/mapa", methods=["GET"])
@jwt_required()
def estado_mapa():
    """
    Estado en tiempo real de todos los minibuses activos.
    Para el mapa del panel web (admin / autoridad).
    """
    from app.models import Minibus
    buses = Minibus.query.filter_by(activo=True).all()
    resultado = []

    for bus in buses:
        ultimo = RegistroParada.query.filter_by(minibus_id=bus.id)\
            .order_by(RegistroParada.registrado_en.desc()).first()

        # Buscar la parada anterior a la última (para mostrar de dónde viene)
        anterior = None
        if ultimo:
            anterior = RegistroParada.query.filter(
                RegistroParada.minibus_id == bus.id,
                RegistroParada.id != ultimo.id
            ).order_by(RegistroParada.registrado_en.desc()).first()

        resultado.append({
            "minibus_id": bus.id,
            "placa": bus.placa,
            "ruta": bus.ruta.nombre if bus.ruta else None,
            "ruta_id": bus.ruta_id,
            "chofer": f"{bus.chofer.nombre} {bus.chofer.apellido}" if bus.chofer else None,
            "latitud": float(ultimo.latitud_real) if ultimo and ultimo.latitud_real else None,
            "longitud": float(ultimo.longitud_real) if ultimo and ultimo.longitud_real else None,
            "en_ruta": ultimo.en_ruta if ultimo else None,
            "parada_anterior": anterior.parada.nombre if anterior and anterior.parada else None,
            "ultima_parada": ultimo.parada.nombre if ultimo and ultimo.parada else None,
            "ultima_actualizacion": ultimo.registrado_en.isoformat() if ultimo else None,
        })

    return ok(resultado)


# ─────────────────────────────────────────────────────────────
# FUNCIÓN INTERNA: generar alerta de desvío
# ─────────────────────────────────────────────────────────────

def _generar_alerta(bus, turno, lat, lon, distancia, disparada_por):
    """Crea una alerta de desvío y envía notificación push al chofer."""
    # Evitar alertas duplicadas recientes (en los últimos 10 minutos)
    from datetime import timedelta
    alerta_reciente = AlertaDesvio.query.filter(
        AlertaDesvio.minibus_id == bus.id,
        AlertaDesvio.estado == "pendiente",
        AlertaDesvio.generada_en >= datetime.utcnow() - timedelta(minutes=10)
    ).first()

    if alerta_reciente:
        return  # No duplicar alertas

    alerta = AlertaDesvio(
        minibus_id=bus.id,
        chofer_id=bus.chofer_id,
        turno_id=turno.id if turno else None,
        latitud_desvio=lat,
        longitud_desvio=lon,
        distancia_metros=distancia,
        disparada_por=disparada_por,
    )
    db.session.add(alerta)
    db.session.flush()

    # Enviar push al chofer
    if bus.chofer_id:
        try:
            notificar_desvio_chofer(
                chofer_id=bus.chofer_id,
                alerta_id=alerta.id,
                placa=bus.placa,
                distancia=distancia or 0,
            )
            alerta.notificacion_enviada = True
            alerta.notificacion_enviada_en = datetime.utcnow()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# HISTORIAL DE ESCANEOS DEL PASAJERO (admin / autoridad)
# ─────────────────────────────────────────────────────────────

@registros_bp.route("/escaneos", methods=["GET"])
@jwt_required()
def listar_escaneos_pasajero():
    """
    Historial de escaneos de QR hechos por pasajeros: fecha, hora,
    latitud, longitud y minibús escaneado. Sirve para auditar dónde
    y cuándo se escaneó cada minibús.
    """
    from app.models import EscaneosPasajero, Minibus as MinibusModel

    placa = request.args.get("placa", "").strip().upper()
    limite = request.args.get("limite", 100, type=int)

    query = EscaneosPasajero.query
    if placa:
        query = query.join(MinibusModel, EscaneosPasajero.minibus_id == MinibusModel.id)\
            .filter(MinibusModel.placa.ilike(f"%{placa}%"))

    escaneos = query.order_by(EscaneosPasajero.escaneado_en.desc()).limit(limite).all()
    return ok([e.to_dict() for e in escaneos])


@registros_bp.route("/escaneos/mapa", methods=["GET"])
@jwt_required()
def escaneos_para_mapa():
    """
    Puntos de escaneo del pasajero con coordenadas, para mostrar
    en el mapa en tiempo real junto a la posición de los buses.
    Solo trae escaneos de las últimas 24 horas para no saturar el mapa.
    """
    from app.models import EscaneosPasajero
    from datetime import timedelta

    desde = datetime.utcnow() - timedelta(hours=24)
    escaneos = EscaneosPasajero.query.filter(
        EscaneosPasajero.escaneado_en >= desde,
        EscaneosPasajero.latitud_pasajero.isnot(None),
        EscaneosPasajero.longitud_pasajero.isnot(None),
    ).order_by(EscaneosPasajero.escaneado_en.desc()).limit(200).all()

    return ok([e.to_dict() for e in escaneos])
