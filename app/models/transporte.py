from datetime import datetime
from app import db


class Ruta(db.Model):
    __tablename__ = "rutas"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    activa = db.Column(db.Boolean, default=True)
    creado_por = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    paradas = db.relationship("Parada", back_populates="ruta",
                               cascade="all, delete-orphan",
                               order_by="Parada.orden")
    minibuses = db.relationship("Minibus", back_populates="ruta")

    def to_dict(self, include_paradas=False):
        data = {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "activa": self.activa,
            "total_paradas": len(self.paradas),
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }
        if include_paradas:
            data["paradas"] = [p.to_dict() for p in self.paradas]
        return data


class Parada(db.Model):
    __tablename__ = "paradas"

    id = db.Column(db.Integer, primary_key=True)
    ruta_id = db.Column(db.Integer, db.ForeignKey("rutas.id", ondelete="CASCADE"), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    orden = db.Column(db.Integer, nullable=False)
    latitud = db.Column(db.Numeric(10, 8), nullable=False)
    longitud = db.Column(db.Numeric(11, 8), nullable=False)
    radio_metros = db.Column(db.Integer, default=50)
    activa = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    ruta = db.relationship("Ruta", back_populates="paradas")

    def to_dict(self):
        return {
            "id": self.id,
            "ruta_id": self.ruta_id,
            "nombre": self.nombre,
            "orden": self.orden,
            "latitud": float(self.latitud),
            "longitud": float(self.longitud),
            "radio_metros": self.radio_metros,
            "activa": self.activa,
        }


class Minibus(db.Model):
    __tablename__ = "minibuses"

    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(20), nullable=False, unique=True)
    codigo_qr = db.Column(db.String(100), nullable=False, unique=True)
    ruta_id = db.Column(db.Integer, db.ForeignKey("rutas.id"))
    chofer_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"))
    modelo = db.Column(db.String(100))
    color = db.Column(db.String(50))
    capacidad = db.Column(db.Integer, default=12)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    ruta = db.relationship("Ruta", back_populates="minibuses")
    chofer = db.relationship("Usuario", back_populates="minibus_asignado",
                              foreign_keys=[chofer_id])

    def to_dict(self, include_chofer=False, include_ruta=False):
        data = {
            "id": self.id,
            "placa": self.placa,
            "codigo_qr": self.codigo_qr,
            "ruta_id": self.ruta_id,
            "chofer_id": str(self.chofer_id) if self.chofer_id else None,
            "modelo": self.modelo,
            "color": self.color,
            "capacidad": self.capacidad,
            "activo": self.activo,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }
        if include_chofer and self.chofer:
            data["chofer"] = self.chofer.to_dict()
        if include_ruta and self.ruta:
            data["ruta"] = self.ruta.to_dict()
        return data
