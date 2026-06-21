from datetime import datetime
from app import db


from sqlalchemy import Computed

class Calificacion(db.Model):
    __tablename__ = "calificaciones"

    id = db.Column(db.Integer, primary_key=True)
    chofer_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"), nullable=False)
    turno_id = db.Column(db.Integer, db.ForeignKey("turnos.id"))
    periodo = db.Column(db.String(10), nullable=False)   # '2026-05'
    fecha_calculo = db.Column(db.Date, default=datetime.utcnow)
    total_paradas = db.Column(db.Integer, default=0)
    paradas_ok = db.Column(db.Integer, default=0)
    alertas_generadas = db.Column(db.Integer, default=0)
    faltas_justificadas = db.Column(db.Integer, default=0)
    faltas_acumuladas = db.Column(db.Integer, default=0)

    # IMPORTANTE: en la BD real (creada con el SQL original), esta columna es
    # GENERATED ALWAYS AS (...) STORED — PostgreSQL la calcula solo y prohíbe
    # que cualquier INSERT/UPDATE le mande un valor manual. Por eso aquí se
    # mapea como server_default (solo lectura desde SQLAlchemy): se puede leer
    # el valor normalmente, pero nunca se incluye en los INSERT/UPDATE que
    # genera el ORM, evitando el error psycopg2.errors.GeneratedAlways.
    calificacion = db.Column(db.Numeric(5, 2), server_default=db.FetchedValue())
    nivel = db.Column(db.String(20), server_default=db.FetchedValue())

    chofer = db.relationship("Usuario")

    def calcular_y_guardar(self):
        """
        calificacion la calcula la BD sola (columna generada). nivel puede
        venir de un trigger de la BD o no, según cómo se creó la tabla — por
        eso aquí se refresca primero desde la BD, y solo si 'nivel' sigue
        vacío después de eso, se calcula como respaldo en Python.
        """
        db.session.flush()
        db.session.refresh(self)

        if self.nivel is None and self.calificacion is not None:
            cal = float(self.calificacion)
            if cal >= 90:
                self.nivel = "excelente"
            elif cal >= 75:
                self.nivel = "bueno"
            elif cal >= 60:
                self.nivel = "regular"
            else:
                self.nivel = "deficiente"

    def to_dict(self):
        # Buscar la placa actual del minibús asignado a este chofer (puede no tener)
        placa_actual = None
        if self.chofer:
            from app.models import Minibus
            bus = Minibus.query.filter_by(chofer_id=self.chofer_id, activo=True).first()
            placa_actual = bus.placa if bus else None

        return {
            "id": self.id,
            "chofer_id": str(self.chofer_id),
            "periodo": self.periodo,
            "fecha_calculo": self.fecha_calculo.isoformat() if self.fecha_calculo else None,
            "total_paradas": self.total_paradas,
            "paradas_ok": self.paradas_ok,
            "alertas_generadas": self.alertas_generadas,
            "faltas_justificadas": self.faltas_justificadas,
            "faltas_acumuladas": self.faltas_acumuladas,
            "calificacion": float(self.calificacion) if self.calificacion else 0,
            "nivel": self.nivel,
            "chofer_nombre": f"{self.chofer.nombre} {self.chofer.apellido}" if self.chofer else None,
            "chofer_ci": self.chofer.numero_ci if self.chofer else None,
            "placa": placa_actual,
        }


class Notificacion(db.Model):
    __tablename__ = "notificaciones"

    id = db.Column(db.BigInteger, primary_key=True)
    usuario_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    # alerta_desvio, parada_ok, justif_aceptada, justif_rechazada, turno_iniciado, turno_finalizado
    titulo = db.Column(db.String(150), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    datos_extra = db.Column(db.JSON)
    leida = db.Column(db.Boolean, default=False)
    enviada = db.Column(db.Boolean, default=False)
    token_dispositivo = db.Column(db.String(300))
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)
    leida_en = db.Column(db.DateTime)

    usuario = db.relationship("Usuario", back_populates="notificaciones")

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "mensaje": self.mensaje,
            "datos_extra": self.datos_extra,
            "leida": self.leida,
            "creada_en": self.creada_en.isoformat() if self.creada_en else None,
            "leida_en": self.leida_en.isoformat() if self.leida_en else None,
        }


class ReporteGenerado(db.Model):
    __tablename__ = "reportes_generados"

    id = db.Column(db.Integer, primary_key=True)
    generado_por = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    formato = db.Column(db.String(10), nullable=False)  # excel, pdf
    filtro_desde = db.Column(db.Date)
    filtro_hasta = db.Column(db.Date)
    filtro_chofer = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"))
    filtro_ruta = db.Column(db.Integer, db.ForeignKey("rutas.id"))
    archivo_url = db.Column(db.String(300))
    generado_en = db.Column(db.DateTime, default=datetime.utcnow)

    generador = db.relationship("Usuario", foreign_keys=[generado_por])

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "formato": self.formato,
            "archivo_url": self.archivo_url,
            "generado_en": self.generado_en.isoformat() if self.generado_en else None,
        }


class TokenDispositivo(db.Model):
    __tablename__ = "tokens_dispositivo"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"), nullable=False)
    token = db.Column(db.String(300), nullable=False)
    plataforma = db.Column(db.String(10), default="android")  # android, ios
    activo = db.Column(db.Boolean, default=True)
    registrado_en = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuario", back_populates="tokens_dispositivo")
