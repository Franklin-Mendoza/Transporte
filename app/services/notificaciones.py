import requests
from flask import current_app
from datetime import datetime
from app import db
from app.models import Notificacion, TokenDispositivo


def enviar_push(usuario_id, tipo, titulo, mensaje, datos_extra=None):
    """
    Crea la notificación en la BD y la envía por FCM al dispositivo del usuario.
    """
    # 1. Obtener token FCM activo del usuario
    token_obj = TokenDispositivo.query.filter_by(
        usuario_id=usuario_id, activo=True
    ).order_by(TokenDispositivo.registrado_en.desc()).first()

    token_fcm = token_obj.token if token_obj else None

    # 2. Guardar en BD
    notif = Notificacion(
        usuario_id=usuario_id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        datos_extra=datos_extra or {},
        token_dispositivo=token_fcm,
    )
    db.session.add(notif)
    db.session.flush()  # Para tener el ID antes del commit

    # 3. Enviar por FCM si hay token
    if token_fcm:
        fcm_key = current_app.config.get("FCM_SERVER_KEY", "")
        if fcm_key:
            _enviar_fcm(token_fcm, titulo, mensaje, datos_extra or {})
            notif.enviada = True

    db.session.commit()
    return notif


def _enviar_fcm(token, titulo, mensaje, datos):
    """Envía la notificación a Firebase Cloud Messaging."""
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        headers = {
            "Authorization": f"key={current_app.config['FCM_SERVER_KEY']}",
            "Content-Type": "application/json",
        }
        payload = {
            "to": token,
            "notification": {
                "title": titulo,
                "body": mensaje,
                "sound": "default",
            },
            "data": datos,
            "priority": "high",
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        current_app.logger.error(f"Error FCM: {e}")
        return False


def notificar_desvio_chofer(chofer_id, alerta_id, placa, distancia):
    """Notificación específica cuando el bus sale de ruta."""
    return enviar_push(
        usuario_id=chofer_id,
        tipo="alerta_desvio",
        titulo="⚠️ Fuera de ruta — Justifica",
        mensaje=f"El minibús {placa} está a {distancia:.0f}m de la ruta autorizada. Ingresa una justificación.",
        datos_extra={"alerta_id": alerta_id, "placa": placa, "distancia": distancia},
    )


def notificar_parada_ok(chofer_id, parada_nombre, hora):
    """Notificación cuando el bus llega correctamente a una parada."""
    return enviar_push(
        usuario_id=chofer_id,
        tipo="parada_ok",
        titulo=f"✓ Parada registrada",
        mensaje=f"{parada_nombre} — {hora}",
        datos_extra={"parada": parada_nombre, "hora": hora},
    )


def notificar_justificacion(chofer_id, estado, comentario=""):
    """Notificación cuando el admin acepta o rechaza una justificación."""
    if estado == "aceptada":
        titulo = "✅ Justificación aceptada"
        mensaje = "Tu justificación fue aceptada. La falta no afectará tu calificación."
        tipo = "justif_aceptada"
    else:
        titulo = "❌ Justificación rechazada"
        mensaje = f"Tu justificación fue rechazada. {comentario}"
        tipo = "justif_rechazada"

    return enviar_push(
        usuario_id=chofer_id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        datos_extra={"estado": estado, "comentario": comentario},
    )
