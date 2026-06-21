from datetime import datetime
from app import db


class CamaraParada(db.Model):
    """
    Asigna una cámara web (detectada por el navegador del admin/operador)
    a una parada específica. El deviceId es el identificador único que
    el navegador asigna a cada cámara conectada (USB, integrada, etc.)
    vía navigator.mediaDevices.enumerateDevices().

    Nota importante: el deviceId de una cámara puede cambiar si se
    desconecta y reconecta el USB en un puerto distinto, por eso también
    guardamos el "label" (nombre legible, ej: "USB2.0 Camera") para que
    el admin pueda reconocerla fácilmente y reasignarla si hace falta.
    """
    __tablename__ = "camaras_parada"

    id = db.Column(db.Integer, primary_key=True)
    parada_id = db.Column(db.Integer, db.ForeignKey("paradas.id", ondelete="CASCADE"),
                           nullable=False, unique=True)
    device_id = db.Column(db.String(300), nullable=False)
    device_label = db.Column(db.String(200))  # nombre legible que da el navegador
    activa = db.Column(db.Boolean, default=True)
    asignada_por = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"))
    asignada_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizada_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parada = db.relationship("Parada")

    def to_dict(self):
        return {
            "id": self.id,
            "parada_id": self.parada_id,
            "parada_nombre": self.parada.nombre if self.parada else None,
            "ruta_id": self.parada.ruta_id if self.parada else None,
            "device_id": self.device_id,
            "device_label": self.device_label,
            "activa": self.activa,
            "asignada_en": self.asignada_en.isoformat() if self.asignada_en else None,
        }
