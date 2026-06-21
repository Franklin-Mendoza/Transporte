import math
from flask import jsonify


# ─────────────────────────────────────────────
# Respuestas estandarizadas
# ─────────────────────────────────────────────

def ok(data=None, mensaje="OK", status=200):
    resp = {"ok": True, "mensaje": mensaje}
    if data is not None:
        resp["data"] = data
    return jsonify(resp), status


def error(mensaje="Error", status=400, detalle=None):
    resp = {"ok": False, "mensaje": mensaje}
    if detalle:
        resp["detalle"] = detalle
    return jsonify(resp), status


# ─────────────────────────────────────────────
# Cálculo de distancia geográfica (Haversine)
# Devuelve distancia en METROS entre dos puntos lat/lng
# ─────────────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en metros entre dos coordenadas GPS.
    Usa la fórmula de Haversine.
    """
    R = 6371000  # Radio de la Tierra en metros
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlam = math.radians(float(lon2) - float(lon1))

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def punto_en_ruta(lat_punto, lon_punto, paradas, radio_metros=100):
    """
    Verifica si un punto (lat, lon) está dentro del radio de cualquier parada de la ruta.
    Devuelve (True, parada_mas_cercana, distancia_metros) si está en ruta.
    Devuelve (False, None, distancia_minima) si está fuera.
    """
    min_dist = float("inf")
    parada_cercana = None

    for parada in paradas:
        dist = haversine(lat_punto, lon_punto, parada.latitud, parada.longitud)
        if dist < min_dist:
            min_dist = dist
            parada_cercana = parada

    en_ruta = min_dist <= radio_metros
    return en_ruta, parada_cercana, round(min_dist, 2)


def punto_cerca_de_parada(lat, lon, parada, radio_metros=None):
    """
    Verifica si un punto está dentro del radio de una parada específica.
    """
    radio = radio_metros or parada.radio_metros or 50
    dist = haversine(lat, lon, parada.latitud, parada.longitud)
    return dist <= radio, round(dist, 2)
