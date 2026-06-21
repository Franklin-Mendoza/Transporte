import uuid
from datetime import datetime, timedelta
from app import db


class Turno(db.Model):
    __tablename__ = "turnos"

    id = db.Column(db.Integer, primary_key=True)
    minibus_id = db.Column(db.Integer, db.ForeignKey("minibuses.id"), nullable=False)
    chofer_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"), nullable=False)
    ruta_id = db.Column(db.Integer, db.ForeignKey("rutas.id"), nullable=False)
    fecha = db.Column(db.Date, default=datetime.utcnow)
    hora_inicio = db.Column(db.DateTime)
    hora_fin = db.Column(db.DateTime)
    estado = db.Column(db.String(20), default="activo")  # activo, finalizado, cancelado
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    minibus = db.relationship("Minibus")
    chofer = db.relationship("Usuario")
    ruta = db.relationship("Ruta")
    registros = db.relationship("RegistroParada", back_populates="turno", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "minibus_id": self.minibus_id,
            "chofer_id": str(self.chofer_id),
            "ruta_id": self.ruta_id,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "hora_inicio": self.hora_inicio.isoformat() if self.hora_inicio else None,
            "hora_fin": self.hora_fin.isoformat() if self.hora_fin else None,
            "estado": self.estado,
            "placa": self.minibus.placa if self.minibus else None,
            "ruta_nombre": self.ruta.nombre if self.ruta else None,
            "chofer_nombre": f"{self.chofer.nombre} {self.chofer.apellido}" if self.chofer else None,
        }


class RegistroParada(db.Model):
    __tablename__ = "registros_parada"

    id = db.Column(db.BigInteger, primary_key=True)
    turno_id = db.Column(db.Integer, db.ForeignKey("turnos.id"))
    minibus_id = db.Column(db.Integer, db.ForeignKey("minibuses.id"), nullable=False)
    parada_id = db.Column(db.Integer, db.ForeignKey("paradas.id"), nullable=False)
    chofer_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"), nullable=False)
    latitud_real = db.Column(db.Numeric(10, 8))
    longitud_real = db.Column(db.Numeric(11, 8))
    distancia_metros = db.Column(db.Numeric(8, 2))
    en_ruta = db.Column(db.Boolean, nullable=False, default=True)
    metodo_registro = db.Column(db.String(20), default="camara")  # camara, pasajero_web, pasajero_app
    registrado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    turno = db.relationship("Turno", back_populates="registros")
    minibus = db.relationship("Minibus")
    parada = db.relationship("Parada")
    chofer = db.relationship("Usuario")

    def to_dict(self):
        return {
            "id": self.id,
            "turno_id": self.turno_id,
            "minibus_id": self.minibus_id,
            "parada_id": self.parada_id,
            "chofer_id": str(self.chofer_id),
            "latitud_real": float(self.latitud_real) if self.latitud_real else None,
            "longitud_real": float(self.longitud_real) if self.longitud_real else None,
            "distancia_metros": float(self.distancia_metros) if self.distancia_metros else None,
            "en_ruta": self.en_ruta,
            "metodo_registro": self.metodo_registro,
            "registrado_en": self.registrado_en.isoformat() if self.registrado_en else None,
            "parada_nombre": self.parada.nombre if self.parada else None,
            "parada_orden": self.parada.orden if self.parada else None,
        }


class EscaneosPasajero(db.Model):
    __tablename__ = "escaneos_pasajero"

    id = db.Column(db.BigInteger, primary_key=True)
    minibus_id = db.Column(db.Integer, db.ForeignKey("minibuses.id"), nullable=False)
    latitud_pasajero = db.Column(db.Numeric(10, 8))
    longitud_pasajero = db.Column(db.Numeric(11, 8))
    parada_actual_id = db.Column(db.Integer, db.ForeignKey("paradas.id"))
    minibus_en_ruta = db.Column(db.Boolean)
    distancia_ruta_metros = db.Column(db.Numeric(8, 2))
    plataforma = db.Column(db.String(20), default="web")  # web, app
    ip_origen = db.Column(db.String(45))
    escaneado_en = db.Column(db.DateTime, default=datetime.utcnow)

    minibus = db.relationship("Minibus")
    parada_actual = db.relationship("Parada")

    def to_dict(self):
        return {
            "id": self.id,
            "minibus_id": self.minibus_id,
            "placa": self.minibus.placa if self.minibus else None,
            "latitud_pasajero": float(self.latitud_pasajero) if self.latitud_pasajero else None,
            "longitud_pasajero": float(self.longitud_pasajero) if self.longitud_pasajero else None,
            "minibus_en_ruta": self.minibus_en_ruta,
            "distancia_ruta_metros": float(self.distancia_ruta_metros) if self.distancia_ruta_metros else None,
            "plataforma": self.plataforma,
            "escaneado_en": self.escaneado_en.isoformat() if self.escaneado_en else None,
        }


class AlertaDesvio(db.Model):
    __tablename__ = "alertas_desvio"

    id = db.Column(db.BigInteger, primary_key=True)
    minibus_id = db.Column(db.Integer, db.ForeignKey("minibuses.id"), nullable=False)
    chofer_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"), nullable=False)
    turno_id = db.Column(db.Integer, db.ForeignKey("turnos.id"))
    latitud_desvio = db.Column(db.Numeric(10, 8))
    longitud_desvio = db.Column(db.Numeric(11, 8))
    distancia_metros = db.Column(db.Numeric(8, 2))
    disparada_por = db.Column(db.String(30), default="pasajero")  # pasajero, camara, sistema, denuncia_pasajero
    estado = db.Column(db.String(20), default="pendiente")  # pendiente, justificada, rechazada, sin_respuesta
    notificacion_enviada = db.Column(db.Boolean, default=False)
    notificacion_enviada_en = db.Column(db.DateTime)
    generada_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    minibus = db.relationship("Minibus")
    chofer = db.relationship("Usuario")
    justificacion = db.relationship("Justificacion", back_populates="alerta", uselist=False)

    @property
    def plazo_justificar(self):
        if self.generada_en:
            return self.generada_en + timedelta(hours=24)
        return None

    @property
    def plazo_vencido(self):
        if self.plazo_justificar:
            return datetime.utcnow() > self.plazo_justificar
        return False

    def to_dict(self):
        return {
            "id": self.id,
            "minibus_id": self.minibus_id,
            "chofer_id": str(self.chofer_id),
            "turno_id": self.turno_id,
            "latitud_desvio": float(self.latitud_desvio) if self.latitud_desvio else None,
            "longitud_desvio": float(self.longitud_desvio) if self.longitud_desvio else None,
            "distancia_metros": float(self.distancia_metros) if self.distancia_metros else None,
            "disparada_por": self.disparada_por,
            "estado": self.estado,
            "notificacion_enviada": self.notificacion_enviada,
            "generada_en": self.generada_en.isoformat() if self.generada_en else None,
            "plazo_justificar": self.plazo_justificar.isoformat() if self.plazo_justificar else None,
            "plazo_vencido": self.plazo_vencido,
            "placa": self.minibus.placa if self.minibus else None,
            "chofer_nombre": f"{self.chofer.nombre} {self.chofer.apellido}" if self.chofer else None,
            "justificacion": self.justificacion.to_dict() if self.justificacion else None,
        }


class Justificacion(db.Model):
    __tablename__ = "justificaciones"

    id = db.Column(db.Integer, primary_key=True)
    alerta_id = db.Column(db.BigInteger, db.ForeignKey("alertas_desvio.id", ondelete="CASCADE"), nullable=False)
    chofer_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"), nullable=False)
    motivo = db.Column(db.String(50), nullable=False)
    # gasolina, emergencia, desvio_trafico, accidente, falla_mecanica, orden_superior, otro
    descripcion = db.Column(db.Text)
    archivo_url = db.Column(db.String(300))
    estado = db.Column(db.String(20), default="pendiente")  # pendiente, aceptada, rechazada
    revisado_por = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"))
    comentario_admin = db.Column(db.Text)
    enviada_en = db.Column(db.DateTime, default=datetime.utcnow)
    revisada_en = db.Column(db.DateTime)

    # Relaciones
    alerta = db.relationship("AlertaDesvio", back_populates="justificacion")
    chofer = db.relationship("Usuario", foreign_keys=[chofer_id])
    revisor = db.relationship("Usuario", foreign_keys=[revisado_por])

    def to_dict(self):
        return {
            "id": self.id,
            "alerta_id": self.alerta_id,
            "chofer_id": str(self.chofer_id),
            "motivo": self.motivo,
            "descripcion": self.descripcion,
            "archivo_url": self.archivo_url,
            "estado": self.estado,
            "comentario_admin": self.comentario_admin,
            "enviada_en": self.enviada_en.isoformat() if self.enviada_en else None,
            "revisada_en": self.revisada_en.isoformat() if self.revisada_en else None,
        }
