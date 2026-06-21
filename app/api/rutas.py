from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Ruta, Parada
from app.utils import ok, error, solo_admin, admin_o_autoridad

rutas_bp = Blueprint("rutas", __name__, url_prefix="/api/rutas")


@rutas_bp.route("/", methods=["GET"])
@jwt_required()
def listar_rutas():
    """Lista todas las rutas. Disponible para todos los roles."""
    solo_activas = request.args.get("activa", "true").lower() == "true"
    query = Ruta.query
    if solo_activas:
        query = query.filter_by(activa=True)
    rutas = query.order_by(Ruta.codigo).all()
    return ok([r.to_dict() for r in rutas])


@rutas_bp.route("/<int:ruta_id>", methods=["GET"])
@jwt_required()
def obtener_ruta(ruta_id):
    """Obtiene una ruta con todas sus paradas."""
    ruta = Ruta.query.get(ruta_id)
    if not ruta:
        return error("Ruta no encontrada", 404)
    return ok(ruta.to_dict(include_paradas=True))


@rutas_bp.route("/", methods=["POST"])
@jwt_required()
@solo_admin
def crear_ruta():
    """Crea una nueva ruta con sus paradas (solo admin)."""
    data = request.get_json()
    admin_id = get_jwt_identity()

    codigo = data.get("codigo", "").strip().upper()
    nombre = data.get("nombre", "").strip()
    descripcion = data.get("descripcion", "").strip()
    paradas_data = data.get("paradas", [])

    if not codigo or not nombre:
        return error("codigo y nombre son obligatorios", 400)

    if Ruta.query.filter_by(codigo=codigo).first():
        return error(f"Ya existe una ruta con el código {codigo}", 409)

    ruta = Ruta(
        codigo=codigo,
        nombre=nombre,
        descripcion=descripcion,
        creado_por=admin_id,
    )
    db.session.add(ruta)
    db.session.flush()  # Para tener el ID de la ruta

    # Crear paradas
    for i, p in enumerate(paradas_data, 1):
        if not p.get("nombre") or p.get("latitud") is None or p.get("longitud") is None:
            db.session.rollback()
            return error(f"Parada {i}: nombre, latitud y longitud son obligatorios", 400)

        parada = Parada(
            ruta_id=ruta.id,
            nombre=p["nombre"].strip(),
            orden=p.get("orden", i),
            latitud=p["latitud"],
            longitud=p["longitud"],
            radio_metros=p.get("radio_metros", 50),
        )
        db.session.add(parada)

    db.session.commit()
    return ok(ruta.to_dict(include_paradas=True), "Ruta creada correctamente", 201)


@rutas_bp.route("/<int:ruta_id>", methods=["PUT"])
@jwt_required()
@solo_admin
def actualizar_ruta(ruta_id):
    """Actualiza datos de una ruta (sin modificar paradas)."""
    ruta = Ruta.query.get(ruta_id)
    if not ruta:
        return error("Ruta no encontrada", 404)

    data = request.get_json()
    if "nombre" in data:
        ruta.nombre = data["nombre"].strip()
    if "descripcion" in data:
        ruta.descripcion = data["descripcion"].strip()
    if "activa" in data:
        ruta.activa = bool(data["activa"])

    db.session.commit()
    return ok(ruta.to_dict(), "Ruta actualizada")


@rutas_bp.route("/<int:ruta_id>", methods=["DELETE"])
@jwt_required()
@solo_admin
def desactivar_ruta(ruta_id):
    """Desactiva una ruta (soft delete)."""
    ruta = Ruta.query.get(ruta_id)
    if not ruta:
        return error("Ruta no encontrada", 404)
    ruta.activa = False
    db.session.commit()
    return ok(mensaje=f"Ruta {ruta.codigo} desactivada")


# ── Paradas ──────────────────────────────────────

@rutas_bp.route("/<int:ruta_id>/paradas", methods=["GET"])
@jwt_required()
def listar_paradas(ruta_id):
    """Lista las paradas de una ruta en orden."""
    ruta = Ruta.query.get(ruta_id)
    if not ruta:
        return error("Ruta no encontrada", 404)
    return ok([p.to_dict() for p in ruta.paradas])


@rutas_bp.route("/<int:ruta_id>/paradas", methods=["POST"])
@jwt_required()
@solo_admin
def agregar_parada(ruta_id):
    """Agrega una parada a una ruta existente."""
    ruta = Ruta.query.get(ruta_id)
    if not ruta:
        return error("Ruta no encontrada", 404)

    data = request.get_json()
    nombre = data.get("nombre", "").strip()
    latitud = data.get("latitud")
    longitud = data.get("longitud")
    radio = data.get("radio_metros", 50)

    if not nombre or latitud is None or longitud is None:
        return error("nombre, latitud y longitud son obligatorios", 400)

    # Orden = siguiente al último
    ultimo_orden = db.session.query(db.func.max(Parada.orden))\
        .filter_by(ruta_id=ruta_id).scalar() or 0

    parada = Parada(
        ruta_id=ruta_id,
        nombre=nombre,
        orden=data.get("orden", ultimo_orden + 1),
        latitud=latitud,
        longitud=longitud,
        radio_metros=radio,
    )
    db.session.add(parada)
    db.session.commit()
    return ok(parada.to_dict(), "Parada agregada", 201)


@rutas_bp.route("/<int:ruta_id>/paradas/<int:parada_id>", methods=["PUT"])
@jwt_required()
@solo_admin
def editar_parada(ruta_id, parada_id):
    """
    Edita una parada existente: nombre, latitud, longitud, radio.
    Útil cuando la cámara física se reubica un poco y hay que ajustar
    las coordenadas exactas donde está instalada.
    """
    parada = Parada.query.filter_by(id=parada_id, ruta_id=ruta_id).first()
    if not parada:
        return error("Parada no encontrada", 404)

    data = request.get_json()

    if "nombre" in data:
        parada.nombre = data["nombre"].strip()
    if "latitud" in data:
        parada.latitud = data["latitud"]
    if "longitud" in data:
        parada.longitud = data["longitud"]
    if "radio_metros" in data:
        parada.radio_metros = data["radio_metros"]
    if "orden" in data:
        parada.orden = data["orden"]
    if "activa" in data:
        parada.activa = bool(data["activa"])

    db.session.commit()
    return ok(parada.to_dict(), "Parada actualizada correctamente")


@rutas_bp.route("/<int:ruta_id>/paradas/<int:parada_id>", methods=["DELETE"])
@jwt_required()
@solo_admin
def eliminar_parada(ruta_id, parada_id):
    """Elimina una parada de una ruta."""
    parada = Parada.query.filter_by(id=parada_id, ruta_id=ruta_id).first()
    if not parada:
        return error("Parada no encontrada", 404)
    db.session.delete(parada)
    db.session.commit()
    return ok(mensaje="Parada eliminada")
