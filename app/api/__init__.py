from flask import Blueprint
from .auth import auth_bp
from .usuarios import usuarios_bp
from .rutas import rutas_bp
from .minibuses import minibuses_bp
from .registros import registros_bp
from .alertas import alertas_bp
from .calificaciones import calificaciones_bp
from .notificaciones import notificaciones_bp
from .turnos import turnos_bp
from .reportes import reportes_bp
from .camaras import camaras_bp

def registrar_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(rutas_bp)
    app.register_blueprint(minibuses_bp)
    app.register_blueprint(registros_bp)
    app.register_blueprint(alertas_bp)
    app.register_blueprint(calificaciones_bp)
    app.register_blueprint(notificaciones_bp)
    app.register_blueprint(turnos_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(camaras_bp)
