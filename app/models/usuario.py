import uuid
from datetime import datetime
from app import db


class Rol(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(30), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación
    usuarios = db.relationship("Usuario", back_populates="rol", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
        }


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    numero_ci = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(150), unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20))
    foto_url = db.Column(db.String(300))
    rol_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    creado_por = db.Column(db.UUID(as_uuid=True), db.ForeignKey("usuarios.id"), nullable=True)
    puede_autoregistrarse = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    rol = db.relationship("Rol", back_populates="usuarios")
    minibus_asignado = db.relationship("Minibus", back_populates="chofer", uselist=False,
                                        foreign_keys="Minibus.chofer_id")
    notificaciones = db.relationship("Notificacion", back_populates="usuario", lazy="dynamic")
    tokens_dispositivo = db.relationship("TokenDispositivo", back_populates="usuario", lazy="dynamic")

    def to_dict(self, include_sensitive=False):
        data = {
            "id": str(self.id),
            "nombre": self.nombre,
            "apellido": self.apellido,
            "nombre_completo": f"{self.nombre} {self.apellido}",
            "numero_ci": self.numero_ci,
            "email": self.email,
            "telefono": self.telefono,
            "foto_url": self.foto_url,
            "rol": self.rol.nombre if self.rol else None,
            "rol_id": self.rol_id,
            "puede_autoregistrarse": self.puede_autoregistrarse,
            "activo": self.activo,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }
        return data
